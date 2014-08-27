"""
Find the edges from the raw power data

Author: Manaswi Saha
Date: 21th August 2014
"""

import pandas as pd
import math
import datetime as dt

from energylenserver.common_imports import *
from filters import *

# Global variables
stars = 30


def detect_edges(streams_df):
    """
    Detect edges from both meters
    """
    stream_edges = {}
    for i, df_i in enumerate(streams_df):
        first_idx = df_i.index[0]
        stream_type = df_i.ix[first_idx]['type']

        print "Detecting Edges for Stream:", stream_type
        edges = []
        ix_list_l = df_i.index
        for idx in range(first_idx + 1, ix_list_l[-1] - winmin + 1):
            edge_type, edge = check_if_edge(df_i, idx, "power")
            if edge_type != "Not an edge":
                edges.append(edge)
                print "Edge:", edge

        # Storing edges in a df
        edges_df = pd.DataFrame()
        if len(edges) >= 1:
            edges_df = pd.DataFrame(
                edges, columns=['index', 'time', 'magnitude', 'curr_power'])
            edges_df = edges_df.set_index('index', drop=True)

            # Filter edges
            edges_df = filter_select_maxtime_edge(edges_df)
        else:
            edges_df = edges_df = pd.DataFrame(columns=['index', 'time',
                                                        'magnitude', 'curr_power'])

        stream_edges[stream_type] = edges_df
        # print "Stream edges:\n", stream_edges
    return stream_edges


def check_if_edge(df, index, power_stream):
    """
    Determines an edge at the specified index in the stream received

    Returns: Edge parameters
    """
    # Taken code from power edge
    # Match with light edge and add the differences
    i = index
    prev = int(round(df.ix[i - 1][power_stream]))
    curr = int(round(df.ix[i][power_stream]))
    next = int(round(df.ix[i + 1][power_stream]))
    currwin = int(round(df.ix[i + winmin][power_stream]))

    time = df.ix[i]['time']

    if i - winmin not in (df.index):
        prevwin = 0
    else:
        prevwin = int(round(df.ix[i - winmin][power_stream]))
        if power_stream != "power":
            if math.floor(prevwin) != 0:
                prevwin = prevwin + 10
        # prevwintime = df.ix[i - pwinmin]['time']

    time = df.ix[i]['time']
    per_thresmin = int(0.25 * curr)

    # Checking for missing time samples
    prev_time = df.ix[i - 1]['time']
    next_time = df.ix[i + 1]['time']

    # Indicates next time sample is missing
    prev_missing_sample = (time - prev_time) > 1
    next_missing_sample = (next_time - time) > 1

    prev_curr_diff = int(math.fabs(curr - prev))
    curr_next_diff = int(math.fabs(next - curr))
    curr_nextwin_diff = int(currwin - curr)
    curr_prevwin_diff = int(prevwin - curr)

    # if (prev_curr_diff < thresmin and curr_nextwin_diff >= thresmin and
    #         curr_next_diff > prev_curr_diff and curr_next_diff > 0):

    # Stricter restrictions
    if (prev_curr_diff < thresmin and curr_nextwin_diff >= thresmin and
        ((curr_next_diff == 0 and prev_curr_diff == 0) or (curr_next_diff > prev_curr_diff))
       and curr_next_diff > 0):

        # logger.debug("\nR1::", i, "currtime", dt.datetime.fromtimestamp(time),)
        # logger.debug("prev ", prev, "curr ", curr, "next ", next,)
        # logger.debug("currwin", currwin)
        # logger.debug("prev_curr_diff", prev_curr_diff, "prevwintime",
            # dt.datetime.fromtimestamp(prevwintime))
        # logger.debug("curr_next_diff ", curr_next_diff,)
        # logger.debug("curr_nextwin_diff", curr_nextwin_diff, "curr_prevwin_diff")
        # curr_prevwin_diff

        edge_type = "rising"
        if (curr_next_diff >= per_thresmin):
            # Storing the rising edge e_i = (time_i, mag_i)
            row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
            return edge_type, row
        if next_missing_sample and curr_next_diff > thresmin:
            logger.debug("Missing Sample:: Index %s", i)
            # Storing the rising edge e_i = (time_i, mag_i)
            row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
            return edge_type, row
        elif (curr_next_diff > per_thresmin):
            logger.debug("Here1 Index:: %s", i)
            # Storing the rising edge e_i = (time_i, mag_i)
            row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
            return edge_type, row
        else:
            logger.debug("Here2 Index:: %s", i)
            pass
    elif (prev_curr_diff < thresmin and curr_nextwin_diff > thresmin
          and curr_next_diff >= per_thresmin and curr_next_diff > 0):

        # logger.debug("\nR2::", i, "currtime", dt.datetime.fromtimestamp(time), "prev ",)
        # logger.debug(prev, "curr ", curr, "next ", next,)
        # logger.debug("currwin", currwin)
        # logger.debug("prev_curr_diff", prev_curr_diff,
            # "prevwintime", dt.datetime.fromtimestamp(prevwintime))
        # logger.debug("curr_next_diff ", curr_next_diff,)
        # logger.debug("curr_nextwin_diff", curr_nextwin_diff, "curr_prevwin_diff",)
        # curr_prevwin_diff

        edge_type = "rising"
        # Storing the rising edge e_i = (time_i, mag_i)
        row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
        return edge_type, row

    elif (prev_curr_diff < thresmin and math.floor(curr_nextwin_diff) <= (-thresmin)
          and ((curr_next_diff == 0 and prev_curr_diff == 0) or (curr_next_diff > prev_curr_diff))
          and curr_prevwin_diff > -thresmin):

        # logger.debug("\nF::", "currtime", dt.datetime.fromtimestamp(time),)
        # logger.debug("prev ", prev, "curr ", curr, "next ", next,)
        # logger.debug("currwin", currwin)
        # logger.debug("prev_curr_diff", prev_curr_diff,
            # "prevwintime", dt.datetime.fromtimestamp(prevwintime))
        # logger.debug("curr_next_diff ", curr_next_diff)
        # logger.debug("curr_nextwin_diff", curr_nextwin_diff, "curr_prevwin_diff",)
        # curr_prevwin_diff

        edge_type = "falling"
        if prev_missing_sample is True or next_missing_sample is True:
            logger.debug("Falling Edge1:: Index %s", i)
            # Storing the falling edge e_i = (time_i, mag_i)
            row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
            return edge_type, row
        elif curr_next_diff < thresmin or curr_next_diff > thresmin:
            logger.debug("Falling Edge2:: Index %s", i)
            # Storing the falling edge e_i = (time_i, mag_i)
            row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
            return edge_type, row
        else:
            pass
    return "Not an edge", {}
