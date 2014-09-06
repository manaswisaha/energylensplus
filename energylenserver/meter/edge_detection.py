"""
Find the edges from the raw power data

Author: Manaswi Saha
Date: 21th August 2014
"""

import math
import json
import time as t
import pandas as pd
# import datetime as dt

from filters import *
from energylenserver.common_imports import *

# Global variables
stars = 30

def detect_and_filter_edges(df):
    """
    1. Detect edges
    2. Perform Preprocessing Step 1a: Filter appliances that are not of interest
    e.g. washing machine, fridge and geyser

    :param df:
    :return edges:
    """
    edges_df = detect_edges(df)
    filter_unmon_appl_edges(edges_df)

def detect_edges_from_meters(streams_df):
    """
    Detect edges from both meters
    """
    stream_edges = {}
    for i, df_i in enumerate(streams_df):
        first_idx = df_i.index[0]
        stream_type = df_i.ix[first_idx]['type']

        print "Detecting Edges for Stream:", stream_type
        stream_edges[stream_type] = detect_edges(df_i)
        # print "Stream edges:\n", stream_edges
    return stream_edges

def detect_edges(df):
    """
    Detect edges from both meters
    """

    rise_edges = []
    fall_edges = []

    ix_list_l = df.index
    first_idx = ix_list_l[0]
    for idx in range(first_idx + 1, ix_list_l[-1] - winmin + 1):
        edge_type, edge = check_if_edge(df, idx, "power")
        if edge_type == "rising":
            rise_edges.append(edge)
        elif edge_type == "falling":
            fall_edges.append(edge)
        # print "Edge: " + str(edge)

    # --Storing edges in a df--
    rise_df = pd.DataFrame(columns=['index', 'time',
                                    'magnitude', 'type', 'curr_power'])
    fall_df = pd.DataFrame(columns=['index', 'time',
                                    'magnitude', 'type', 'curr_power'])
    edges_df = pd.DataFrame(columns=['index', 'time',
                                     'magnitude', 'type', 'curr_power'])
    if len(rise_edges) >= 1 or len(fall_edges) >= 1:

        if len(rise_edges) >= 1:
            # --Rising Edges--
            rise_df = pd.DataFrame(
                rise_edges, columns=['index', 'time', 'magnitude', 'type', 'curr_power'])

            # Filter rising edges
            rise_df = filter_select_maxtime_edge(rise_df)

        if len(fall_edges) >= 1:
            # --Falling Edges--
            fall_df = pd.DataFrame(
                fall_edges, columns=['index', 'time', 'magnitude', 'type', 'curr_power'])

            # Filter falling edges
            fall_df = filter_select_maxtime_edge(fall_df)

        # Final set of edges
        edges_df = pd.concat([rise_df, fall_df])
        edges_df = edges_df.set_index('index', drop=True)

    return edges_df




def check_if_edge(df, index, power_stream):
    """
    Determines an edge at the specified index in the stream received

    Returns: Edge parameters
    """
    i = index
    prev = int(round(df.ix[i - 1][power_stream]))
    curr = int(round(df.ix[i][power_stream]))
    next = int(round(df.ix[i + 1][power_stream]))
    currnextnext = int(round(df.ix[i + 2][power_stream]))
    currwin = int(round(df.ix[i + winmin][power_stream]))

    time = df.ix[i]['time']

    if i - winmin not in (df.index):
        prevwin = 0
    else:
        prevwin = int(round(df.ix[i - winmin][power_stream]))

    time = df.ix[i]['time']
    per_current_val = int(0.25 * curr)

    # Checking for missing time samples
    prev_time = df.ix[i - 1]['time']
    next_time = df.ix[i + 1]['time']

    # Indicates next time sample is missing
    prev_missing_sample = (time - prev_time) > sampling_rate
    next_missing_sample = (next_time - time) > sampling_rate

    prev_curr_diff = int(math.fabs(curr - prev))
    curr_next_diff = int(math.fabs(next - curr))
    curr_nextwin_diff = int(currwin - curr)
    curr_prevwin_diff = int(prevwin - curr)
    curr_nextnext_diff = int(currnextnext - curr)

    # if curr_nextwin_diff > 0:
    #     print("RISETEST::{0}:: TIME: [{1}] MAG::{2}".format(i, t.ctime(time), curr_nextwin_diff))
    #     print("prev={0} curr={1} next={2}".format(prev, curr, next))
    #     print("curr_next_diff::{0}  prev_curr_diff::{1}".format(curr_next_diff, prev_curr_diff))

    # print "[" + t.ctime(time) + "] currnextnextDIFF:" + str(math.fabs(curr_nextnext_diff))
    # Removes spikes
    if math.fabs(curr_nextnext_diff) < thresmin:
        # print("[{0} currnextnext:{1} curr_nextnext_diff:{2}".format(
        #     t.ctime(time), currnextnext, math.fabs(curr_nextnext_diff)))
        return "Not an edge", {}

    # Rising Edge
    if (curr_nextwin_diff >= thresmin and prev_curr_diff <= 5 and curr_next_diff > prev_curr_diff):

        print("Rise::{0}:: TIME: [{1}] MAG::{2}".format(i, t.ctime(time), curr_nextwin_diff))
        print("prev={0} curr={1} next={2}".format(prev, curr, next))
        print("curr_next_diff::{0}  prev_curr_diff::{1} curr_nextnext_diff::{2}".
              format(curr_next_diff, prev_curr_diff, math.fabs(curr_nextnext_diff)))

        edge_type = "rising"

        if next_missing_sample and curr_next_diff >= thresmin:
            # Storing the rising edge e_i = (time_i, mag_i)
            row = {"index": i, "time": time, "magnitude":
                   curr_nextwin_diff, "type": edge_type, "curr_power": curr}
            # print "Missing Sample: edge at [" + t.ctime(time) + "]" + json.dumps(row)
            return edge_type, row
        else:
            # print "Rise: None of the conditions satisfied:: [" + t.ctime(time) + "]"
            pass

    # Falling Edge
    elif (prev_curr_diff < thresmin and math.floor(curr_nextwin_diff) <= -thresmin
          and ((curr_next_diff != 0 and prev_curr_diff != 0) or (curr_next_diff > prev_curr_diff))
          and math.fabs(curr_prevwin_diff) < thresmin and curr_next_diff > thresmin):

        print("Fall::{0}:: TIME: [{1}] MAG::{2}".format(i, t.ctime(time), curr_nextwin_diff))
        print("prev={0} curr={1} next={2}".format(prev, curr, next))
        print("curr_next_diff::{0} prev_curr_diff::{1} curr_prevwin_diff::{2}".
              format(curr_next_diff, prev_curr_diff,
                     curr_prevwin_diff))

        edge_type = "falling"
        if curr_next_diff < thresmin or curr_next_diff > thresmin:
            # Storing the falling edge e_i = (time_i, mag_i)
            row = {"index": i, "time": time, "magnitude":
                   curr_nextwin_diff, "type": edge_type, "curr_power": curr}
            # print "Falling Edge2: edge at [" + t.ctime(time) + "]" + json.dumps(row)
            return edge_type, row

        if prev_missing_sample is True or next_missing_sample is True:
            # Storing the falling edge e_i = (time_i, mag_i)
            row = {"index": i, "time": time, "magnitude":
                   curr_nextwin_diff, "type": edge_type, "curr_power": curr}
            # print "Falling Edge1: edge at [" + t.ctime(time) + "]" + json.dumps(row)
            return edge_type, row

        else:
            # print "Fall: None of the conditions satisfied: [" + t.ctime(time) + "]"
            pass
    return "Not an edge", {}
