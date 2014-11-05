"""
Edge Matching
Taking time-correlated rising and falling edges, goal is to
match each rising and falling edge to determine the usage time.
Use the Wifi data and meter data, to find the location of
the activity and also act as a filter to distinguish between edges
with similar magnitude (coming from similar fixtures).
The phase of the power event will give the
coarse level location. Combining it with Wifi will give
the user's activity location.

Input: Time-correlated edges with user activity
Output: Time slices of interest <T_i, T_j, ...>
    T_i = (s_i, e_i)
    where,
        s_i = start time of activity
        e_i = end time of activity

"""

from energylenserver.common_imports import *

# Enable Logging
logger = logging.getLogger('energylensplus_meterdata')


def make_pairs(rise_fall_dict, rise_df, fall_df, edge_type, app):

    row_df_list = []
    new_rel_idx = rise_fall_dict

    for fall_idx, rise_idx_list in new_rel_idx.items():
        # Processing for falling edges where rising edges exist
        if len(rise_idx_list) > 0:

            logger.debug(
                "Fall_index: %s Rise index: %s", fall_idx, rise_idx_list)
            logger.debug("-" * stars)

            # Falling edge
            f_time = int(fall_df.ix[fall_idx]['time'])
            f_mag = (-1) * fall_df.ix[fall_idx]['magnitude']
            f_phase = fall_df.ix[fall_idx]['phase']
            logger.debug("Fall_time %s", dt.datetime.fromtimestamp(f_time))

            phase_mag_min_diff = (rise_idx_list[0], math.fabs(
                f_mag - rise_df.ix[rise_idx_list[0]]['magnitude']),
                rise_df.ix[rise_idx_list[0]]['phase'])
            print "First min", phase_mag_min_diff
            for rid in rise_idx_list:
                if rid != 0:
                    r_mag = int(rise_df.ix[rid]['magnitude'])
                    diff = math.fabs(f_mag - r_mag)
                    r_phase = rise_df.ix[rid]['phase']
                    if app in [4, 5]:
                        if phase_mag_min_diff[1] > diff and f_phase == r_phase:
                            phase_mag_min_diff = (rid, diff, r_phase)
                            print "New min", phase_mag_min_diff
                    else:
                        if phase_mag_min_diff[1] > diff:
                            phase_mag_min_diff = (rid, diff, r_phase)
                            print "New min", phase_mag_min_diff
            # Taking the rising edge which is the closest to the fall magnitude
            r_index = phase_mag_min_diff[0]
            r_time = int(rise_df.ix[r_index]['time'])
            logger.debug("Rise Index:: %s", r_index)
            logger.debug("Rise Time: %s", dt.datetime.fromtimestamp(r_time))

            # Creating edge pair entry
            row_df = pd.DataFrame(
                {"start_time": rise_df.ix[r_index]['time'],
                 "end_time": f_time,
                 "magnitude": f_mag,
                 "type": edge_type, "phase": f_phase},
                index=[0])
            logger.debug("Testdf: \n%s", row_df)
            row_df_list.append(row_df)

            # Filter 4: Removing this rising edge which has been associated with
            # a falling edge
            for fid, rise_idx_list in new_rel_idx.items():

                if r_index in rise_idx_list and fid != fall_idx:
                    # logger.debug("Fall_index: %d Rise index:%s",
                                 # fall_index, rise_indx_list)
                    rise_idx_list.remove(r_index)
            logger.debug("New Rising Edge List::\n%s", new_rel_idx)
            logger.debug("-" * stars)

    return row_df_list


