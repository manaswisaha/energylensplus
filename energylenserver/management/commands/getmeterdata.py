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
from energylenserver.functions import *
from energylenserver.constants import *
from energylenserver.meter.smap import get_meter_info
from energylenserver.tasks import meterDataHandler


TIMEZONE = 'Asia/Kolkata'

# Global variables
STREAM_URL = "http://energy.iiitd.edu.in:9106/republish"


# Participating apartments
apt_no_list = ['101', '1003', '1002']
uuid_list = []
payload = ""

# Destination Folder for the output files
dst_folder = 'data/meter/'


class Client:

    def __init__(self):

        print "\n[Initializing Client...]"

        global uuid_list, payload

        self.msg_count = {}
        self.current_file = {}

        for i in uuid_list:
            self.msg_count[i] = 0
            self.current_file[i] = ""

        self.conn = pycurl.Curl()
        self.conn.setopt(pycurl.URL, STREAM_URL)
        self.conn.setopt(pycurl.WRITEFUNCTION, self.on_receive)
        self.conn.setopt(pycurl.POST, 1)
        self.conn.setopt(pycurl.POSTFIELDS, payload)
        try:
            self.conn.perform()
        except KeyboardInterrupt:
            print "\n\nInterrupted by user, shutting down.."
            sys.exit(0)

    def create_file(self, filename):

        if not os.path.isfile(filename):
            with open(filename, "w+") as myfile:
                writer = csv.writer(myfile)
                writer.writerow(["time", "power"])

    def write_to_file(self, filename, data):
        print "Writing.."

        with open(filename, "a+") as myfile:
            writer = csv.writer(myfile)
            writer.writerow(data)

    def on_receive(self, data):
        global dst_folder

        try:
            if data.strip():
                try:
                    readings = json.loads(data)
                    print "Readings:\n", readings
                except ValueError:
                    # Log error
                    filename = os.path.join(settings.BASE_DIR, "/logs/meterdata.csv")
                    print "Invalid JSON string passed. Ignoring data:", data
                    string_to_log = ["[" + time.ctime(time.time()) + "]", str(data)]
                    self.write_to_file(filename, string_to_log)
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
                        print "File Path:\n", file_path
                        self.create_file(file_path)
                        self.current_file[uuid] = file_path
                        self.write_to_file(file_path, record)

                    # 2*winmin + 1 is the minimum number of values needed for edge detection
                    elif msg_count in range(2, 9):
                        file_path = self.current_file[uuid]
                        self.write_to_file(file_path, record)

                        if msg_count == 2 * winmin + 1:
                            print "\n[DETECT EDGES]..."
                            # Reset current file and msg count for the uuid
                            self.msg_count[uuid] = 0
                            self.current_file[uuid] = ""

                            print "File Path:\n", file_path

                            prev_file = ""
                            curr_file = os.path.basename(file_path)
                            df = pd.read_csv(file_path)

                            # Determine current uuid
                            meter_uuid_folder = os.path.dirname(file_path)
                            # uuid = meter_uuid_folder.split('/')[-1]

                            # -- Retrieve values from previous file --
                            folder_listing = sorted(os.listdir(meter_uuid_folder))
                            print "Files", folder_listing
                            for the_file in folder_listing:
                                if the_file.startswith("prev_"):
                                    prev_file = the_file
                                    prev_file = os.path.join(meter_uuid_folder, prev_file)
                                    break

                            if prev_file != "":
                                df_prev = pd.read_csv(prev_file)
                                # Use the last few values for edge detection
                                df_prev = df_prev.ix[df_prev.index[1:]]

                                df_len = len(df)
                                # Combine prev file with the current one
                                df = pd.concat([df_prev, df]).sort("time")
                                df = df.reset_index(drop=True)
                                df['act_time'] = [dt.datetime.fromtimestamp(val) for val in df.time]

                                print "TOGETHER:\n", df

                                print "Length:", len(df_prev), df_len, len(df)
                                del df['act_time']

                                # Delete previous file
                                try:
                                    os.unlink(prev_file)
                                except Exception, e:
                                    print e

                            # -- Buffer current file --
                            # For use in the next task, rename it with prev_<filename>
                            new_file = os.path.join(meter_uuid_folder, "prev_" + curr_file)
                            os.renames(file_path, new_file)

                            # Create an event and pass it on to the listeners
                            # for consuming this file
                            meterDataHandler.delay(df, file_path)

        except KeyboardInterrupt:
            print "\n\nInterrupted by user, shutting down.."
            sys.exit(0)


class Command(BaseCommand):
    help = "Retrieves real-time meter data from the sMap server"

    def handle(self, *args, **options):
        """
        Retrieves real-time meter data and passes it on the edge detection
        component
        """

        global dst_folder, apt_no_list, payload, uuid_list

        base_dir = settings.BASE_DIR

        try:
            dst_folder = os.path.join(base_dir, 'energylenserver/' + dst_folder)

            # Delete existing directories inside data/meter folder
            import shutil
            print "\nDeleting files from the old run.."
            folder_listing = os.listdir(dst_folder)
            for d in folder_listing:
                d = os.path.join(dst_folder, d)
                shutil.rmtree(d)

            print "Getting UUIDs for all apartment meters.."

            # Retrieve uuids for the apartment numbers
            for apt_no in apt_no_list:
                print "Apartment:", apt_no
                meter_list = get_meter_info(apt_no)
                print "Meters:\n", meter_list
                for meter in meter_list:
                    meter_uuid = meter['uuid']
                    uuid_list.append(meter_uuid)

                    try:
                        # Create directory for the uuid
                        folder = dst_folder + meter_uuid + "/"
                        if not os.path.exists(folder):
                            os.makedirs(folder)
                            print "Folder created:", folder
                    except OSError, e:
                        print "[DirectoryCreationError]", e
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
            print "\nPayload:\n", "[" + payload + "]"

            # Open persistent HTTP connection to sMAP
            Client()
        except KeyboardInterrupt:
            print "\n\nInterrupted by user, shutting down.."
            sys.exit(0)

        except Exception, e:
            self.stdout.write("GetMeterDataException] %s" % str(e))
            sys.exit(1)
