import os
import math
import time
import pandas as pd
import datetime as dt
# import numpy as np

from django.conf import settings

base_dir = settings.BASE_DIR
res_folder = os.path.join(base_dir, 'results/')
gt_folder = os.path.join(base_dir, 'ground_truth/')

# Bounds for time frame (in seconds)
limit = 7


def to_time(time_string):
    return time.mktime(dt.datetime.strptime(time_string, "%d/%m/%YT%H:%M:%S").timetuple())


def read_run_no():
    '''
    Function to read the run no from the common file
    '''
    cfile = res_folder + "current.txt"
    f = open(cfile, 'r')
    n_run = f.read()
    f.close()

    return n_run


def is_missed_set():
    '''
    Function to read the remove missed value from the common file
    '''
    rfile = res_folder + "missed.txt"
    f = open(rfile, 'r')
    missed = f.read()
    f.close()

    return bool(missed)


def check_spurious_missed_event(apt_no, ev_timestamp):
    '''
    Function to check if event matches with ground truth
    If yes, then return the record and return result
    '''
    ev_timestamp = int(ev_timestamp)

    ev_log_file = gt_folder + str(apt_no) + '_eventlog.csv'
    gt_df = pd.read_csv(ev_log_file)

    gt_missed = gt_df[gt_df.missed == 1]
    act_missed = gt_missed.act_id.unique().tolist()

    missed_status = False
    spurious_status = True

    # Remove missed
    for gidx in gt_df.index:

        true_time = int(gt_df.ix[gidx]['timestamp'])
        act_id = gt_df.ix[gidx]['act_id']

        if math.fabs(ev_timestamp - true_time) <= limit:
            spurious_status = False

            if act_id in act_missed:
                missed_status = True

            return missed_status, spurious_status

    return missed_status, spurious_status


def match_ground_truth(apt_no, ev_timestamp, location, appliance):
    '''
    Function to check if event matches with ground truth
    If yes, then return the record
    '''

    if is_missed_set():
        ev_log_file = gt_folder + str(apt_no) + '_missed_eventlog.csv'
    else:
        ev_log_file = gt_folder + str(apt_no) + '_eventlog.csv'

    gt_df = pd.read_csv(ev_log_file)

    ev_timestamp = int(ev_timestamp)
    label = 'none'
    for gidx in gt_df.index:

        true_time = int(gt_df.ix[gidx]['timestamp'])
        true_loc = gt_df.ix[gidx]['location']
        true_appl = gt_df.ix[gidx]['appliance']

        if math.fabs(ev_timestamp - true_time) <= limit:

            if (location != "dummy" and appliance != "dummy"):

                label = ''
                if location != true_loc:
                    label = "location"
                if appliance != true_appl:
                    if label == "location":
                        label = "both"
                    else:
                        label = "appliance"

                if label == '':
                    return True, label

                break

            elif(location != "dummy" and location == true_loc):
                return True, "location"
            elif (appliance != "dummy" and appliance == true_appl):
                return True, "appliance"
    if label != 'none' and label != '':
        return False, label
    return False, "spurious"


def match_location(apt_no, dev_id, timestamp, location):
    '''
    Function to check if event matches with ground truth location
    '''
    timestamp = int(timestamp)

    tos_file = gt_folder + str(apt_no) + '_' + str(dev_id) + '_timeofstay.csv'

    gt_df = pd.read_csv(tos_file)
    gt_df['time_entered'] = [to_time(time_string) for time_string in gt_df.time_entered]
    gt_df['time_left'] = [to_time(time_string) for time_string in gt_df.time_left]

    gt_df['time_entered'] = gt_df.time_entered.astype('int')
    gt_df['time_left'] = gt_df.time_left.astype('int')

    for gidx in gt_df.index:

        true_loc = gt_df.ix[gidx]['location']
        time_entered = gt_df.ix[gidx]['time_entered']
        time_left = gt_df.ix[gidx]['time_left']

        if timestamp in range(time_entered, time_left + 1) and location == true_loc:
            return True
    return False


def match_appliance(apt_no, dev_id, timestamp, appliance):
    '''
    Function to check if event matches with ground truth location
    '''
    timestamp = int(timestamp)

    tos_file = gt_folder + str(apt_no) + '_' + str(dev_id) + '_timeofstay.csv'
    activity_log = gt_folder + str(apt_no) + '_activitylog.csv'

    gt_df = pd.read_csv(tos_file)
    gt_df['time_entered'] = [to_time(time_string) for time_string in gt_df.time_entered]
    gt_df['time_left'] = [to_time(time_string) for time_string in gt_df.time_left]

    gt_df['time_entered'] = gt_df.time_entered.astype('int')
    gt_df['time_left'] = gt_df.time_left.astype('int')

    # Find location
    for gidx in gt_df.index:

        true_loc = gt_df.ix[gidx]['location']
        time_entered = gt_df.ix[gidx]['time_entered']
        time_left = gt_df.ix[gidx]['time_left']

        if timestamp in range(time_entered, time_left + 1):
            location = true_loc
            break

    # Get activity log entries from the same location based on time
    activity_gt = pd.read_csv(activity_log)

    activity_gt = activity_gt[activity_gt.location == location]
    activity_gt = activity_gt[activity_gt.end_time <= timestamp]

    return False


