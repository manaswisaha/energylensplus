"""
Find the edges from the raw power data

Author: Manaswi Saha
Date: 21th August 2014
"""

import pandas as pd
import os
import sys
import math
import datetime as dt
from collections import defaultdict
import numpy as np
import warnings
import logging

from constants import *

# Global variables
stars = 30

# Disable warnings
warnings.filterwarnings('ignore')

# Enable Logging
logger = logging.getLogger('energy-lens-plus')
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)


def check_if_light_edge(df_l, index, power_stream):

    i = index
    prev = int(round(df_l.ix[i - 1][power_stream]))
    curr = int(round(df_l.ix[i][power_stream]))
    next = int(round(df_l.ix[i + 1][power_stream]))
    currwin = int(round(df_l.ix[i + lwinmin][power_stream]))

    if i - lwinmin not in (df_l.index):
        prevwin = 0
    else:
        prevwin = int(df_l.ix[i - lwinmin][power_stream])

    # If checking for a particular phase, increase by 10 watts
    if power_stream != "lightpower":
        if math.floor(prev) != 0:
            prev = prev + 10
        if math.floor(curr) != 0:
            curr = curr + 10
        if math.floor(next) != 0:
            next = next + 10
        if math.floor(currwin) != 0:
            currwin = currwin + 10

    time = df_l.ix[i]['time']
    per_lthresmin = int(0.25 * lthresmin)

    # Checking for missing time samples
    prev_time = df_l.ix[i - 1]['time']
    next_time = df_l.ix[i + 1]['time']

    # Indicates next time sample is missing
    prev_missing_sample = (time - prev_time) > 1
    next_missing_sample = (next_time - time) > 1

    prev_curr_diff = curr - prev
    curr_next_diff = int(math.fabs(next - curr))
    curr_prevwin_diff = prevwin - curr
    curr_nextwin_diff = currwin - curr

    # print "Looking for light edge in stream:", power_stream, "for Index:", i
    # print "Magnitude::", curr_nextwin_diff

    # if(time in [1385466741, 1385467127, 1385485791, 1385486655]):
    #     logger.debug("\n")
    #     logger.debug("Per lthresmin %d", per_lthresmin)
    #     logger.debug(
    #         "Looking for light edge in stream: %s for Index: %d", power_stream, i)
    #     logger.debug("R:: currtime %s prev %s curr %s next %s",
    #                  dt.datetime.fromtimestamp(time), prev, curr, next)
    #     logger.debug("currwin %s", currwin)
    #     logger.debug(
    #         "prev_curr_diff %s curr_next_diff %s", prev_curr_diff, curr_next_diff)
    #     logger.debug("curr_nextwin_diff %s curr_prevwin_diff %s",
    #                  curr_nextwin_diff, curr_prevwin_diff)

    #     if (prev_curr_diff < per_lthresmin and curr_nextwin_diff >= lthresmin and
    #         ((curr_next_diff == 0 and prev_curr_diff == 0) or (curr_next_diff > prev_curr_diff))
    #        and curr_next_diff > 0):
    #         logger.debug("True")
    #         logger.debug("Missing Sample value %s", next_missing_sample)
    #         logger.debug("Curr next diff %s", curr_next_diff)
    #         if next_missing_sample:
    #             logger.debug("Missing Sample yes")
    #         if int(curr_next_diff) >= lthresmin:
    #             logger.debug("Satisfied condition")
    #     elif (prev_curr_diff < per_lthresmin and curr_next_diff >= per_lthresmin
    #           and curr_nextwin_diff > lthresmin):
    #         logger.debug(" CurrNextDiff between lthresmin half: %d", i)
    #     elif prev_curr_diff < lthresmin and curr_nextwin_diff > lthresmin:
    #         logger.debug("True-- Fan")
    #     elif (prev_curr_diff < lthresmin and math.floor(curr_nextwin_diff) <= (-lthresmin)
    #           and curr_next_diff > prev_curr_diff):
    #         logger.debug("True - Falling")

    # logger.debug(
    #     "\nR:: %d currtime %s prev %s curr %s next %s", i, dt.datetime.fromtimestamp(time),
    #     prev, curr, next)
    # logger.debug("currwin:%s", currwin)
    # logger.debug("prev_curr_diff : %s curr_next_diff %s", prev_curr_diff, curr_next_diff)
    # logger.debug("curr_nextwin_diff :%s", curr_nextwin_diff)

    if (prev_curr_diff < per_lthresmin and curr_nextwin_diff >= lthresmin and
            ((curr_next_diff == 0 and prev_curr_diff == 0) or (curr_next_diff > prev_curr_diff))
       and curr_next_diff > 0):

        logger.debug(
            "\nR1:: %d currtime %s prev %s curr %s next %s", i, dt.datetime.fromtimestamp(time),
            prev, curr, next)
        # logger.debug("currwin", currwin)
        # logger.debug("prev_curr_diff", prev_curr_diff, "curr_next_diff ", curr_next_diff)
        # logger.debug("curr_nextwin_diff", curr_nextwin_diff, "curr_prevwin_diff")
        # curr_prevwin_diff

        edge_type = "rising"
        # Only checking these conditions for cumulative power
        if power_stream == "lightpower":
            if next_missing_sample and int(curr_next_diff) > lthresmin:
                logger.debug("Missing Sample:: Index %d", i)
                # Storing the rising edge e_i = (time_i, mag_i)
                row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
                return edge_type, row
            # or curr_next_diff > lthresmin:
            elif (curr_next_diff >= per_lthresmin):
                logger.debug("Here1 Index:: %d", i)
                # Storing the rising edge e_i = (time_i, mag_i)
                row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
                return edge_type, row
            else:
                pass
        else:
            # Storing the rising edge e_i = (time_i, mag_i)
            row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
            return edge_type, row
    elif (prev_curr_diff < per_lthresmin and curr_next_diff >= per_lthresmin
          and curr_nextwin_diff > lthresmin):
        logger.debug(
            "\nR2:: %d currtime %s prev %s curr %s next %s", i, dt.datetime.fromtimestamp(time),
            prev, curr, next)
        # logger.debug("\nR2::" , i, "currtime", dt.datetime.fromtimestamp(time), "prev")
        # logger.debug(prev, "curr ", curr, "next ", next,)
        # logger.debug("currwin", currwin)
        # logger.debug("prev_curr_diff", prev_curr_diff, "curr_next_diff ", curr_next_diff,)
        # logger.debug("curr_nextwin_diff", curr_nextwin_diff, "curr_prevwin_diff",)
        # curr_prevwin_diff

        edge_type = "rising"
        # Storing the rising edge e_i = (time_i, mag_i)
        row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
        return edge_type, row

    elif (prev_curr_diff < lthresmin and math.floor(curr_nextwin_diff) <= (-lthresmin)
          and ((curr_next_diff == 0 and prev_curr_diff == 0) or (curr_next_diff > prev_curr_diff))
          and curr_prevwin_diff > -lthresmin):

        # logger.debug("\nF::", "currtime", dt.datetime.fromtimestamp(time),
            # "prev ", prev, "curr ", curr, "next ", next,)
        # logger.debug("currwin", currwin)
        # logger.debug("prev_curr_diff", prev_curr_diff, "curr_next_diff ", curr_next_diff)
        # logger.debug("curr_nextwin_diff", curr_nextwin_diff, "curr_prevwin_diff",)
        # curr_prevwin_diff

        edge_type = "falling"
        if prev_missing_sample is True or next_missing_sample is True:
            # Storing the falling edge e_i = (time_i, mag_i)
            row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
            return edge_type, row
        elif curr_next_diff < lthresmin or curr_next_diff >= lthresmin:
            # Storing the falling edge e_i = (time_i, mag_i)
            row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
            return edge_type, row
        else:
            pass
    return "Not an edge", {}


