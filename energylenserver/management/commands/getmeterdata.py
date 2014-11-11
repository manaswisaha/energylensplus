"""
[PRODUCER] Generates meter data for the consumer

Script to process streaming data from smap
and pass them to the edge_detection API on the EnergyLens+ Server

Things done:
    1. Retrieve meter data from smap db using republish API
    2. Store data on the disk
    3. Detect edges and store them


Input: apt number list
Output: csv file with timestamped power values
Format: <timestamp, power>

Author: Manaswi Saha
Date: 27th Aug 2014
"""
import os
import sys
import subprocess

import csv
import json
import pycurl
import datetime as dt

import numpy as np
import pandas as pd


# Django imports
from django.core.management.base import BaseCommand
from django.conf import settings

# EnergyLens+ imports
from energylenserver.common_imports import *
from energylenserver.constants import apt_no_list
from energylenserver.functions import *
from energylenserver.meter import smap
from energylenserver.tasks import meterDataHandler


# Enable Logging
logger = logging.getLogger('energylensplus_meterdata')

TIMEZONE = 'Asia/Kolkata'

# Global variables
STREAM_URL = "http://energy.iiitd.edu.in:9106/republish"


# Participating apartments
# apt_no_list = ['1201']  # , '101', '1003', '1002']
uuid_list = []
payload = ""

# Destination Folder for the output files
dst_folder = 'data/meter/'


class Client:

    def __init__(self):

        logger.debug("[Initializing Client...]")

        global uuid_list, payload

        self.conn = None
        self.msg_count = {}
        self.current_file = {}

        self.backoff_network_error = 0.25
        self.backoff_http_error = 5
        self.backoff_rate_limit = 60

        for i in uuid_list:
            self.msg_count[i] = 0
            self.current_file[i] = ""

        self.setup_connection()

    def setup_connection(self):
        """
        Establishes a persistent connection with the sMap server
        """

        if self.conn:
            self.conn.close()

        self.backoff_network_error = 0.25
        self.backoff_http_error = 5
        self.backoff_rate_limit = 60

        self.conn = pycurl.Curl()
        self.conn.setopt(pycurl.URL, STREAM_URL)
        self.conn.setopt(pycurl.POST, 1)
        self.conn.setopt(pycurl.POSTFIELDS, payload)
        self.conn.setopt(pycurl.WRITEFUNCTION, self.on_receive)

    def start(self):
        """
        Starts listening to the open stream
        """

        while True:
            self.setup_connection()
            try:
                self.conn.perform()
            except:
                # Network error, use linear back off up to 16 seconds
                logger.error('Network error: %s' % self.conn.errstr())
                logger.error('Waiting %s seconds before trying again' % self.backoff_network_error)
                time.sleep(self.backoff_network_error)
                self.backoff_network_error = min(self.backoff_network_error + 1, 16)
                continue
            # HTTP Error
            sc = self.conn.getinfo(pycurl.HTTP_CODE)
            if sc == 420:
                # Rate limit, use exponential back off starting with 1 minute and double
                # each attempt
                logger.error('Rate limit, waiting %s seconds' % self.backoff_rate_limit)
                time.sleep(self.backoff_rate_limit)
                self.backoff_rate_limit *= 2
            else:
                # HTTP error, use exponential back off up to 320 seconds
                logger.error('HTTP error %s, %s' % (sc, self.conn.errstr()))
                logger.error('Waiting %s seconds' % self.backoff_http_error)
                time.sleep(self.backoff_http_error)
                self.backoff_http_error = min(self.backoff_http_error * 2, 320)

    def create_file(self, filename):

        if not os.path.isfile(filename):
            with open(filename, "w+") as myfile:
                writer = csv.writer(myfile)
                writer.writerow(["time", "power"])

    def write_to_file(self, filename, data):

        with open(filename, "a+") as myfile:
            writer = csv.writer(myfile)
            writer.writerow(data)

    def on_receive(self, data):
        global dst_folder

        try:
            if data.strip():
                try:
                    readings = json.loads(data)
                    # logger.debug("Readings: \n%s", readings)
                except ValueError:
                    # Log error
                    logger.debug("Invalid JSON string passed. Ignoring data:%s", data)
                    string_to_log = ["[" + time.ctime(time.time()) + "]", str(data)]
                    logger.debug("%s", string_to_log)
                    return

                # Parse json body
                for key in readings:
                    record = readings[key]
                    uuid = record['uuid']
                    reading = np.array(record['Readings'])
                    timestamp = reading[0, 0] / 1000
                    value = reading[0, 1]
                    record = [timestamp, value]

                    self.msg_count[uuid] += 1
                    msg_count = self.msg_count[uuid]

                    # If first record of a new batch for the uuid, create new file
                    if msg_count == 1:
                        filename = (timestamp_to_str(time.time(),
                                                     "%d-%m-%Y_%H:%M:%S") + ".csv")
                        file_path = os.path.join(dst_folder + uuid + "/", filename)
                        # logger.debug("File Path:\n\t%s", file_path)
                        self.create_file(file_path)
                        self.current_file[uuid] = file_path
                        self.write_to_file(file_path, record)

                    # 2*winmin + 1 is the minimum number of values needed for edge detection
                    elif msg_count in range(2, 9):
                        file_path = self.current_file[uuid]
                        self.write_to_file(file_path, record)

                        if msg_count == 2 * winmin + 1:
                            logger.debug("[Detecting edges]...")
                            # Reset current file and msg count for the uuid
                            self.msg_count[uuid] = 0
                            self.current_file[uuid] = ""

                            # logger.debug("File Path:\n\t", file_path)

                            prev_file = ""
                            curr_file = os.path.basename(file_path)
                            df = pd.read_csv(file_path)

                            # Determine current uuid
                            meter_uuid_folder = os.path.dirname(file_path)
                            # uuid = meter_uuid_folder.split('/')[-1]

                            # -- Retrieve values from previous file --
                            folder_listing = sorted(os.listdir(meter_uuid_folder))
                            # logger.debug("Files: %s", folder_listing)
                            for the_file in folder_listing:
                                if the_file.startswith("prev_"):
                                    prev_file = the_file
                                    prev_file = os.path.join(meter_uuid_folder, prev_file)
                                    break

                            if prev_file != "":
                                df_prev = pd.read_csv(prev_file)
                                # Use the last few values for edge detection
                                df_prev = df_prev.ix[df_prev.index[1:]]

                                # df_len = len(df)
                                # Combine prev file with the current one
                                df = pd.concat([df_prev, df]).sort("time")
                                df = df.reset_index(drop=True)
                                df['act_time'] = [dt.datetime.fromtimestamp(val) for val in df.time]

                                # logger.debug("Length:%d %d %d", len(df_prev), df_len, len(df))
                                del df['act_time']

                                # Delete previous file
                                try:
                                    os.unlink(prev_file)
                                except Exception, e:
                                    logger.error("%s", e)

                            # -- Buffer current file --
                            # For use in the next task, rename it with prev_<filename>
                            new_file = os.path.join(meter_uuid_folder, "prev_" + curr_file)
                            os.renames(file_path, new_file)

                            # Create an event and pass it on to the listeners
                            # for consuming this file
                            meterDataHandler.delay(df, file_path)

        except KeyboardInterrupt:
            logger.error("\n\nInterrupted by user, shutting down..")
            sys.exit(0)