def write_classification_labels(apt_no, dev_id, timestamp, label, value):
    '''
    Update event/user log with cause of error
    '''
    run_no = read_run_no()
    run_folder = res_folder + "offline/" + run_no + "/"

    event_log = run_folder + str(apt_no) + '_' + str(dev_id) + '_eventLog.csv'

    event_df = pd.read_csv(event_log)
    t_event_df = event_df[event_df.timestamp == timestamp]

    if len(t_event_df) == 1:
        idx = t_event_df.index[0]
    else:
        idx = t_event_df.index[-1]

    event_df.ix[idx, label] = value
    event_df.to_csv(event_log, index=False)


def write_reason(apt_no, dev_id, timestamp, reason, details):
    '''
    Update event log with cause of error
    '''
    run_no = read_run_no()
    run_folder = res_folder + "offline/" + run_no + "/"

    event_log = run_folder + str(apt_no) + '_' + str(dev_id) + '_eventLog.csv'

    event_df = pd.read_csv(event_log)
    t_event_df = event_df[event_df.timestamp == timestamp]

    if len(t_event_df) == 1:
        idx = t_event_df.index[0]
    else:
        idx = t_event_df.index[-1]

    event_rec = t_event_df.ix[idx]

    rec_reason = event_rec['reason']
    rec_details = str(event_rec['details'])

    if details != '':
        if rec_details != 'nan':
            details = rec_details + '-' + details
    elif rec_details != 'nan':
        details = rec_details

    print("Writing for [%s]: time=%s[%s] reason=%s details=%s \n" %
          (dev_id, timestamp, time.ctime(timestamp), rec_reason, details))

    if rec_reason == 'spurious':
        pass
    elif (rec_reason == 'location' and reason == 'appliance') or \
            (rec_reason == 'appliance' and reason == 'location'):
        event_df.ix[idx, 'reason'] = 'both'
    elif rec_reason != 'correct' and reason == 'correct':
        event_df.ix[idx, 'reason'] = rec_reason
    else:
        event_df.ix[idx, 'reason'] = reason

    event_df.ix[idx, 'details'] = details

    event_df.to_csv(event_log, index=False)


def get_table_df(apt_no, table_name):
    '''
    Gets the table df
    table_name: event, activity, usage, wastage
    '''
    run_no = read_run_no()
    run_folder = res_folder + "offline/" + run_no + "/"

    if table_name == "event":
        log_file = run_folder + str(apt_no) + '_common_eventLog.csv'
    else:
        log_file = run_folder + str(apt_no) + '_' + table_name + 'Log.csv'

    df = pd.read_csv(log_file)
    return df


def get_on_events(apt_no, event_time):
    event_df = get_table_df(apt_no, "event")

    event_df = event_df[(event_df.timestamp < event_time) & (event_df.apt_no == apt_no)
                        & (event_df.event_type == "ON") & (event_df.matched == 0)]

    return event_df


def get_on_events_by_location_offline(apt_no, event_time, location):
    event_df = get_table_df(apt_no, "event")

    if location == "all":
        event_df = event_df[(event_df.timestamp <= event_time) & (event_df.apt_no == apt_no)
                            & (event_df.event_type == "ON") & (event_df.matched == 0) &
                            (event_df.location != "Unknown")]

    else:
        event_df = event_df[(event_df.timestamp <= event_time) & (event_df.apt_no == apt_no)
                            & (event_df.event_type == "ON") & (event_df.matched == 0) &
                            (event_df.location != "Unknown") & (event_df.location == location)]

    return event_df


def get_off_events_by_offline(apt_no, on_event_time, off_event_time, location, appliance):
    event_df = get_table_df(apt_no, "event")

    event_df = event_df[(event_df.timestamp >= on_event_time) &
                        (event_df.timestamp <= off_event_time) &
                        (event_df.apt_no == apt_no) &
                        (event_df.event_type == "OFF") & (event_df.matched == 0) &
                        (event_df.location == location) & (event_df.appliance == appliance)]

    return event_df


def get_userid_from_event(apt_no, event_id):
    event_df = get_table_df(apt_no, "event")

    event_i = event_df[event_df.id == event_id]

    event = event_i.ix[event_i.index[0]]

    return event['dev_id']