def check_if_power_edge(df_p, index, power_stream):

    i = index
    prev = df_p.ix[i - 1][power_stream]
    curr = df_p.ix[i][power_stream]
    next = df_p.ix[i + 1][power_stream]
    currwin = int(round(df_p.ix[i + pwinmin][power_stream]))

    # If checking for a particular phase, increase by 10 watts
    if power_stream != "power":
        if math.floor(prev) != 0:
            prev = prev + 10
        if math.floor(curr) != 0:
            curr = curr + 10
        if math.floor(next) != 0:
            next = next + 10
        if math.floor(currwin) != 0:
            currwin = currwin + 10

    time = df_p.ix[i]['time']

    if i - pwinmin not in (df_p.index):
        prevwin = 0
    else:
        prevwin = int(df_p.ix[i - pwinmin][power_stream])
        if power_stream != "power":
            if math.floor(prevwin) != 0:
                prevwin = prevwin + 10
        # prevwintime = df_p.ix[i - pwinmin]['time']
    time = df_p.ix[i]['time']
    per_pthresmin = int(0.25 * curr)

    # Checking for missing time samples
    prev_time = df_p.ix[i - 1]['time']
    next_time = df_p.ix[i + 1]['time']

    # Indicates next time sample is missing
    prev_missing_sample = (time - prev_time) > 1
    next_missing_sample = (next_time - time) > 1

    prev_curr_diff = int(math.fabs(curr - prev))
    curr_next_diff = int(math.fabs(next - curr))
    curr_nextwin_diff = int(currwin - curr)
    curr_prevwin_diff = int(prevwin - curr)

    # Code for debugging
    # range(2683, 3652)
    # if time in [1385480507]:
    #     logger.debug(
    #         "Looking for power edge for Index %d in power_stream %s", i, power_stream)
    #     logger.debug("F:: currtime %s prev %s curr %s next %s",
    #                  dt.datetime.fromtimestamp(time), prev, curr, next)
    #     logger.debug("currwin %s", currwin)
    #     logger.debug(
    #         "prev_curr_diff %s curr_next_diff %s", prev_curr_diff, curr_next_diff,)
    #     logger.debug("curr_nextwin_diff %s", curr_nextwin_diff)

    #     logger.debug("Per pthresmin %s", per_pthresmin)

    #     if (prev_curr_diff < pthresmin):
    #         logger.debug("prev_curr_diff < pthresmin 1True")
    #     else:
    #         logger.debug("prev_curr_diff < pthresmin False1")
    #     if curr_next_diff > prev_curr_diff and curr_next_diff > 0:
    #         logger.debug(
    #             "curr_next_diff > prev_curr_diff and curr_next_diff > 0: 2True")
    #     else:
    #         logger.debug(
    #             "curr_next_diff > prev_curr_diff and curr_next_diff > 0: False2")
    #     if curr_nextwin_diff <= -pthresmin or curr_nextwin_diff <= lthresmin:
    #         logger.debug("curr_nextwin_diff <= -l/pthresmin: 3True")
    #     else:
    #         logger.debug("curr_nextwin_diff <= -pthresmin: False3")
    #     if curr_next_diff != prev_curr_diff:
    #         logger.debug("curr_next_diff != prev_curr_diff: 4True")
    #     else:
    #         logger.debug("curr_next_diff != prev_curr_diff: 4False")
    #     if curr_next_diff >= per_pthresmin:
    #         logger.debug("curr_next_diff >= per_pthresmin: 5True")
    #     else:
    #         logger.debug("curr_next_diff >= per_pthresmin: False5")
    #     if curr_nextwin_diff > pthresmin:
    #         logger.debug("curr_nextwin_diff > pthresmin: True6")
    #     else:
    #         logger.debug("curr_nextwin_diff > pthresmin: False6")

    # Original Edge Detection Algorithm for Power Edges
    # if (prev_curr_diff < pthresmin and curr_nextwin_diff >= pthresmin
    #    and curr_next_diff > prev_curr_diff
    #    and curr_next_diff >= per_pthresmin):

    #     edge_type = "rising"
    # Storing the rising edge e_i = (time_i, mag_i)
    #     row = {"index": i, "time": time, "magnitude": curr_nextwin_diff}
    #     return edge_type, row
    # elif (prev_curr_diff < pthresmin and curr_nextwin_diff <= (-pthresmin)
    #       and curr_next_diff > prev_curr_diff
    #       and int(curr_next_diff) >= per_pthresmin):

    #     edge_type = "falling"
    # Storing the falling edge e_i = (time_i, mag_i)
    #     row = {"index": i, "time": time, "magnitude": curr_nextwin_diff}
    #     return edge_type, row
    # return "Not an edge", {}

    # Testing #
    if (prev_curr_diff < pthresmin and curr_nextwin_diff >= pthresmin and
            curr_next_diff > prev_curr_diff and curr_next_diff > 0):

        # logger.debug("\nR1::", i, "currtime", dt.datetime.fromtimestamp(time),)
        # logger.debug("prev ", prev, "curr ", curr, "next ", next,)
        # logger.debug("currwin", currwin)
        # logger.debug("prev_curr_diff", prev_curr_diff, "prevwintime",
            # dt.datetime.fromtimestamp(prevwintime))
        # logger.debug("curr_next_diff ", curr_next_diff,)
        # logger.debug("curr_nextwin_diff", curr_nextwin_diff, "curr_prevwin_diff")
        # curr_prevwin_diff

        edge_type = "rising"
        if (curr_next_diff >= per_pthresmin):
            # Storing the rising edge e_i = (time_i, mag_i)
            row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
            return edge_type, row
        if next_missing_sample and curr_next_diff > pthresmin:
            logger.debug("Missing Sample:: Index %s", i)
            # Storing the rising edge e_i = (time_i, mag_i)
            row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
            return edge_type, row
        elif (curr_next_diff > per_pthresmin):
            logger.debug("Here1 Index:: %s", i)
            # Storing the rising edge e_i = (time_i, mag_i)
            row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
            return edge_type, row
        else:
            logger.debug("Here2 Index:: %s", i)
            pass
    elif (prev_curr_diff < pthresmin and curr_nextwin_diff > pthresmin
          and curr_next_diff >= per_pthresmin and curr_next_diff > 0):
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

    elif (prev_curr_diff < pthresmin and math.floor(curr_nextwin_diff) <= (-pthresmin)
          and curr_next_diff > prev_curr_diff
          and curr_prevwin_diff > -pthresmin):

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
        elif curr_next_diff < pthresmin or curr_next_diff > pthresmin:
            logger.debug("Falling Edge2:: Index %s", i)
            # Storing the falling edge e_i = (time_i, mag_i)
            row = {"index": i, "time": time, "magnitude": curr_nextwin_diff, "curr_power": curr}
            return edge_type, row
        else:
            pass
    return "Not an edge", {}


