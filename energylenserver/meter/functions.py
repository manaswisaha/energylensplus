import time
import pandas as pd
import numpy as np
import datetime as dt

from smap import get_meter_data_for_time_slice
from edge_detection import *
from constants import *
from energylenserver.functions import *

# Enable Logging
import logging
logger = logging.getLogger('energylensplus_django')


# Global variables
date_format = "%Y-%m-%dT%H:%M:%S"


def compute_power(start_mag, end_mag):
    return int(round((start_mag + end_mag) / 2))


def training_compute_power(apt_no, start_time, end_time):
    """
    Computes the power consumption in the given time interval
    """

    logger.debug("Computing power for training data...")
    power = np.random.randn()

    # ------
    # Retrieve data from the server
    # ------
    start_time = int(start_time) / 1000
    end_time = int(end_time) / 1000

    logger.debug("Orig:: ST: %s ET:%s", timestamp_to_str(
        start_time, date_format), timestamp_to_str(end_time, date_format))

    # '''
    # --- Negligible time difference ---
    # Measure the difference between time of the phone with the meter data
    # Once measured, set the global variable in the constants
    # If phone is ahead, subtract from the time sent
    # If phone is behind, add to the time sent

    if apt_no != 1201:
        # 102A
        time_diff = -9
    else:
        time_diff = 0

    # Convert time to seconds and add/subtract the difference time
    start_time = start_time + time_diff
    end_time = end_time + time_diff
    logger.debug("New:: ST: %s ET:%s", timestamp_to_str(
        start_time, date_format), timestamp_to_str(end_time, date_format))
    # '''

    # Adding 5 to fetch extra to account for missing values??
    edge_window = winmax * sampling_rate + 5

    # Add a window to the given event time duration
    s_time = start_time - edge_window
    s_time = timestamp_to_str(s_time, date_format)

    e_time = end_time + edge_window
    e_time = timestamp_to_str(e_time, date_format)

    # Retrieve power data from smap server for both meters
    # between <start_time> and <end_time>
    # if apt_no == 1201:
    time.sleep(winmax * 2)
    if apt_no in [102, '102A']:
        apt_no = '102A'
    streams_df_list = get_meter_data_for_time_slice(apt_no, s_time, e_time)

    if len(streams_df_list) == 0:
        # Sufficient training data not present
        power = 0
        logger.debug("Insufficient training data!")
        return power

    '''
    # Temp Code -- START
    meter_df = streams_df_list[0]
    logger.debug("Meter ST: %s", timestamp_to_str(meter_df.ix[0]['time'], date_format))
    logger.debug("Meter ET: %s", timestamp_to_str(
        meter_df.ix[meter_df.index[-1]]['time'], date_format))
    # Temp Code -- END
    '''

    # Contains start and end edges list from both meters
    edge_list = []

    # -------
    # Detect start/end edges for both meters
    # -------
    for i, edge_time in enumerate([start_time, end_time]):

        # Temp code -- START
        '''
        if i == 0:
            logger.debug("[For rising edge (ON)]")
        else:
            logger.debug("[For falling edge (OFF)]")
        '''
        # Temp code -- END

        # Add a window around the event edges
        s_time = edge_time - edge_window - (5 * sampling_rate)
        e_time = edge_time + edge_window + 3

        logger.debug("Start time: %s [%s]", s_time, timestamp_to_str(s_time, date_format))
        logger.debug("End time: %s [%s]", e_time, timestamp_to_str(e_time, date_format))

        # For checking the edge, filter df to include data only in the window of <winmax> seconds
        # around the event time
        streams_df_new = [df[(df.time >= s_time) & (df.time <= e_time)]
                          for df in streams_df_list]
        logger.debug("Streams %d:\n%s", i, streams_df_new)

        # Detect edges for both meters
        edge_list.append(detect_edges_from_meters(streams_df_new))
    # logger.debug("\nEdges_i:\n\n%s", edge_list)

    # -------
    # Accumulate start/end edges from each meter
    # -------
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

    logger.debug("Edges: \n%s", meter_edges_list)

    if len(meter_edges_list) == 0:
        # No edges detected
        power = 0
        logger.debug("No activity in the given time period!")
        return power

    # -------
    # Determine in which meter, edge was detected and compute power
    # -------
    for meter_edges in meter_edges_list:
        if "start" not in meter_edges or "end" not in meter_edges:
            logger.debug("Keywords missing (start/end)!")
            continue

        start_df = meter_edges["start"]
        end_df = meter_edges["end"]

        start_len = len(start_df)
        end_len = len(end_df)

        if start_len == 0 or end_len == 0:
            logger.debug("Start/End edge set is empty")
            continue

        end_df["magnitude"] = end_df.magnitude.abs()
        if start_len == 1 and end_len == 1:
            start_mag = start_df.ix[start_df.index[0]]["magnitude"]
            end_mag = end_df.ix[end_df.index[0]]["magnitude"]
            # Compute power
            power = compute_power(start_mag, end_mag)
            logger.debug("Power consumed:%s", power)

        elif start_len > 1 and end_len > 1:
            # Compare based on the power magnitude
            logger.debug("Double CONFUSION!!")

        elif start_len > 1 or end_len > 1:
            if start_len > 1:
                less_df = end_df.copy()
                more_df = start_df.copy()
            elif end_len > 1:
                less_df = start_df.copy()
                more_df = end_df.copy()

            less_mag = less_df.ix[less_df.index[0]]["magnitude"]

            power = less_mag * percent_change
            min_mag = less_mag - power
            max_mag = less_mag + power

            more_mag_list = [{'mag': more_df.ix[idx]["magnitude"],
                              'diffce': math.fabs(more_df.ix[idx]["magnitude"] - less_mag)}
                             for idx in more_df.index
                             if more_df.ix[idx]["magnitude"] >= min_mag
                             and more_df.ix[idx]["magnitude"] <= max_mag]

            if len(more_mag_list) == 0:
                logger.debug("No matching end edges found")
                continue

            more_mag_df = pd.DataFrame(more_mag_list, columns=['mag', 'diffce'])
            more_mag_df = more_mag_df[more_mag_df.diffce == more_mag_df.diffce.min()]
            more_mag_df.reset_index(drop=True, inplace=True)

            more_mag = more_mag_df.ix[0]["mag"]

            # Compute power
            power = compute_power(less_mag, more_mag)

    logger.debug("Power consumed: %s", power)
    return power


