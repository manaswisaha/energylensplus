import os
import math
import time
import pandas as pd
import datetime as dt
import numpy as np

from django.conf import settings

base_dir = settings.BASE_DIR
res_folder = os.path.join(base_dir, 'results/')
gt_folder = os.path.join(base_dir, 'ground_truth/')

# Bounds for time frame (in seconds)
limit = 5


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


def check_spurious_event(apt_no, ev_timestamp):
    '''
    Function to check if event matches with ground truth
    If yes, then return the record and return result
    '''
    ev_log_file = gt_folder + str(apt_no) + '_eventlog.csv'

    gt_df = pd.read_csv(ev_log_file)

    ev_timestamp = int(ev_timestamp)
    for gidx in gt_df.index:

        true_time = int(gt_df.ix[gidx]['timestamp'])

        if math.fabs(ev_timestamp - true_time) <= limit:
            return False, gt_df.ix[gidx]

    return True, {}


def match_ground_truth(apt_no, ev_timestamp, location, appliance):
    '''
    Function to check if event matches with ground truth
    If yes, then return the record
    '''
    ev_log_file = gt_folder + str(apt_no) + '_eventlog.csv'

    gt_df = pd.read_csv(ev_log_file)

    ev_timestamp = int(ev_timestamp)
    for gidx in gt_df.index:

        true_time = int(gt_df.ix[gidx]['timestamp'])
        true_loc = gt_df.ix[gidx]['location']
        true_appl = gt_df.ix[gidx]['appliance']

        if math.fabs(ev_timestamp - true_time) <= limit:

            if (location != "dummy" and appliance != "dummy"):

                label = ''
                if location == true_loc:
                    label = "location"
                if appliance == true_appl:
                    if label == "location":
                        label = "both"
                    else:
                        label = "appliance"

                if label != '':
                    return True, label

            elif(location != "dummy" and location == true_loc) or \
                    (appliance != "dummy" and appliance == true_appl):
                return True, gt_df.ix[gidx]

    return False, {}


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
    print "Indexes::", event_df.index

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

    print("Writing for: timestamp[%s]=%s reason=%s details=%s \n" %
          (time.ctime(timestamp), timestamp, reason, details))

    if rec_reason == 'spurious':
        pass
    elif rec_reason == 'location' and reason == 'appliance':
        event_df.ix[idx, 'reason'] = 'both'
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


def get_userid_from_event(apt_no, event_id):
    event_df = get_table_df(apt_no, "event")

    event_i = event_df[event_df.id == event_id]

    event = event_i.ix[event_i.index[0]]

    return event['dev_id']
