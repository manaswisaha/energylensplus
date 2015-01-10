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

# Enable Logging
logger = logging.getLogger('energylensplus_meterdata')

# Global variables
stars = 30


def detect_edges_from_meters(streams_df):
    """
    Detect edges from both meters
    Usage: Computing Metadata calculation
    """
    stream_edges = {}
    for i, df_i in enumerate(streams_df):
        if len(df_i.index) == 0:
            continue
        first_idx = df_i.index[0]
        stream_type = df_i.ix[first_idx]['type']

        logger.debug("Detecting Edges for Stream: %s", stream_type)
        stream_edges[stream_type] = detect_edges(df_i)
        # logger.debug("Stream edges:\n%s", stream_edges)
    logger.debug("Training Data Computation over")
    return stream_edges


def detect_and_filter_edges(df):
    """
    Entry function for edge detection
    1. Detect edges
    2. Perform Preprocessing Step 1a: Filter appliances that are not of interest
    e.g. washing machine, fridge and geyser

    :param df:
    :return edges:
    """
    edges_df = detect_edges(df)
    if len(edges_df) > 0:
        logger.debug("Edges: %s\n", edges_df)
    edges_df = filter_unmon_appl_edges(edges_df)
    edges_df = filter_transitional_edges(edges_df)

    return edges_df


def detect_edges(df):
    """
    Detect edges from both meters
    """

    rise_edges = []
    fall_edges = []

    try:

        ix_list_l = df.index
        first_idx = ix_list_l[0]
        for idx in range(first_idx + 1, ix_list_l[-1] - winmax + 1):
            edge_type, edge = check_if_edge(df, idx, "power")
            if edge_type == "rising":
                rise_edges.append(edge)
            elif edge_type == "falling":
                fall_edges.append(edge)
            # logger.debug("Edge: " + str(edge)

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

        # logger.debug("Edges: %s\n", edges_df)
        return edges_df
    except Exception, e:
        logger.exception("[DetectEdgesException]:: %s", e)