def combine_streams(df):
    """
    Receives the light and power streams and combines them into one stream
    """

    stream1_df = df[0]
    stream2_df = df[1]

    stream1_df['time'] = (stream1_df['time']).astype('int')
    stream2_df['time'] = (stream2_df['time']).astype('int')

    start_time = min(stream1_df.ix[0]['time'], stream2_df.ix[0]['time'])
    end_time = max(stream1_df.ix[stream1_df.index[-1]]['time'],
                   stream2_df.ix[stream2_df.index[-1]]['time'])
    # logger.debug ("ST:%s ET:%s", start_time, end_time)

    time_values = range(start_time, end_time + 1, sampling_rate)
    n_time_values = len(time_values)
    # logger.debug ("Total values: %d ", n_time_values)

    stream1 = dict(zip(stream1_df.time, stream1_df.power))
    stream2 = dict(zip(stream2_df.time, stream2_df.power))

    # logger.debug ("Stream1 %s", stream1)
    # logger.debug ("Stream2 %s", stream2)

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
        # logger.debug ("Stream %d :\n%s", i, streams[i].head(10))

    # Combining Streams
    comb_stream_df = pd.DataFrame({'time': time_values, 'power': [0] * n_time_values},
                                  columns=['time', 'power'])
    # comb_stream_df['time'] = comb_stream_df['time'] * 1000
    for idx in comb_stream_df.index:
        comb_stream_df.ix[idx]['power'] = streams[0].ix[idx]['power'] + streams[1].ix[idx]['power']

    comb_stream_df.sort('time', inplace=True)
    # logger.debug ("Combined Stream:\n %s", comb_stream_df.head(20))

    return comb_stream_df
