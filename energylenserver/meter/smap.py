"""
Functions that interacts with sMAP server
and retrieves meter data
"""

import time
import requests
import pandas as pd
import numpy as np


# Global variables
url = 'http://energy.iiitd.edu.in:9106/api/query'


def get_latest_power_data(apt_no):
    """
    Gets the latest reading from both meters

    Usage: For real-time data access
    """
    payload = ("select data before now "
               "where Metadata/Extra/FlatNumber ='" + str(apt_no) + "' and "
               "Metadata/Extra/PhysicalParameter='Power'")

    r = requests.post(url, data=payload)
    print r
    payload_body = r.json()
    print payload_body

    lpower = 0

    if len(payload_body) > 1:
        readings = payload_body[0]['Readings']
        time_1 = readings[0][0]
        power = readings[0][1]

        readings = payload_body[1]['Readings']
        time_2 = readings[0][0]
        lpower = readings[0][1]

        timestamp = max(time_1, time_2) / 1000

        # Handling power outages where meter data may not be the latest
        if abs(time_1 - time_2) > 2:
            time_low = min(time_1, time_2) / 1000
            now_time = time.time()

            if abs(now_time - time_low) > 3:
                if time_low == time_1:
                    power = 0
                elif time_low == time_2:
                    lpower = 0

    else:
        readings = payload_body[0]['Readings']
        timestamp = readings[0][0]
        power = readings[0][1]

    print "Power", power
    print "LPower", lpower

    total_power = power + lpower

    return timestamp, total_power


def get_meter_data(query):
    """
    Gets the readings from smap based on the query

    Returns: Dataframes for both streams
    """

    print "Getting meter data..."
    r = requests.post(url, data=query)
    print r
    payload = r.json()
    print payload

    return payload


def get_meter_data_for_time_slice(apt_no, start_time, end_time):
    """
    Retrieves meter data in the specified time interval
    """

    print "\nGetting meter data between", start_time, "and", end_time

    query = ("select data in ('" + str(start_time) + "','" + str(end_time) + "') "
             "limit 200000 "
             "where Metadata/Extra/FlatNumber ='" + str(apt_no) + "' and "
             "Metadata/Extra/PhysicalParameter='Power'")

    r = requests.post(url, data=query)
    # print r
    payload = r.json()
    print "Payload:", payload

    meters = get_meter_info(apt_no)

    streams = []
    meter_type = []
    for i in range(0, len(payload)):
        uuid = payload[i]['uuid']

        # Get meter type based on uuid
        for meter in meters:
            if meter['uuid'] == uuid:
                m_type = meter['type']
                print uuid, m_type

        meter_type.append(m_type)
        streams.append(np.array(payload[i]['Readings']))
    # print "Streams:", streams

    df = [pd.DataFrame({'time': readings[:, 0] / 1000, 'power': readings[:, 1],
                        'type': meter_type[i] * len(readings)}, columns=['time', 'power'])
          for i, readings in enumerate(streams)]

    return df


def get_meter_info(apt_no):
    """
    Get meter info from smap server
    """
    payload = ("select uuid, Metadata/Instrument/SupplyType "
               "where Metadata/Extra/FlatNumber ='" + str(apt_no) + "' and "
               "Metadata/Extra/PhysicalParameter='Power'")

    r = requests.post(url, data=payload)
    print r
    payload_body = r.json()
    print payload_body

    meters = []
    for i in range(0, len(payload)):
        meter = payload_body[0]

        meters.append({'uuid': meter['uuid'], 'type': meter[
                       'Metadata']['Instrument']['SupplyType']})

    return meters
