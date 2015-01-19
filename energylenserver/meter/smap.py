"""
Functions that interacts with sMAP server
and retrieves meter data

sMAP Details:
Time range syntax: %m/%d/%Y, %m/%d/%Y %H:%M, or %Y-%m-%dT%H:%M:%S.
For instance 10/16/1985 and 2/29/2012 20:00 are valid

Example query:
payload="select data in (now -5minutes, now) where
Metadata/LoadLocation/FlatNumber ='103' and Metadata/Extra/PhysicalParameter='PowerPhase1'
and Metadata/Extra/Type='Power'"

Refer: http://www.cs.berkeley.edu/~stevedh/smap2/archiver.html
"""

import time
import requests
import pandas as pd
import numpy as np

from energylenserver.models.functions import retrieve_meter_info
# Enable Logging
import logging
logger = logging.getLogger('energylensplus_django')

# Global variables
url = 'http://energy.iiitd.edu.in:9306/api/query'


def get_meter_data(query):
    """
    Gets the readings from smap based on the query

    Returns: Dataframes for both streams
    """

    logger.debug("sMap: Getting meter data...")
    r = requests.post(url, data=query)
    logger.debug("%s", r)
    payload = r.json()
    logger.debug("%s", payload)

    return payload


def get_latest_power_data(apt_no):
    """
    Gets the latest reading from both meters

    Usage: For real-time data access
    """
    if apt_no in ['102A', 102]:
        apt_no = '102A'
    payload = ("select data before now "
               "where Metadata/LoadLocation/FlatNumber ='" + str(apt_no) + "' and "
               "Metadata/Extra/PhysicalParameter='Power'")

    r = requests.post(url, data=payload)
    # logger.debug (r)
    payload_body = r.json()
    logger.debug(payload_body)

    lpower = 0

    # For two meters
    if len(payload_body) > 1:
        readings = payload_body[0]['Readings']
        time_1 = readings[0][0]
        power = readings[0][1]

        readings = payload_body[1]['Readings']
        time_2 = readings[0][0]
        lpower = readings[0][1]

        timestamp = max(time_1, time_2)

        # Handling power outages where meter data may not be the latest
        if abs(time_1 - time_2) > 2:
            time_low = min(time_1, time_2)
            now_time = time.time()

            if abs(now_time - time_low) > 3:
                if time_low == time_1:
                    power = 0
                elif time_low == time_2:
                    lpower = 0

    # For a single meter
    else:
        readings = payload_body[0]['Readings']
        timestamp = readings[0][0]
        power = readings[0][1]

    logger.debug("Power: %f", power)
    logger.debug("LPower: %f", lpower)

    total_power = power + lpower

    return timestamp, total_power


def get_meter_data_for_time_slice(apt_no, start_time, end_time):
    """
    Retrieves meter data in the specified time interval
    """
    if apt_no in ['102A', 102]:
        apt_no = '102A'

    logger.debug("sMap: Getting meter data for %s between %s and %s", apt_no, start_time, end_time)

    query = ("select data in ('" + str(start_time) + "','" + str(end_time) + "') "
             "limit 200000 "
             "where Metadata/LoadLocation/FlatNumber ='" + str(apt_no) + "' and "
             "Metadata/Extra/PhysicalParameter='Power'")

    r = requests.post(url, data=query)
    # logger.debug ("%s",r)
    payload = r.json()
    # logger.debug ("Payload:%s", payload)

    if apt_no in ['102A', 102]:
        apt_no = 102
    meters = retrieve_meter_info(apt_no)
    logger.debug("Meters: %s", meters)

    streams = []
    meter_type = []
    l_meters = range(0, len(meters))
    for i in l_meters:
        uuid = payload[i]['uuid']

        # Get meter type based on uuid
        for meter in meters:
            if meter['uuid'] == uuid:
                m_type = meter['type']
                # logger.debug (uuid, m_type)

        meter_type.append(m_type)
        streams.append(np.array(payload[i]['Readings']))
    # logger.debug("Streams: %s", streams)

    if len(streams[0]) > 0:

        df = [pd.DataFrame({'time': readings[:, 0] / 1000, 'power': readings[:, 1],
                            'type': [meter_type[i]] * len(readings)},
                           columns=['time', 'power', 'type']) for i, readings in enumerate(streams)]
    else:
        df = []

    return df


def get_meter_info(apt_no):
    """
    Get meter info from smap server
    """
    if apt_no in ['102A', 102]:
        apt_no = '102A'
    payload = ("select uuid, Metadata/Instrument/SupplyType "
               "where Metadata/LoadLocation/FlatNumber ='" + str(apt_no) + "' and "
               "Metadata/Extra/PhysicalParameter='Power'")

    r = requests.post(url, data=payload)
    # logger.debug ("%s",r)
    payload_body = r.json()
    # logger.debug ("Payload:\n%s", payload_body)

    meters = []
    for i in range(0, len(payload_body)):
        meter = payload_body[i]

        meters.append({'uuid': meter['uuid'], 'type': meter[
                       'Metadata']['Instrument']['SupplyType']})

    return meters