def edge_matching(df_l, df_p, edge_list, app):

    # Output
    time_slices = pd.DataFrame(
        columns=['start_time', 'end_time', 'magnitude', 'type'])

    # TODO: Filter out voltage fluctuations seen across multiple phases

    # Find the time slices (start and end time of activity) by matching
    # based on magnitude of the edges

    # for rising and its corresponding falling edge
    # l_power = 5
    # p_power = 100

    rise_l_df = edge_list[0].reset_index(drop=True)
    fall_l_df = edge_list[1].reset_index(drop=True)
    rise_p_df = edge_list[2].reset_index(drop=True)
    fall_p_df = edge_list[3].reset_index(drop=True)

    print "-" * stars
    print "Edge Matching Process"
    print "-" * stars

    # For every falling edge, find the matching rising edge
    full_df_list = []
    for k in [0, 1]:
        if k == 0:
            rise_df = rise_l_df
            fall_df = fall_l_df
            # power = l_power
            edge_type = "light"
            logger.debug("Matching for light edges......")
            logger.debug("-" * stars)
        else:
            rise_df = rise_p_df
            fall_df = fall_p_df
            # power = p_power
            edge_type = "power"
            logger.debug("Matching for power edges......")
            logger.debug("-" * stars)

        # Filter 1: Filter falling edges where it is before any rising edge
        # cols = ['time', 'time_sec', 't_meter','magnitude', 'label', 'pred_label']
        re_l_idx = [np.where(rise_df.time < i)[0] for i in fall_df.time]
        logger.debug("Filter 1 results: %s", re_l_idx)

        # Filter 2: Match falling with rising edges where its magnitude between
        # a power threshold window

        # This dict contains the falling edge index as the key and the corresponding
        # rising edges as list items
        new_rel_idx = defaultdict(list)
        for i, row in enumerate(re_l_idx):
            no_ele = len(row)
            re_l = []
            if no_ele > 0:
                fall_mag = math.fabs(fall_df.ix[i]['magnitude'])
                fall_phase = fall_df.ix[i]['phase']
                # Set power threshold for magnitude comparison between
                # rising and falling
                power = fall_mag * percent_change
                logger.debug("Idx %d %s fall_mag=%s %s fall phase:%s", i,
                             fall_mag - power, fall_mag, fall_mag + power, fall_phase)
                # For debugging - printing the rising edges corres. to falling
                # edges
                restr = ''
                for idx in row:
                    restr += ' ' + str(rise_df.ix[idx]['magnitude'])
                logger.debug("Rising edges::%s", restr)
                # Generating matching rising edge list for the falling edge i
                if app in [4, 5]:
                    logger.debug("Using Phase for time slice generation")
                    re_l = [idx for idx in row if rise_df.ix[idx]['magnitude'] >= fall_mag - power
                            and rise_df.ix[idx]['magnitude'] <= fall_mag + power and
                            rise_df.ix[idx]['phase'] == fall_phase]
                else:
                    re_l = [idx for idx in row if rise_df.ix[idx]['magnitude'] >= fall_mag - power
                            and rise_df.ix[idx]['magnitude'] <= fall_mag + power]
                logger.debug("Matched Rising Edges with fidx %d: %s", i, re_l)
            new_rel_idx[i] = re_l
        logger.debug("Filter 2 results: %s", new_rel_idx.items())

        row_df_list = make_pairs(new_rel_idx, rise_df, fall_df, edge_type, app)
        full_df_list = full_df_list + row_df_list

    # logger.debug("\nMatched Edges: \n%s", full_df_list)
    if len(full_df_list) == 0:
        print "No time slices found!"
        return time_slices
    elif len(full_df_list) == 1:
        time_slices = full_df_list[0]
    else:
        time_slices = pd.concat(full_df_list)

    time_slices = time_slices.reset_index(drop=True)
    # print "Time slices::", time_slices

    # Printing Format
    print_ts_df = time_slices.copy()

    print_ts_df['act_start_time'] = [dt.datetime.fromtimestamp(i)
                                     for i in time_slices['start_time']]
    print_ts_df['act_end_time'] = [dt.datetime.fromtimestamp(i)
                                   for i in time_slices['end_time']]
    print_ts_df = print_ts_df.sort(['start_time'])
    print "\nGenerated Time Slices::\n", print_ts_df
    return time_slices