def filter_edges(rise_df, fall_df, winmin, thres):

    # Removing duplicate indexes
    rise_df["index"] = rise_df.index
    rise_df.drop_duplicates(cols='index', take_last=True, inplace=True)
    del rise_df["index"]

    fall_df["index"] = fall_df.index
    fall_df.drop_duplicates(cols='index', take_last=True, inplace=True)
    del fall_df["index"]

    # FILTER 1:
    # Handle cases where 2 rising edges corresponding to a single
    # falling edge - combining them to one edge

    for ix_i in rise_df.index:
        sim_edge_set = []
        for ix_j in rise_df.index:
            curr_prev_diff = math.fabs(rise_df.ix[ix_j]['time'] -
                                       rise_df.ix[ix_i]['time'])
            if ix_i == ix_j or ix_i > ix_j:
                continue
            elif curr_prev_diff in range(winmin, winmin + 2 + 1):
                logger.debug("Index i: %d", ix_i)
                logger.debug("Index j: %d", ix_j)
                sim_edge_set.append(ix_j)
        # Add the magnitude of the two edges and convert into a single
        # edge
        if len(sim_edge_set) > 0:
            tmp = rise_df.ix[sim_edge_set]
            sel_idx = tmp[tmp.magnitude == tmp.magnitude.max()].index[0]
            new_mag = (rise_df.ix[ix_i]['magnitude'] +
                       rise_df.ix[sel_idx]['magnitude'])
            rise_df.ix[ix_i]['magnitude'] = new_mag
            logger.debug("Inside Index j: %s New Mag: %s ", sel_idx, new_mag)
            logger.debug("Rise time:: %s Rise Time (2): %s",
                         dt.datetime.fromtimestamp(rise_df.ix[ix_i]['time']),
                         dt.datetime.fromtimestamp(rise_df.ix[sel_idx]['time']))
            # Remove the second edge
            rise_df.drop(sel_idx)

    # FILTER 2:
    # Filter out spike edges where rising and falling edges
    # are within a small time frame (lwinmin)
    # This is to remove quick successive turn ON and OFFs

    tmp = pd.concat([rise_df, fall_df])
    tmp = tmp.sort('time')
    tmp['ts'] = (tmp.time / 100).astype('int')
    # logger.debug("\nConcatenated TMPDF::\n %s", tmp)
    for i, ix_i in enumerate(tmp.index):
        for j, ix_j in enumerate(tmp.index):
            if(ix_i == ix_j) or ix_i > ix_j:
                continue
            elif (tmp.ix[ix_i]['ts'] == tmp.ix[ix_j]['ts'] and
                  tmp.ix[ix_i]['magnitude'] > tmp.ix[ix_j]['magnitude'] and
                  tmp.ix[ix_j]['magnitude'] == -tmp.ix[ix_i]['magnitude']):
                logger.debug("Index i:: %s", ix_i)
                logger.debug("Removing %s %s", ix_i, ix_j)
                if ix_i in rise_df.index:
                    rise_df = rise_df.drop(ix_i)
                fall_df = fall_df.drop(ix_j)

    # for ix_i in rise_df.index:
    #     curr = df_l.ix[ix_i]['lightpower']
    #     currnext = df_l.ix[ix_i + 1]['lightpower']
    #     currnext_next = df_l.ix[ix_i + 2]['lightpower']
    #     curr_next_diff = int(currnext - curr)
    #     succ_fall_mag = math.ceil(int(currnext_next - currnext))
    #     logger.debug("Index:", ix_i, "Succ Fall Mag", \
        # succ_fall_mag, "CurrNextDiff", curr_next_diff)
    # if ix_i ==
    #     if (succ_fall_mag >= lthresmin and
    #        (succ_fall_mag - curr_next_diff) in np.arange(0, 2, 0.1)):
    #         logger.debug("Index:", ix_i, "Succ Fall Mag", succ_fall_mag,)
    #         logger.debug("CurrNextDiff", curr_next_diff)
    #         rise_df.drop(ix_i)
    #         logger.debug("Inside Succ Fall Mag", succ_fall_mag, "Index", i)

    # FILTER 3:
    # Select the edge amongst a group of edges within a small time frame (a minute)
    # and which are close to each other in terms of magnitude
    # with maximum timestamp

    # Rising Edges
    tmp_df = rise_df.copy()
    # tmp_df['ts'] = (rise_df.time / 100).astype('int')
    tmp_df['tmin'] = [str(dt.datetime.fromtimestamp(i).hour) + '-' +
                      str(dt.datetime.fromtimestamp(i).minute) for i in tmp_df.time]
    # print "Grouped Max", tmp_df.groupby('tmin')['magnitude'].max()
    # ts_grouped = tmp_df.groupby('tmin').max()
    # tmp_df = pd.concat([tmp_df[(tmp_df.tmin == i) &
    #                   (tmp_df.magnitude == ts_grouped.ix[i]['magnitude'])]
    #     for i in ts_grouped.index])
    # ts_grouped = tmp_df.groupby('tmin')['time'].max()
    # tmp_df = tmp_df[tmp_df.time.isin(ts_grouped)].sort(['time'])

    # Select the edge with the maximum timestamp lying within a minute
    idx_list = []
    for i, idx in enumerate(tmp_df.index):

        if idx == tmp_df.index[-1]:
            if idx not in idx_list:
                idx_list.append(idx)
            break
        t = tmp_df.ix[idx]['time']
        t_next = tmp_df.ix[tmp_df.index[i + 1]]['time']
        diff = t_next - t
        if diff <= 60:
            t_mag = tmp_df.ix[idx]['magnitude']
            t_next_mag = tmp_df.ix[tmp_df.index[i + 1]]['magnitude']
            t_curr_power = math.fabs(tmp_df.ix[idx]['curr_power'])
            t_next_curr_power = math.fabs(tmp_df.ix[tmp_df.index[i + 1]]['curr_power'])

            curr_diff = math.fabs(t_next_curr_power - t_curr_power)

            if curr_diff < 0.5 * thres:
                if t_mag <= 60:
                    threshold = 0.2
                elif t_mag >= 1000:
                    print "in"
                    threshold = 0.25
                else:
                    threshold = 0.1
                if math.fabs(t_mag - t_next_mag) <= threshold * t_mag:
                    idx_list.append(tmp_df.index[i + 1])
                    if idx in idx_list:
                        idx_list.remove(idx)
                else:
                    if idx not in idx_list:
                        idx_list.append(idx)
            else:
                if idx not in idx_list:
                    idx_list.append(idx)
        else:
            if idx not in idx_list:
                idx_list.append(idx)
    print "Rise idx_list", idx_list
    tmp_df = tmp_df.ix[idx_list].sort(['time'])
    rise_df = tmp_df.ix[:, :-1]

    # Falling Edges
    tmp_df = fall_df.copy()
    # tmp_df['ts'] = (fall_df.time / 100).astype('int')
    tmp_df['tmin'] = [str(dt.datetime.fromtimestamp(i).hour) + '-' +
                      str(dt.datetime.fromtimestamp(i).minute) for i in tmp_df.time]

    # Select the edge with the maximum timestamp lying within a minute
    idx_list = []
    for i, idx in enumerate(tmp_df.index):
        # if idx in idx_list:
        #     continue
        if idx == tmp_df.index[-1]:
            if idx not in idx_list:
                idx_list.append(idx)
            break
        t = tmp_df.ix[idx]['time']
        t_next = tmp_df.ix[tmp_df.index[i + 1]]['time']
        diff = t_next - t
        if diff <= 60:
            t_mag = math.fabs(tmp_df.ix[idx]['magnitude'])
            t_next_mag = math.fabs(tmp_df.ix[tmp_df.index[i + 1]]['magnitude'])
            t_curr_power = math.fabs(tmp_df.ix[idx]['curr_power'])
            t_next_curr_power = math.fabs(tmp_df.ix[tmp_df.index[i + 1]]['curr_power'])

            curr_diff = math.fabs(t_next_curr_power - t_curr_power)

            # print "\n idx ", idx, "now time", dt.datetime.fromtimestamp(t),
            # print "next time", dt.datetime.fromtimestamp(t_next)
            # print "t_mag", t_mag, "t_next_mag", t_next_mag
            # print "t_curr_power", t_curr_power, "t_next_curr_power", t_next_curr_power
            # print "curr_diff", curr_diff
            if curr_diff == 0:
                idx_list.append(tmp_df.index[i + 1])
                if idx in idx_list:
                    idx_list.remove(idx)
                # print "idx in", idx, "next idx", tmp_df.index[i + 1], idx_list
            elif curr_diff < 0.5 * thres:
                if t_mag <= 60:
                    threshold = 0.2
                elif t_mag >= 1000:
                    print "in"
                    threshold = 0.25
                else:
                    threshold = 0.1
                if math.fabs(t_mag - t_next_mag) <= threshold * t_mag:
                    idx_list.append(tmp_df.index[i + 1])
                    if idx in idx_list:
                        idx_list.remove(idx)
                    # print "idx in", idx, "next idx", tmp_df.index[i + 1], idx_list
                else:
                    # print "idx out", idx
                    if idx not in idx_list:
                        idx_list.append(idx)
            else:
                if idx not in idx_list:
                    idx_list.append(idx)

        else:
            if idx not in idx_list:
                idx_list.append(idx)
    print "\nFall idx_list", idx_list
    tmp_df = tmp_df.ix[idx_list].sort(['time'])

    # tmp_df = pd.concat([tmp_df[(tmp_df.tmin == i) &
    #                   (tmp_df.magnitude == ts_grouped.ix[i]['magnitude'])]
    #     for i in ts_grouped.index])
    # ts_grouped = tmp_df.groupby('tmin')['time'].max()
    # tmp_df = tmp_df[tmp_df.time.isin(ts_grouped)].sort(['time'])
    fall_df = tmp_df.ix[:, :-1]

    return rise_df, fall_df


