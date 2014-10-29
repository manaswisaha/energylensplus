import time
import pandas as pd
import numpy as np
import datetime as dt

from smap import get_meter_data_for_time_slice
from edge_detection import *
from constants import *
from energylenserver.functions import *


# sys.path.insert(1, '/home/manaswi/EnergyLensPlusCode/energylensplus')
# print "SYSPATH", sys.path

# import os
# os.environ['DJANGO_SETTINGS_MODULE'] = "energylensplus.settings"

# Global variables
date_format = "%Y-%m-%dT%H:%M:%S"

"""
TODO:
1. Measure the difference between the time between phone and meter
"""


def compute_power(start_mag, end_mag):
    return (start_mag + end_mag) / 2


def training_compute_power(apt_no, start_time, end_time):
    """
    Computes the power consumption in the given time interval
    """

    print "\nComputing power for training data..."
    power = np.random.randn()

    # TODO: Measure the difference between time of the phone with the meter data
    # Once measured, set the global variable in the constants
    # For now, taking it as 5 seconds
    time_diff = -5  # If phone is ahead, subtract from the time sent
    time_diff = 5  # If phone is behind, add to the time sent

    # Convert time to seconds and add/subtract the difference time
    start_time = int(start_time) / 1000 + time_diff
    end_time = int(end_time) / 1000 + time_diff

    # Add a window to the given event time duration
    s_time = start_time - winmax
    s_time = timestamp_to_str(s_time, date_format)

    e_time = end_time + winmax
    e_time = timestamp_to_str(e_time, date_format)

    # ---Temp code----START
    # Test Edge 1- Light
    s_time = "2014-08-20T17:34:04"
    e_time = "2014-08-20T17:37:39"

    # Test Edge 2- Light
    s_time = "2014-08-20T17:43:17"
    e_time = "2014-08-20T17:44:01"

    start_time = str_to_timestamp(s_time, date_format)
    end_time = str_to_timestamp(e_time, date_format)

    # Test Edge 1- Light
    s_time = "2014-08-20T17:33:54"
    e_time = "2014-08-20T17:37:49"

    # Test Edge 2- Light
    s_time = "2014-08-20T17:43:07"
    e_time = "2014-08-20T17:44:11"
    # ---Temp code----END

    # Retrieve power data from smap server for both meters
    # between <start_time> and <end_time>
    streams_df = get_meter_data_for_time_slice(apt_no, s_time, e_time)

    # print "Streams:", streams_df

    # Contains start and end edges list from both meters
    edge_list = []

    # ---Detect start/end edges for both meters---
    for i, edge_time in enumerate([start_time, end_time]):

        # Temp code -- START
        if i == 0:
            print "\n[For rising edge (ON)]"
        else:
            print "\n[For falling edge (OFF)]"
        # Temp code -- END

        # Add a window around the event edges
        # Adding 5 to fetch extra to account for missing values
        s_time = edge_time - winmax - 5
        e_time = edge_time + winmax + 5

        # print "Start time:", s_time
        # print "End time:", e_time

        # For checking the edge, filter df to include data only in the window of <winmax> seconds
        # around the event time
        streams_df_new = [df[(df.time >= s_time) &
                             (df.time <= e_time)]
                          for df in streams_df]
        # print "NewStreams:\n", streams_df_new

        # Detect edges for both meters
        edge_list.append(detect_edges_from_meters(streams_df_new))
    # print "Edges_i:\n", edge_list

    # ---Accumulate start/end edges from each meter---
    meter_edges_list = [{}]
    edge_dict = edge_list[0]
    if len(edge_dict.keys()) == 2:
        meter_edges_list.append({})

    flag = False  # indicates whether light meter exists
    for i, edge_dict in enumerate(edge_list):

        if "Light" in edge_dict.keys():
            flag = True
            light_df = edge_dict["Light"]

            # Filter edges if rising edge has a negative power
            if i == 0:
                light_df = light_df[light_df.magnitude > 0]
                meter_edges_list[0]["start"] = light_df
            # Filter edges if falling edge has a positive power
            else:
                light_df = light_df[light_df.magnitude < 0]
                meter_edges_list[0]["end"] = light_df

        if "Power" in edge_dict.keys():
            power_df = edge_dict["Power"]

            if flag:
                l_ix = 1
            else:
                l_ix = 0

            # Filter edges if rising edge has a negative power
            if i == 0:
                power_df = power_df[power_df.magnitude > 0]
                meter_edges_list[l_ix]["start"] = power_df
            # Filter edges if falling edge has a positive power
            else:
                power_df = power_df[power_df.magnitude < 0]
                meter_edges_list[l_ix]["end"] = power_df

    # print "\nEdges:\n", meter_edges_list

    # ---Determine in which meter, edge was detected and computer power---
    for meter_edges in meter_edges_list:
        start_df = meter_edges["start"]
        end_df = meter_edges["end"]

        start_len = len(start_df)
        end_len = len(end_df)
        if start_len == 1 and end_len == 1:
            start_mag = start_df.ix[start_df.index[0]]["magnitude"]
            end_mag = math.fabs(end_df.ix[end_df.index[0]]["magnitude"])
            # Compute power
            power = compute_power(start_mag, end_mag)
            print "Power consumed:", power
        elif start_len > 1 and end_len > 1:
            print "CONFUSION!!"
    return power


def combine_streams(df):
    """
    Receives the light and power streams and combines them into one stream
    """

    stream1_df = df[0]
    stream2_df = df[1]

    stream1_df['time'] = (stream1_df['time'] / 1000).astype('int')
    stream2_df['time'] = (stream2_df['time'] / 1000).astype('int')

    print stream1_df.head()
    print stream2_df.head()

    start_time = min(stream1_df.ix[0]['time'], stream2_df.ix[0]['time'])
    end_time = max(stream1_df.ix[stream1_df.index[-1]]['time'],
                   stream2_df.ix[stream2_df.index[-1]]['time'])
    # print "ST:", start_time, "ET:", end_time

    time_values = range(start_time, end_time + 1)
    n_time_values = len(time_values)
    # print "Total values", n_time_values

    stream1 = dict(zip(stream1_df.time, stream1_df.power))
    stream2 = dict(zip(stream2_df.time, stream2_df.power))

    # print "Stream1", stream1
    # print "Stream2", stream2

    stream1_new = dict(zip(time_values, [np.NaN] * n_time_values))
    stream2_new = dict(zip(time_values, [np.NaN] * n_time_values))
    for t in time_values:
        if t in stream1:
            stream1_new[t] = stream1[t]
        if t in stream2:
            stream2_new[t] = stream2[t]

    # Sorting dictionaries
    streams = [pd.DataFrame(columns=['time', 'power'])] * 2
    for i, stream in enumerate([stream1_new, stream2_new]):
        for key in sorted(stream.iterkeys()):
            stream[key] = stream[key]

        streams[i] = pd.DataFrame(stream.items(), columns=['time', 'power'])
        streams[i].fillna(method='pad', inplace=True)
        streams[i].fillna(method='bfill', inplace=True)
        # print "Stream", i, ":\n", streams[i].head(10)

    # Combining Streams
    comb_stream_df = pd.DataFrame({'time': time_values, 'power': [0] * n_time_values},
                                  columns=['time', 'power'])
    comb_stream_df['time'] = comb_stream_df['time'] * 1000
    for idx in comb_stream_df.index:
        comb_stream_df.ix[idx]['power'] = streams[0].ix[idx]['power'] + streams[1].ix[idx]['power']

    comb_stream_df.sort('time', inplace=True)
    # print "Combined Stream:\n", comb_stream_df.head(20)

    return comb_stream_df
