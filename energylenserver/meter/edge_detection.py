"""
Find the edges from the raw power data

Author: Manaswi Saha
Date: 21th August 2014
"""

import pandas as pd
import math
import datetime as dt

from energylenserver.common_imports import *

# Global variables
stars = 30


"""
TODO:
1. Measure the difference between the time between phone and meter
2. Make a common function for edge detection instead of light and power edges
separately
"""


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

    """
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
    """

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

    """
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
    """

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


def check_if_edge(df_l, index, power_stream):
    pass


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