def filter_apt_edges(rise_df, fall_df, apt_no, etype, df_p):

    # Removing duplicate indexes
    rise_df["index"] = rise_df.index
    rise_df.drop_duplicates(cols='index', take_last=True, inplace=True)
    del rise_df["index"]

    fall_df["index"] = fall_df.index
    fall_df.drop_duplicates(cols='index', take_last=True, inplace=True)
    del fall_df["index"]

    # For power edges
    if etype == 'power':

        # Filter 1
        # Filtering out edges with magnitude between 130 to 150
        # Rising Edges
        idx_list = []
        for i in rise_df.index:
            magnitude = rise_df.ix[i]['magnitude']
            time = rise_df.ix[i]['time']
            if apt_no == '603':
                # Likely power consumption of fridge is 110-150
                if magnitude >= 110 and magnitude <= 150:
                    print "idx", i, "magnitude", magnitude
                    idx_list.append(i)
            elif apt_no == '703':
                if magnitude >= 130 and magnitude <= 190:
                    idx_list.append(i)
                # 26-27Nov
                # if time in range(1385470967, 1385471880):
                #     idx_list.append(i)
        rise_df = rise_df.ix[rise_df.index - idx_list]

        # Falling Edges
        idx_list = []
        for i in fall_df.index:
            magnitude = math.fabs(fall_df.ix[i]['magnitude'])
            time = math.fabs(fall_df.ix[i]['time'])
            if apt_no == '603':
                # Likely power consumption of fridge is 110-150
                if magnitude >= 110 and magnitude <= 150:
                    print "idx", i, "magnitude", magnitude
                    idx_list.append(i)
            elif apt_no == '703':
                if magnitude >= 130 and magnitude <= 170:
                    idx_list.append(i)
                # 26-27Nov
                # if time in range(1385470967, 1385471880):
                #     idx_list.append(i)
                # 28-29Nov
                if time in range(1385646060, 1385648144):
                    idx_list.append(i)
        fall_df = fall_df.ix[fall_df.index - idx_list]

        # Filter 2 - removing RO edges
        print "\nFiltering process started.....\n"
        edge_total_list = pd.concat([rise_df, fall_df])
        edge_total_list = edge_total_list.sort(['time'])
        edge_index = edge_total_list.index
        # List containing indexes to remove
        rise_idx_list = []
        fall_idx_list = []
        for i, idx in enumerate(edge_total_list.index):
            now_edge = edge_total_list.ix[idx]['time']
            now_mag = edge_total_list.ix[idx]['magnitude']
            if i + 1 not in range(0, len(edge_index)):
                # Reached the end
                if now_mag < 0 and int(math.fabs(now_mag)) in range(60, 75):
                    # If diff power between curr and prev power last 20 seconds
                    # is similar to the fall mag then select edge
                    curr_power = edge_total_list.ix[idx]['curr_power']
                    for j in range(20, 26):
                        # Find prev power
                        prev_time = now_edge - j
                        row_df = df_p[df_p.time == prev_time]
                        if len(row_df) > 0:
                            prev_sec_power = row_df.ix[row_df.index[0]]['power']
                            diff_power = int(curr_power - prev_sec_power)
                            if now_mag in range(int(diff_power) - 2, int(diff_power) + 3):
                                fall_idx_list.append(idx)
                continue

            next_edge = edge_total_list.ix[edge_index[i + 1]]['time']
            next_mag = edge_total_list.ix[edge_index[i + 1]]['magnitude']
            diff = int(math.fabs(next_edge)) - int(now_edge)

            if ((now_edge < 0 and int(math.fabs(now_mag)) in range(60, 75))
               or now_edge == 1385383788 or next_mag == 1385383788):
                print "\nNow time", dt.datetime.fromtimestamp(now_edge)
                print "Next time", dt.datetime.fromtimestamp(next_edge)
                print "Now mag", now_mag, "next mag", next_mag
                print "Diff", diff

            # Its a falling edge and magnitude is b/w 60 - 70 and previous edge was a rising edge
            if (next_mag < 0 and int(math.fabs(next_mag)) in range(60, 75)
               and now_edge > 0 and diff in range(20, 30)
               and int(now_mag * 0.1) == int(math.fabs(next_mag) * 0.1)):
                # Removing both edges
                rise_idx_list.append(idx)
                fall_idx_list.append(edge_index[i + 1])
            # If rising edge was not detected
            elif now_mag < 0 and int(math.fabs(now_mag)) in range(60, 75):
                print "\nNow time", dt.datetime.fromtimestamp(now_edge)
                print "Next time", dt.datetime.fromtimestamp(next_edge)
                print "Now mag", now_mag, "next mag", next_mag
                print "Diff", diff

                # If diff power between curr and prev power last 20 seconds
                # is similar to the fall mag then select edge
                curr_power = edge_total_list.ix[idx]['curr_power']
                for j in range(20, 30):
                    # Find prev power
                    prev_time = now_edge - j
                    row_df = df_p[df_p.time == prev_time]

                    if len(row_df) > 0:

                        prev_sec_power = row_df.ix[row_df.index[0]]['power']
                        diff_power = int(curr_power - prev_sec_power)
                        if (int(math.fabs(now_mag)) in range(diff_power - 2, diff_power + 3)):
                            print "j=", j
                            print "curr_power", curr_power
                            print "prev_time", prev_time
                            print "row", row_df
                            print "prev_sec_power", prev_sec_power, 'diff_power', diff_power
                            fall_idx_list.append(idx)
        rise_idx_list = list(set(rise_idx_list))
        fall_idx_list = list(set(fall_idx_list))
        # Removing selected edges
        rise_df = rise_df.ix[rise_df.index - rise_idx_list]
        fall_df = fall_df.ix[fall_df.index - fall_idx_list]

    return rise_df, fall_df