class Command(BaseCommand):
    help = "Retrieves real-time meter data from the sMap server"

    def handle(self, *args, **options):
        """
        Retrieves real-time meter data and passes it on the edge detection
        component
        """

        global dst_folder, payload, uuid_list

        base_dir = settings.BASE_DIR

        try:
            dst_folder = os.path.join(base_dir, 'energylenserver/' + dst_folder)

            # Delete existing directories inside data/meter folder
            import shutil
            logger.debug("Deleting files from the old run..")
            folder_listing = os.listdir(dst_folder)
            for d in folder_listing:
                d = os.path.join(dst_folder, d)
                shutil.rmtree(d)

            logger.debug("Getting UUIDs for all apartment meters..")

            # Retrieve uuids for the apartment numbers
            for apt_no in apt_no_list:
                logger.debug("Apartment: %s", apt_no)
                meter_list = smap.get_meter_info(apt_no)

                logger.debug("Meters:\n %s", meter_list)
                for meter in meter_list:
                    meter_uuid = meter['uuid']
                    uuid_list.append(meter_uuid)

                    try:
                        # Create directory for the uuid
                        folder = dst_folder + meter_uuid + "/"
                        if not os.path.exists(folder):
                            os.makedirs(folder)
                            logger.debug("Folder created: %s", folder)
                    except OSError, e:
                        logger.error("[DirectoryCreationError]::%s", e)
                        sys.exit(1)

            # Create Payload
            payload = "Metadata/Extra/PhysicalParameter='Power' and (Metadata/Extra/FlatNumber = "

            list_len = len(apt_no_list)
            for i, apt_no in enumerate(apt_no_list):
                payload += "'" + apt_no + "'"

                if i != (list_len - 1):
                    payload += " or Metadata/Extra/FlatNumber = "
                else:
                    payload += ")"
            logger.debug("Payload:\n [%s]", payload)

            # Open persistent HTTP connection to sMAP
            c = Client()
            c.setup_connection()
            c.start()
        except KeyboardInterrupt:
            logger.error("\n\nInterrupted by user, shutting down..")
            sys.exit(0)

        except Exception, e:
            logger.error("[GetMeterDataException] %s\n" % str(e))
            sys.exit(1)
