import os
import sys
import time
import math
import pandas as pd
import numpy as np
import datetime as dt


# Django imports
from django.conf import settings
from energylenserver.common_imports import *
from energylenserver.core import apportionment as aprt
from energylenserver.models import functions as mod_func
from django_pandas.io import read_frame


# Enable Logging
logger = logging.getLogger('energylenserver')

base_dir = settings.BASE_DIR
folder = os.path.join(base_dir, 'results/')
gt_folder = os.path.join(base_dir, 'ground_truth/')


apt_no_list = [103, 101, 1201]


def to_time(time_string):
    return time.mktime(dt.datetime.strptime(time_string, "%d/%m/%YT%H:%M:%S").timetuple())

d_times = {103: {'st_time': int(to_time("1/2/2015T15:30:00")),
                 'et_time': int(to_time("12/2/2015T06:30:00"))},
           101: {'st_time': int(to_time("4/2/2015T13:00:00")),
                 'et_time': int(to_time("17/2/2015T17:00:00"))},
           1201: {'st_time': int(to_time("8/2/2015T05:05:00")),
                  # 1201: {'st_time': int(to_time("26/1/2015T07:35:00")),
                  'et_time': int(to_time("13/2/2015T00:00:00"))}}


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


def create_presence_log(apt_no, presence_log):
    '''
    Creates a presence log for the apartment based on
    time of stay values from occupants
    '''
    occupants = mod_func.retrieve_users(apt_no)

    for user in occupants:
        devid = user.dev_id
        user_log = gt_folder + str(apt_no) + '_' + \
            str(devid) + '_timeofstay.csv'
        u_presence_log = gt_folder + str(apt_no) + '_' + \
            str(devid) + '_presencelog.csv'

        user_df = pd.read_csv(user_log)
        user_df['time_entered'] = [to_time(time_string) for time_string in user_df.time_entered]
        user_df['time_left'] = [to_time(time_string) for time_string in user_df.time_left]

        user_df['time_entered'] = user_df.time_entered.astype('int')
        user_df['time_left'] = user_df.time_left.astype('int')

        presence_df = pd.DataFrame(columns=['timestamp', 'location'])

        for idx in user_df.index:

            true_loc = user_df.ix[idx]['location']
            time_entered = user_df.ix[idx]['time_entered']
            time_left = user_df.ix[idx]['time_left']

            timestamp = range(time_entered, time_left + 1)
            location = [true_loc] * len(timestamp)

            tmp_df = pd.DataFrame({'timestamp': timestamp, 'location': location},
                                  columns=['timestamp', 'location'])

            presence_df = pd.concat([presence_df, tmp_df])

        presence_df.sort(['timestamp'], inplace=True)
        presence_df.reset_index(drop=True, inplace=True)
        presence_df.to_csv(u_presence_log, index=False)

    with open(presence_log, "w+") as myfile:
        myfile.write("Presence log created")


limit = 7


def check_activity(apt_no, activity, event_df, gt_activity_df):
    '''
    Validate inferred activity with ground truth,
    and return the result along with the reason
    '''
    try:
        # Start validation of activity
        start_eventid = activity.start_event
        start_ev = event_df[event_df.id == start_eventid]
        start_idx = start_ev.index[0]

        start_event = start_ev.ix[start_idx]
        # Check start event
        if start_event['reason'] == 'correct':

            # If correct, then check end event
            end_eventid = activity.end_event
            end_ev = event_df[event_df.id == end_eventid]
            end_idx = end_ev.index[0]

            end_event = end_ev.ix[end_idx]

            if end_event['reason'] == 'correct':

                # If both events are correct, then check if both start and end event belong together
                for idx in gt_activity_df.index:
                    true_st = gt_activity_df.ix[idx]['start_time']
                    true_et = gt_activity_df.ix[idx]['end_time']

                    if (math.fabs(start_event['timestamp'] - true_st) <= limit) and \
                            (math.fabs(end_event['timestamp'] - true_et) <= limit):
                        return True, "correct"
                return False, "incorrect"

            else:
                return False, end_event['reason']
        else:
            return False, start_event['reason']
    except Exception, e:
        logger.exception("[Check Activity]:: %s", e)


def get_error_assigned_activity_energy(apt_no, activity, gt_activity_df):
    '''
    Determines how much of the inferred activity is correct
    '''
    location = activity.location
    appliance = activity.appliance
    start_time = activity.start_time
    end_time = activity.end_time
    act_duration = set(range(start_time, end_time + 1))

    filt_gt_df = gt_activity_df[(gt_activity_df.location == location) &
                                (gt_activity_df.appliance == appliance) &
                                (gt_activity_df.start_time.isin(act_duration) |
                                    gt_activity_df.end_time.isin(act_duration))]

    inferred = 0
    actual = 0

    for idx in filt_gt_df.index:

        true_st = filt_gt_df.ix[idx]['start_time']
        true_et = filt_gt_df.ix[idx]['end_time']
        true_duration = set(range(true_st, true_et + 1))

        common_duration = act_duration & true_duration

    return