def generate_light_edges(df_l):

    # ----------------------------------------------
    # LIGHT EDGE DETECTION
    # ----------------------------------------------
    # Find the edges in the light meter (LP Power phase) since activity and
    # its duration is well explained/defined by the usage of lights and
    # fans.

    ix_list_l = df_l.index
    r_row_list = []
    f_row_list = []

    print "-" * stars
    print "Detecting Edges in Light Meter"
    print "-" * stars

    for i in range(1, ix_list_l[-1] - lwinmin + 1):
        edge_type, result = check_if_light_edge(df_l, i, "lightpower")
        # print "EType", edge_type
        # print "Res", result
        if edge_type == "falling":
            f_row_list.append(result)
        elif edge_type == "rising":
            r_row_list.append(result)
        else:
            pass

    # print "Rising Row List", r_row_list
    # print "Falling Row List", f_row_list

    rising_edges_l_df = pd.DataFrame()
    if len(r_row_list) < 1:
        rising_edges_l_df = pd.DataFrame(columns=['index', 'time', 'magnitude', 'curr_power'])
    else:
        rising_edges_l_df = pd.DataFrame(
            r_row_list, columns=['index', 'time', 'magnitude', 'curr_power'])
    rising_edges_l_df = rising_edges_l_df.set_index('index', drop=True)

    falling_edges_l_df = pd.DataFrame()
    if len(f_row_list) < 1:
        falling_edges_l_df = pd.DataFrame(columns=['index', 'time', 'magnitude', 'curr_power'])
    else:
        falling_edges_l_df = pd.DataFrame(
            f_row_list, columns=['index', 'time', 'magnitude', 'curr_power'])
    falling_edges_l_df = falling_edges_l_df.set_index('index', drop=True)

    # Adding the actual times to the frame
    rising_edges_l_df['act_time'] = [
        dt.datetime.fromtimestamp(int(t)) for t in rising_edges_l_df.time]
    falling_edges_l_df['act_time'] = [
        dt.datetime.fromtimestamp(int(t)) for t in falling_edges_l_df.time]

    print "Rising Edges::\n", rising_edges_l_df
    print "Falling edges::\n", falling_edges_l_df

    rising_edges_l_df, falling_edges_l_df = filter_edges(
        rising_edges_l_df, falling_edges_l_df, lwinmin, lthresmin)

    # Print the edges with the timestamps values converted to UTC +5.30
    # format
    # Rising Edges
    print_lr_df = rising_edges_l_df.copy()
    t = pd.to_datetime(print_lr_df['time'], unit='s')
    index = pd.DatetimeIndex(t, tz='UTC').tz_convert(TIMEZONE)
    print_lr_df.set_index(index, inplace=True, drop=False)

    # Falling Edges
    print_lf_df = falling_edges_l_df.copy()
    t = pd.to_datetime(print_lf_df['time'], unit='s')
    index = pd.DatetimeIndex(t.tolist(), tz='UTC').tz_convert(TIMEZONE)
    print_lf_df.set_index(index, inplace=True, drop=False)

    print "-" * stars
    print "Filtered Edges:"
    print "-" * stars
    print "Rising Edges::\n", print_lr_df
    print "Falling edges::\n", print_lf_df

    return rising_edges_l_df, falling_edges_l_df


