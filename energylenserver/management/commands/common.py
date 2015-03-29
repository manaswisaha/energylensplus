import os
import time
import pandas as pd
import datetime as dt


# Django imports
from django.conf import settings

base_dir = settings.BASE_DIR
folder = os.path.join(base_dir, 'results/')


def to_time(time_string):
    return time.mktime(dt.datetime.strptime(time_string, "%d/%m/%YT%H:%M:%S").timetuple())

apt_no_list = [101, 103, 1201]
d_times = {103: {'st_time': int(to_time("1/2/2015T15:30:00")),
                 'et_time': int(to_time("12/2/2015T06:30:00"))},
           101: {'st_time': int(to_time("4/2/2015T13:00:00")),
                 'et_time': int(to_time("17/2/2015T17:00:00"))},
           1201: {'st_time': int(to_time("26/1/2015T00:00:00")),
                  'et_time': int(to_time("16/2/2015T00:00:00"))}}


def create_gt_event_log(gt_df, ev_log_path):
    '''
    Creates an event log from the ground truth of activities
    '''
    start_event_df = gt_df.ix[:, ['start_time', 'location', 'appliance', 'st_missed']]
    end_event_df = gt_df.ix[:, ['end_time', 'location', 'appliance', 'et_missed']]

    new_col_list = ['timestamp', 'location', 'appliance', 'missed']
    start_event_df.columns = new_col_list
    end_event_df.columns = new_col_list

    event_df = pd.concat([start_event_df, end_event_df])
    event_df['timestamp'] = event_df['timestamp'].fillna('1/1/1970T05:30:00')

    event_df['timestamp'] = [to_time(time_str) for time_str in event_df.timestamp]
    event_df.sort(['timestamp'], inplace=True)
    event_df.reset_index(inplace=True)
    ev_cols = event_df.columns.values
    ev_cols[0] = 'act_id'
    event_df.columns = ev_cols

    event_df.to_csv(ev_log_path, index=False)


def create_gt_activity_log(gt_df, activity_log_path):
    '''
    Creates an event log from the ground truth of activities
    '''
    gt_df['start_time'] = gt_df['start_time'].fillna('1/1/1970T05:30:00')
    gt_df['end_time'] = gt_df['end_time'].fillna('1/1/1970T05:30:00')

    gt_df['start_time'] = [to_time(time_str) for time_str in gt_df.start_time]
    gt_df['end_time'] = [to_time(time_str) for time_str in gt_df.end_time]
    gt_df.sort(['start_time'], inplace=True)
    gt_df.reset_index(inplace=True)
    gt_df.to_csv(activity_log_path, index=False)


def calculate_accuracy_summary(apt_no, run_no, remove_missed):
    '''
    Calculates the different errors based on
            - the error group
            - cumulative result for events and activities
    Calculates the apportionment accuracy in comparison to ground truth
    --- total energy usage and wastage per person
    Refer: Wattshare -- cal. percentage error
    '''
    # Folders
    run_folder = folder + "offline/" + run_no
    gt_folder = os.path.join(base_dir, 'ground_truth/')

    # Ground truth files
    gt_evlog_file = gt_folder + str(apt_no) + '_eventlog.csv'
    gt_activitylog_file = gt_folder + str(apt_no) + '_activitylog.csv'

    # Ground truth
    gt_event_df = pd.read_csv(gt_evlog_file)
    gt_activity_df = pd.read_csv(gt_activitylog_file)

    # Event and activity log files
    eventlog_file = run_folder + str(apt_no) + '_commoneventLog.csv'
    activitylog_file = run_folder + str(apt_no) + '_activityLog.csv'

    # Calculate event accuracy
    event_df = pd.read_csv(eventlog_file)
    total_actual_events = len(gt_event_df)
    total_inferred_events = len(event_df)
    gt_missed_events = len(gt_event_df[gt_event_df.missed == 1])
    incorrect_events = len(gt_event_df[gt_event_df.missed == 1])

    error_groups = ['correct', 'spurious', 'location', 'appliance', 'both']

    # Calculate activity accuracy
    activity_df = pd.read_csv(activitylog_file)
    total_actual_activities = len(gt_activity_df)
    total_inferred_activities = len(activity_df)

    # Result data structure
    result = {"event": {"actual": total_actual_events,
                        "inferred": total_inferred_events
                        },
              "activity": {"actual": total_actual_activities,
                           "inferred": total_inferred_activities
                           }
              }

    print "Results::"
    return result
