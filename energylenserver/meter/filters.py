"""
Contains all the filters required for the meter data
"""

import math
import datetime as dt

from energylenserver.common_imports import *


def remove_duplicate_edges(df):
    df["index"] = df.index
    df.drop_duplicates(cols='index', take_last=True, inplace=True)
    del df["index"]

    return df


def filter_select_maxtime_edge(df):

    # Select the edge amongst a group of edges within a small time frame (a minute)
    # and which are close to each other in terms of magnitude
    # with maximum timestamp

    # Rising Edges
    tmp_df = df.copy()
    # tmp_df['ts'] = (df.time / 100).astype('int')
    tmp_df['tmin'] = [str(dt.datetime.fromtimestamp(i).hour) + '-' +
                      str(dt.datetime.fromtimestamp(i).minute) for i in tmp_df.time]

    # Select the edge with the maximum timestamp lying within a minute
    idx_list = []
    for i, idx in enumerate(tmp_df.index):

        if idx == tmp_df.index[-1]:
            if idx not in idx_list:
                idx_list.append(idx)
            break
        next_idx = tmp_df.index[i + 1]
        t = tmp_df.ix[idx]['time']
        t_next = tmp_df.ix[next_idx]['time']
        diff = t_next - t
        if diff <= 60:
            t_mag = math.fabs(tmp_df.ix[idx]['magnitude'])
            t_next_mag = math.fabs(tmp_df.ix[next_idx]['magnitude'])

            t_curr_power = math.fabs(tmp_df.ix[idx]['curr_power'])
            t_next_curr_power = math.fabs(tmp_df.ix[next_idx]['curr_power'])

            curr_diff = math.fabs(t_next_curr_power - t_curr_power)

            if curr_diff == 0:
                idx_list.append(next_idx)
                if idx in idx_list:
                    idx_list.remove(idx)
            elif curr_diff < 0.5 * thresmin:
                if t_mag <= 60:
                    threshold = 0.2
                elif t_mag >= 1000:
                    print "in"
                    threshold = 0.25
                else:
                    threshold = 0.1

                threshold_mag = threshold * t_mag
                # print "Threshold:", threshold
                # print "ThresholdMag:", threshold_mag

                if math.fabs(t_mag - t_next_mag) <= threshold_mag:
                    idx_list.append(next_idx)
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
    # print "Edge idx_list", idx_list
    tmp_df = tmp_df.ix[idx_list].sort(['time'])
    df = tmp_df.ix[:, :-1]

    return df

def filter_unmon_appl_edges(df):
    """
    Filters out appliances that are not of interest
    e.g. washing machine, fridge and geyser
    """
    # --Filter out fridge--

    # --Filter out washing machine
    pass

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


def filter_edges(rise_df, fall_df, winmin):

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

    return rise_df, fall_df


def filter_time_slices(time_slices, apt_no, exp_no):
    """
    Remove fridge events and events where the duration is less than 30 seconds
    """
    # Removing the extraneous time slices

    if apt_no == '102A':
        # Likely power consumption of fridge is 110 - 180
        fridge_ts = time_slices[(time_slices.magnitude >= 110) & (time_slices.magnitude <= 180) &
                                (time_slices.type == 'power')]
        print fridge_ts
        time_slices = time_slices.ix[time_slices.index - fridge_ts.index]

        # Old Experiment No. 3 for ELens13 experiments
        if exp_no == 'elens3':
            discard_ts = time_slices[
                (time_slices.phase == 'Not Found') & (time_slices.magnitude < 100)]
            time_slices = time_slices.ix[time_slices.index - discard_ts.index]

    elif apt_no == '603':
        print "here"
        # Likely power consumption of fridge is 110-150
        time_slices = time_slices[(time_slices.magnitude < 110) | (time_slices.magnitude > 150) &
                                  (time_slices.type == 'power')]
        # 25-26Nov
        if exp_no == '25-26Nov':
            time_slices = time_slices[time_slices.end_time < 1385404505]
        elif exp_no == '26-27Nov':
            time_slices = time_slices[time_slices.end_time < 1385492334]

    elif apt_no == '703':
        # Likely power consumption of fridge is 130-152
        fridge_ts = time_slices[(time_slices.magnitude >= 130) & (time_slices.magnitude <= 170) &
                                (time_slices.type == 'power')]
        time_slices = time_slices.ix[time_slices.index - fridge_ts.index]

        # Likely power consumption of geyser > 2000 but on light phase > 1000
        geyser_ts = time_slices[(time_slices.magnitude > 1000) & (time_slices.type == 'light')]
        time_slices = time_slices.ix[time_slices.index - geyser_ts.index]

        # 26-27Nov
        if exp_no == '26-27Nov':
            washing_ts = time_slices[
                (time_slices.start_time >= 1385470967) & (time_slices.end_time <= 1385471880)]
            time_slices = time_slices.ix[time_slices.index - washing_ts.index]

        # 28-29Nov
        if exp_no == '28-29Nov':
            time_slices = time_slices[
                (time_slices.start_time < 1385646060) | (time_slices.end_time > 1385648143)]

    # Removing time slices with duration less than 30 seconds
    idx_list = []
    for idx in time_slices.index:
        start_time = time_slices.ix[idx]['start_time']
        end_time = time_slices.ix[idx]['end_time']
        magnitude = time_slices.ix[idx]['magnitude']

        time_diff = end_time - start_time

        if time_diff < 30 and magnitude < 80:
            print "idx", idx, "time_diff", time_diff, "magnitude", magnitude
            # Qualified for filtering it
            idx_list.append(idx)
    time_slices = time_slices.ix[time_slices.index - idx_list]

    return time_slices