def check_if_edge(df, index, power_stream):
    """
    Determines an edge at the specified index in the stream received

    Returns: Edge parameters
    """
    i = index
    try:
        prev = int(round(df.ix[i - 1][power_stream]))
        curr = int(round(df.ix[i][power_stream]))
        next = int(round(df.ix[i + 1][power_stream]))
        currnextnext = int(round(df.ix[i + 2][power_stream]))
        currwin = int(round(df.ix[i + winmin][power_stream]))

        time = df.ix[i]['time']
        tprev = int(round(df.ix[i - 1]['time']))
        tcurr = int(round(df.ix[i]['time']))
        tnext = int(round(df.ix[i + 1]['time']))
        tcurrwin = int(round(df.ix[i + winmin]['time']))

        if i - winmin not in (df.index):
            prevwin = 0
        else:
            prevwin = int(round(df.ix[i - winmin][power_stream]))

        per_thresmin = int(0.5 * thresmin)

        time = df.ix[i]['time']

        # Checking for missing time samples
        prev_time = df.ix[i - 1]['time']
        next_time = df.ix[i + 1]['time']

        # Indicates next time sample is missing
        prev_missing_sample = (
            (time - prev_time) > sampling_rate) and ((time - prev_time) < 2 * sampling_rate)
        next_missing_sample = (
            (next_time - time) > sampling_rate) and ((next_time - time) < 2 * sampling_rate)

        prev_curr_diff = int(math.fabs(curr - prev))
        curr_next_diff = int(math.fabs(next - curr))
        curr_nextwin_diff = int(currwin - curr)
        curr_prevwin_diff = int(prevwin - curr)
        curr_nextnext_diff = int(currnextnext - curr)

        magnitude = curr_nextwin_diff

        if magnitude > 0:
            # Indicates a rising edge
            # Use the winmax window for determining the edge
            currwin = int(round(df.ix[i + winmax][power_stream]))
            tcurrwin = int(round(df.ix[i + winmax]['time']))
            curr_nextwin_diff = int(currwin - curr)
            magnitude = curr_nextwin_diff

        # logger.debug("CR [%s] MAG: %s Curr: %s", t.ctime(tcurr), magnitude, curr)
        # logger.debug("CW [%s] Currwin: %s", t.ctime(tcurrwin), currwin)

        '''
        if curr_next_diff >= thresmin and math.fabs(magnitude) >= thresmin:
            logger.debug("EDGETEST::{0}:: TIME: [{1}] MAG::{2}".format(
                i, t.ctime(time), magnitude))
            logger.debug("tprev=[{0}] prev={1}".format(t.ctime(tprev), prev))
            logger.debug("tcurr=[{0}] curr={1}".format(t.ctime(tcurr), curr))
            logger.debug("tnext=[{0}] next={1}".format(t.ctime(tnext), next))
            logger.debug("tcurrwin=[{0}] currwin={1}".format(t.ctime(tcurrwin), currwin))
            logger.debug("curr_next_diff::{0}  prev_curr_diff::{1}".format(
                curr_next_diff, prev_curr_diff))
            logger.debug("curr_nextnext_diff::{0} curr_prevwin_diff::{1}".format(
                curr_nextnext_diff, curr_prevwin_diff))
        '''

        # For falling edge: for comparison with curr_next_diff
        if magnitude < 0:
            mag_abs = math.fabs(magnitude)
            if mag_abs <= 50:
                per_current_val = int(0.45 * mag_abs)
            else:
                per_current_val = int(0.25 * mag_abs)

        # Removes spikes
        if math.fabs(curr_nextnext_diff) < thresmin:
            # logger.debug("[{0} currnextnext:{1} curr_nextnext_diff:{2}".format(
            #     t.ctime(time), currnextnext, math.fabs(curr_nextnext_diff)))
            return "Not an edge", {}

        # Rising Edge
        if ((magnitude >= thresmin or curr_next_diff >= thresmin) and magnitude > 0
                and prev_curr_diff < thresmin and curr_next_diff > prev_curr_diff):

            logger.debug("Rise::{0}:: TIME: [{1}] MAG::{2}".format(i, t.ctime(time), magnitude))
            logger.debug("tprev=[{0}] prev={1}".format(t.ctime(tprev), prev))
            logger.debug("tcurr=[{0}] curr={1}".format(t.ctime(tcurr), curr))
            logger.debug("tnext=[{0}] next={1}".format(t.ctime(tnext), next))
            logger.debug("tcurrwin=[{0}] currwin={1}".format(t.ctime(tcurrwin), currwin))
            logger.debug("curr_next_diff::{0}  prev_curr_diff::{1} curr_nextnext_diff::{2}".
                         format(curr_next_diff, prev_curr_diff, math.fabs(curr_nextnext_diff)))

            edge_type = "rising"

            if curr_next_diff > magnitude:
                magnitude = curr_next_diff

            if next_missing_sample and curr_next_diff >= thresmin:

                # Storing the rising edge e_i = (time_i, mag_i)
                row = {"index": i, "time": time, "magnitude":
                       magnitude, "type": edge_type, "curr_power": curr}

                logger.debug("[EDGE FOUND::RISE] Missing Sample: [%s] %s",
                             t.ctime(time), json.dumps(row))
                return edge_type, row

            if curr_next_diff >= per_thresmin:

                # Storing the rising edge e_i = (time_i, mag_i)
                row = {"index": i, "time": time, "magnitude":
                       magnitude, "type": edge_type, "curr_power": curr}
                logger.debug("[EDGE FOUND::RISE] Curr Next greater: edge at [%s] %s",
                             t.ctime(time), magnitude)
                return edge_type, row
            else:
                # logger.debug("Rise: None of the conditions satisfied:: [" + t.ctime(time) + "]"
                pass

        # Falling Edge
        elif (prev_curr_diff < thresmin and math.floor(magnitude) <= -thresmin
              and ((curr_next_diff != 0) or (curr_next_diff > prev_curr_diff))
              and math.fabs(curr_prevwin_diff) < thresmin and curr_next_diff >= per_current_val):

            logger.debug("Fall::{0}:: TIME: [{1}] MAG::{2}".format(i, t.ctime(time), magnitude))
            logger.debug("tprev=[{0}] prev={1}".format(t.ctime(tprev), prev))
            logger.debug("tcurr=[{0}] curr={1}".format(t.ctime(tcurr), curr))
            logger.debug("tnext=[{0}] next={1}".format(t.ctime(tnext), next))
            logger.debug("tcurrwin=[{0}] currwin={1}".format(t.ctime(tcurrwin), currwin))
            logger.debug("curr_next_diff::{0} prev_curr_diff::{1} curr_prevwin_diff::{2}".
                         format(curr_next_diff, prev_curr_diff,
                                curr_prevwin_diff))

            edge_type = "falling"
            if curr_next_diff < thresmin or curr_next_diff > thresmin:
                # Storing the falling edge e_i = (time_i, mag_i)
                row = {"index": i, "time": time, "magnitude":
                       magnitude, "type": edge_type, "curr_power": curr}
                logger.debug("[EDGE FOUND::FALL] [%s] %s", t.ctime(time), magnitude)
                return edge_type, row

            if prev_missing_sample is True or next_missing_sample is True:
                # Storing the falling edge e_i = (time_i, mag_i)
                row = {"index": i, "time": time, "magnitude":
                       magnitude, "type": edge_type, "curr_power": curr}
                logger.debug(
                    "[EDGE FOUND::FALL] Missing sample: [%s] %s", t.ctime(time), magnitude)
                return edge_type, row

            else:
                # logger.debug("Fall: None of the conditions satisfied: [" + t.ctime(time) + "]"
                pass
    except Exception, e:
        logger.exception("[CheckEdgesException]:: %s", e)

    return "Not an edge", {}