def segregate(string):

    str_list = string.split('-')

    s_str_list = [lstr.split('_') for lstr in str_list]

    arr_list = []
    for item in s_str_list:
        arr_list += item

    if "similar appliance" in arr_list:
        return True
    else:
        return False


def calculate_accuracy_summary(apt_no, run_no, remove_missed, running_time):
    '''
    Calculates the different errors based on
            - the error group
            - cumulative result for events and activities
    Calculates the apportionment accuracy in comparison to ground truth
    --- total energy usage and wastage per person
    Refer: Wattshare -- cal. percentage error
    '''
    try:
        # Folders
        run_folder = folder + "offline/" + run_no + '/'

        # Ground truth files
        if remove_missed:
            gt_evlog_file = gt_folder + str(apt_no) + '_missed_eventlog.csv'
            gt_activitylog_file = gt_folder + str(apt_no) + '_missed_activitylog.csv'
        else:
            gt_evlog_file = gt_folder + str(apt_no) + '_eventlog.csv'
            gt_activitylog_file = gt_folder + str(apt_no) + '_activitylog.csv'

        # Ground truth
        gt_event_df = pd.read_csv(gt_evlog_file)
        gt_activity_df = pd.read_csv(gt_activitylog_file)

        # Event and activity log files
        eventlog_file = run_folder + str(apt_no) + '_common_eventLog.csv'
        activitylog_file = run_folder + str(apt_no) + '_activityLog.csv'

        '''
        Calculate event accuracy
        '''
        event_df = pd.read_csv(eventlog_file)
        total_actual_events = len(gt_event_df)
        total_inferred_events = len(event_df)
        gt_missed_events = len(gt_event_df[gt_event_df.missed == 1])

        error_groups = ['correct', 'spurious', 'location', 'appliance', 'both']
        # Calculate error groups - events
        total_group_events = {}
        for group in error_groups:
            total_group_events[group] = len(event_df[event_df.reason == group])

        # Find similar appliance entries
        # Look for groups - both and appliance and search for substring - similar appliance
        df = event_df[event_df.reason.isin(['both', 'appliance'])]
        df['d_details'] = df.details.apply(segregate)

        total_similar_appliance_errors = len(np.where(df['d_details'] == True)[0])
        percent_sim = (total_similar_appliance_errors / float(total_inferred_events)) * 100

        appliance_error_groups = ['similar appliance', 'distance diff',
                                  'multiple users', 'audio based']

        '''
        Calculate activity accuracy
        '''
        activity_df = pd.read_csv(activitylog_file)
        total_actual_activities = len(gt_activity_df)
        total_inferred_activities = len(activity_df)
        gt_missed_activities = len(gt_activity_df[(gt_activity_df.st_missed == 1) |
                                                  gt_activity_df.et_missed == 1])

        activity_df['reason'] = [''] * len(activity_df)

        for idx in activity_df.index:
            activity = activity_df.ix[idx]
            match, reason = check_activity(apt_no, activity, event_df, gt_activity_df)

            correct_assigned_energy = 0

            activity_df.ix[idx, 'reason'] = reason

        # Calculate error groups - events
        total_group_activities = {}
        for group in error_groups + ['incorrect']:
            total_group_activities[group] = len(activity_df[activity_df.reason == group])

        '''
        Apportionment accuracy
        '''
        # Usage and Wastage log files
        usagelog_file = run_folder + str(apt_no) + '_usageLog.csv'
        wastagelog_file = run_folder + str(apt_no) + '_wastageLog.csv'

        usage_df = pd.read_csv(usagelog_file)
        wastage_df = pd.read_csv(wastagelog_file)

        # Get metadata
        occupants = mod_func.retrieve_users(apt_no)
        m_data = mod_func.retrieve_metadata(apt_no)
        metadata_df = read_frame(m_data, verbose=False)
        rooms = metadata_df.location.unique()
        labels = dict(enumerate(list(rooms)))
        rooms_dict_val = {v: k for k, v in labels.items()}

        # Get presence based appliances
        metadata_df['appliance'] = metadata_df.appliance.apply(lambda s: s.split('_')[0])
        tmp_metadata_df = metadata_df.ix[:, ['appliance']].drop_duplicates()
        metadata_df = metadata_df.ix[tmp_metadata_df.index]
        presence_based = metadata_df[metadata_df.presence_based == 1].appliance.tolist()

        correct_act_df = activity_df[activity_df.reason == "correct"]

        correct_act_df['error_percent'] = [0] * len(correct_act_df)
        correct_act_df['tot_error_percent'] = [0] * len(correct_act_df)
        correct_act_df['usage_error_percent'] = [0] * len(correct_act_df)
        correct_act_df['wastage_error_percent'] = [0] * len(correct_act_df)

        total_usage = 0
        total_wastage = 0
        total_consumption = 0
        for act_count, idx in enumerate(correct_act_df.index):
            act_entry = correct_act_df.ix[idx]

            act_id = act_entry['id']
            start_time = int(act_entry['start_time'])
            end_time = int(act_entry['end_time'])
            location = act_entry['location']
            appliance = act_entry['appliance']
            power = act_entry['power']
            actual_consumption = aprt.get_energy_consumption(start_time, end_time, power)

            total_consumption += actual_consumption

            if appliance in presence_based:
                # Creation of presence matrix from ground truth
                timestamp = range(start_time, end_time + 1)
                presence_df = pd.DataFrame(index=timestamp)

                for user in occupants:
                    devid = user.dev_id
                    u_presence_log = gt_folder + str(apt_no) + '_' + \
                        str(devid) + '_presencelog.csv'

                    gt_presence_df = pd.read_csv(u_presence_log)

                    gtp_df = gt_presence_df[(gt_presence_df.timestamp >= start_time) &
                                            (gt_presence_df.timestamp <= end_time) &
                                            (gt_presence_df.location == location)]
                    gtp_df = gtp_df.set_index('timestamp')

                    gtp_df.columns = [str(devid)]

                    gtp_df[str(devid)].replace(rooms_dict_val, inplace=True)

                    presence_df = presence_df.join(gtp_df)

                presence_df = presence_df.fillna(100)

                presence_df['user_count'] = presence_df.sum(axis=1, numeric_only=True)

                empty_df = presence_df[presence_df.user_count == 100]
                present_df = presence_df[presence_df.user_count != 100]

                wastage_duration = len(empty_df)
                usage_duration = len(present_df)

                true_usage = round(float(usage_duration) / 3600.0, 2) * power
                true_wastage = round(float(wastage_duration) / 3600.0, 2) * power

                # Per-user apportionment accuracy (comparison w/ ground truth)

            else:
                true_usage = actual_consumption
                true_wastage = 0

            actual_tot_consumption = true_usage + true_wastage

            # Calculation from the inferred data
            fil_u_df = usage_df[usage_df.activity_id == act_id]
            fil_w_df = wastage_df[wastage_df.activity_id == act_id]

            tot_usage = 0
            if len(fil_u_df) > 0:
                for e_idx in fil_u_df.index:
                    tot_usage += fil_u_df.ix[e_idx]['usage']

            tot_wastage = 0
            if len(fil_w_df) > 0:
                for e_idx in fil_w_df.index:
                    tot_wastage += fil_w_df.ix[e_idx]['wastage']

            tot_consumption = tot_usage + tot_wastage

            total_usage += tot_usage
            total_wastage += tot_wastage

            # Per-activity apportionment accuracy (comparison w/ ground truth)
            consumption_error_perc = (
                math.fabs(actual_consumption - tot_consumption) / actual_consumption) * 100
            usage_error_perc = (math.fabs(true_usage - tot_usage) / true_usage) * 100

            if true_wastage == 0:
                wastage_error_perc = 0
            else:
                wastage_error_perc = (math.fabs(true_wastage - tot_wastage) / true_wastage) * 100

            correct_act_df.ix[idx, 'tot_error_percent'] = round(consumption_error_perc, 2)
            correct_act_df.ix[idx, 'usage_error_percent'] = round(usage_error_perc, 2)
            correct_act_df.ix[idx, 'wastage_error_percent'] = round(wastage_error_perc, 2)

            if correct_act_df.ix[idx, 'usage_error_percent'] > 0:
                print("[%d] Activity ID: %d" % (act_count, idx))
                print "Location:", location
                print "Appliance:", appliance
                print "Actual total consumption:", actual_consumption
                print "Actual consumption error:", (actual_consumption - actual_tot_consumption)
                print "True usage:", true_usage
                print "True wastage:", true_wastage
                print "Inferred usage:", tot_usage
                print "Inferred wastage:", tot_wastage
                print "Usage Error:", correct_act_df.ix[idx, 'usage_error_percent']
                print "Wastage Error:", correct_act_df.ix[idx, 'wastage_error_percent']
                print "\n"

            # Segregation Accuracy (algorithm accuracy)
            error_percent = (
                math.fabs(actual_consumption - tot_consumption) / actual_consumption) * 100
            correct_act_df.ix[idx, 'error_percent'] = round(error_percent, 2)

        avg_error_percent = correct_act_df['error_percent'].mean()
        avg_tot_error_percent = correct_act_df['tot_error_percent'].mean()
        avg_usage_error_percent = correct_act_df['usage_error_percent'].mean()
        avg_wastage_error_percent = correct_act_df['wastage_error_percent'].mean()

        print "Total Usage:", total_usage
        print "Total Wastage:", total_wastage
        print "Avg. Total Error:", avg_tot_error_percent
        print "Avg. Usage Error:", avg_usage_error_percent
        print "Avg. Wastage Error:", avg_wastage_error_percent

        # sys.exit(0)

        '''
        Print report
        '''
        report_file = run_folder + str(apt_no) + '_report.txt'
        if os.path.isfile(report_file):
            os.unlink(report_file)

        # Create report
        with open(report_file, "w+") as myfile:

            myfile.write("-" * 20 + "\n")
            myfile.write("Apartment number:: %s\n" % apt_no)
            myfile.write("Run number:: %s\n" % run_no)
            myfile.write("Running time:: %s minutes\n" % running_time)
            myfile.write("-" * 20 + "\n")

            # Print Ground truth summary
            myfile.write("Ground Truth Summary \n" + "-" * 20 + "\n")
            myfile.write("Total performed events:: %s\n" % total_actual_events)
            myfile.write("Total missed events:: %s\n" % gt_missed_events)
            myfile.write("Total performed activities:: %s\n" % total_actual_activities)
            myfile.write("Total missed activities:: %s\n" % gt_missed_activities)
            myfile.write("-" * 20 + "\n")

            # Print event summary
            myfile.write("Event Summary \n" + "-" * 20 + "\n")
            myfile.write("Total inferred events:: %s\n" % total_inferred_events)
            for group in error_groups:
                if group == "correct":
                    precision = (total_group_events[group] / float(total_inferred_events)) * 100
                    recall = (total_group_events[group] / float(total_actual_events)) * 100
                    myfile.write("Group '%s':: %s P/R::[%s/%s]\n" % (group,
                                                                     total_group_events[group],
                                                                     round(precision, 2),
                                                                     round(recall, 2)))
                else:
                    percent = (total_group_events[group] / float(total_inferred_events)) * 100
                    myfile.write("Group '%s':: %s [%s]\n" % (group, total_group_events[group],
                                                             round(percent, 2)))
            myfile.write("Group 'similar appliance':: %s [%s]\n" %
                         (total_similar_appliance_errors, round(percent_sim, 2)))
            myfile.write("-" * 20 + "\n")

            # Print activity summary
            myfile.write("Activity Summary \n" + "-" * 20 + "\n")
            myfile.write("Total inferred activities:: %s\n" % total_inferred_activities)
            for group in error_groups + ['incorrect']:
                if group == "correct":
                    precision = (
                        total_group_activities[group] / float(total_inferred_activities)) * 100
                    recall = (total_group_activities[group] / float(total_actual_activities)) * 100
                    myfile.write("Group '%s':: %s P/R::[%s/%s]\n" %
                                 (group, total_group_activities[group],
                                  round(precision, 2),
                                  round(recall, 2)))
                else:
                    percent = (
                        total_group_activities[group] / float(total_inferred_activities)) * 100
                    myfile.write("Group '%s':: %s [%s]\n" % (group, total_group_activities[group],
                                                             round(percent, 2)))
            myfile.write("-" * 20 + "\n")

            # Print Apportionment Accuracy
            myfile.write("Apportionment Summary \n" + "-" * 20 + "\n")
            myfile.write("Total Consumption:: %s\n" % total_consumption)
            myfile.write("Total Usage:: %s\n" % total_usage)
            myfile.write("Total wastage:: %s\n" % total_wastage)

            myfile.write("Segregation error percentage:: %s\n" % round(avg_error_percent, 2))
            myfile.write("Energy apportionment error percentage:: %s\n" %
                         round(avg_tot_error_percent, 2))
            myfile.write("Usage error percentage:: %s\n" % round(avg_usage_error_percent, 2))
            myfile.write("Wastage error percentage:: %s\n" % round(avg_wastage_error_percent, 2))
            myfile.write("-" * 20 + "\n")

        # Read and send report to the stdout
        with open(report_file, 'r') as fin:
            print fin.read()

        '''
        # Result data structure
        result = {"event": {"actual": total_actual_events,
                            "inferred": total_inferred_events
                            },
                  "activity": {"actual": total_actual_activities,
                               "inferred": total_inferred_activities
                               }
                  }
        '''
    except Exception, e:
        logger.exception("[Calculate Accuracy]:: %s", e)