def generate_power_edges(df_p):

    # ----------------------------------------------
    # POWER EDGE DETECTION
    # ----------------------------------------------
    # Find the edges in the power meter (Power phase) for detecting
    # an power event

    ix_list_p = df_p.index
    r_row_list = []
    f_row_list = []
    print "-" * stars
    print "Detecting Edges in Power Meter"
    print "-" * stars
    for i in range(1, ix_list_p[-1] - pwinmin + 1):
        edge_type, result = check_if_power_edge(df_p, i, "power")
        if edge_type == "falling":
            f_row_list.append(result)
        elif edge_type == "rising":
            r_row_list.append(result)
        else:
            pass

    rising_edges_p_df = pd.DataFrame(
        r_row_list, columns=['index', 'time', 'magnitude', 'curr_power'])
    rising_edges_p_df = rising_edges_p_df.set_index('index', drop=True)

    falling_edges_p_df = pd.DataFrame(
        f_row_list, columns=['index', 'time', 'magnitude', 'curr_power'])
    falling_edges_p_df = falling_edges_p_df.set_index('index', drop=True)

    # Adding the actual times to the frame
    rising_edges_p_df['act_time'] = [
        dt.datetime.fromtimestamp(int(t)) for t in rising_edges_p_df.time]
    falling_edges_p_df['act_time'] = [
        dt.datetime.fromtimestamp(int(t)) for t in falling_edges_p_df.time]

    print "Rising Edges::\n", rising_edges_p_df
    print "Falling Edges::\n", falling_edges_p_df

    rising_edges_p_df, falling_edges_p_df = filter_edges(
        rising_edges_p_df, falling_edges_p_df, pwinmin, pthresmin)

    # Print the edges with the timestamps values converted to UTC +5.30
    # format

    # Rising Edges
    print_pr_df = rising_edges_p_df.copy()
    t = pd.to_datetime(
        rising_edges_p_df['time'], unit='s')
    index = pd.DatetimeIndex(t.tolist(), tz='UTC').tz_convert(TIMEZONE)
    print_pr_df.set_index(index, inplace=True, drop=False)

    # Falling Edges
    print_pf_df = falling_edges_p_df.copy()
    t = pd.to_datetime(
        falling_edges_p_df['time'], unit='s')
    index = pd.DatetimeIndex(t.tolist(), tz='UTC').tz_convert(TIMEZONE)
    print_pf_df.set_index(index, inplace=True, drop=False)

    print "-" * stars
    print "Filtered Edges:"
    print "-" * stars
    print "Rising Edges::\n", print_pr_df
    print "Falling Edges::\n", print_pf_df

    return rising_edges_p_df, falling_edges_p_df
