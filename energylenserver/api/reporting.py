"""
Module for the energy reporting APIs
"""
import json
import time
import random as rnd

from numpy import random
from django_pandas.io import read_frame

from constants import PERSONAL_ENERGY_API, ENERGY_WASTAGE_REPORT_API
from energylenserver.models import functions as mod_func


# Enable Logging
import logging
logger = logging.getLogger('energylensplus_gcm')

"""
Helper Functions
"""


def constrained_sum_sample_pos(n, total):
    """Return a randomly chosen list of n positive integers summing to total.
    Each such list is equally likely to occur."""

    dividers = sorted(rnd.sample(xrange(1, total), n - 1))
    return [a - b for a, b in zip(dividers + [total], [0] + dividers)]


def random_id():
    """
    Used for generating message ids
    Returns: a random alphanumerical id
    """

    import string
    rid = ''
    for x in range(8):
        rid += random.choice(string.digits)
    return rid

"""
Main Functions
"""


def filter_user_activities(dev_id, activity_df):
    """
    Filter the activity list based on the specified user id
    """
    try:

        activity_id_list = activity_df.id.tolist()

        # User specific activities
        usage_entries = mod_func.retrieve_usage_entries(dev_id, activity_id_list)
        if isinstance(usage_entries, bool) or usage_entries.count() == 0:
            return False, False

        u_entries_df = read_frame(usage_entries, verbose=False)
        activity_id = u_entries_df.activity.unique().tolist()

        # Filtered activity
        activity_df = activity_df[activity_df.id.isin(activity_id)]

        return activity_df, u_entries_df

    except Exception, e:
        logger.debug("[FilterActivityException]:: %s", e)
        return False, False


def determine_hourly_consumption(start_time, end_time, no_of_hours, activities_df, consumption_df):
    """
    Determines the hourly usage/wastage based on activities
    """
    hourly_consumption = [0] * no_of_hours

    activities = {}
    for idx in activities_df:
        row = activities_df.ix[idx]
        activities[row['id']] = {'power': row['power']}

    i = 0
    if "usage" in consumption_df.columns:
        energy = "usage"
    elif "wastage" in consumption_df.columns:
        energy = "wastage"

    st = start_time
    while i < no_of_hours:

        et = st + 3600
        filtered_df = consumption_df[(consumption_df.start_time.isin(range(st, et))) |
                                     (consumption_df.end_time.isin(range(st, et)))]

        hour_usage = 0
        for idx in filtered_df.index:
            row = filtered_df.ix[idx]
            energy_val = row[energy]
            s_time = row['start_time']
            e_time = row['end_time']
            act_id = row['activity']
            power = activities[act_id]
            if s_time >= st and e_time < et:
                hour_usage += energy_val
            elif s_time >= st:
                duration = et - s_time
                hour_usage += duration * power
            elif e_time < et:
                duration = e_time - st
                hour_usage += duration * power
        hourly_consumption[i] = hour_usage
        i += 1

    return hourly_consumption


def get_energy_report(dev_id, api, start_time, end_time):
    """
    Retrieves all the activities for the user within the given time interval

    Input:the number of hours or the time interval
    """

    no_of_hours = 12
    if not str(end_time).isdigit():
        end_time_str = end_time.split(" ")
        if end_time_str[2] == "hours":
            no_of_hours = int(end_time_str[1])
            logger.debug("Number of hours: %d", no_of_hours)
    end_time = time.time()
    start_time = end_time - no_of_hours * 3600

    options = {}

    '''
    # Temp
    usage_list = random.randint(1000, size=no_of_hours)
    logger.debug("Energy Usage:%s", usage_list)
    total_usage = sum(usage_list)
    total_consumption = (total_usage * 100) / 40
    perc_list = constrained_sum_sample_pos(4, 100)
    perc_list.sort()
    '''

    # '''
    # Retrieve records from the db
    records = mod_func.retrieve_activities(start_time, end_time, activity_name="all")

    if isinstance(records, bool):
        return options

    all_activities_df = read_frame(records, verbose=False)
    activities_df, usage_df = filter_user_activities(dev_id, all_activities_df)

    if isinstance(activities_df, bool) or len(activities_df) == 0:
        return options
    # '''

    if api == PERSONAL_ENERGY_API:

        '''
        options['total_usage'] = total_usage
        options['total_consumption'] = total_consumption
        options['hourly_usage'] = usage_list.tolist()

        options['activities'] = []
        options['activities'].append(
            {'name': "TV", "usage": total_usage * perc_list[1] / 100.})
        options['activities'].append(
            {'name': "AC", "usage": total_usage * perc_list[2] / 100.})
        options['activities'].append(
            {'name': "Microwave", "usage": total_usage * perc_list[3] / 100.})
        options['activities'].append(
            {'name': "Unknown", "usage": total_usage * perc_list[0] / 100.})
        return options
        '''

        if len(activities_df) > 0:
            hourly_usage = determine_hourly_consumption(
                start_time, end_time, no_of_hours, activities_df, usage_df)

            if len(hourly_usage) > 0:
                total_usage = sum(hourly_usage)
                total_consumption = activities_df.usage.sum()
                options['total_usage'] = total_usage
                options['hourly_consumption'] = hourly_usage
                options['total_consumption'] = total_consumption

                logger.debug("Energy Usage:%s", hourly_usage)

                options['activities'] = []
                act_usage_df = activities_df.groupby(['appliance']).sum()

                for appl in act_usage_df.index:
                    options['activities'].append({'name': appl,
                                                  'usage': act_usage_df.ix[appl]['usage']})

    elif api == ENERGY_WASTAGE_REPORT_API:

        '''
        options['total_wastage'] = total_usage
        options['total_consumption'] = total_consumption
        # options['percent'] = (total_wastage / total_consumption) * 100
        options['hourly_wastage'] = usage_list.tolist()

        options['activities'] = []
        options['activities'].append(
            {'name': "TV", "wastage": total_usage * perc_list[1] / 100.})
        options['activities'].append(
            {'name': "AC", "wastage": total_usage * perc_list[2] / 100.})
        options['activities'].append(
            {'name': "Microwave", "wastage": total_usage * perc_list[3] / 100.})
        options['activities'].append(
            {'name': "Unknown", "wastage": total_usage * perc_list[0] / 100.})

        return options
        '''

        if len(activities_df) > 0:
            # Get wastage entries
            activity_id_list = activities_df.id.tolist()
            w_entries = mod_func.retrieve_wastage_entries(dev_id, activity_id_list)
            wastage_df = read_frame(w_entries, verbose=False)

            hourly_wastage = determine_hourly_consumption(
                start_time, end_time, no_of_hours, activities_df, wastage_df)

            if len(hourly_wastage) > 0:
                total_wastage = sum(hourly_wastage)
                total_consumption = activities_df.usage.sum()
                options['total_wastage'] = total_wastage
                options['hourly_consumption'] = hourly_wastage
                options['total_consumption'] = total_consumption

                logger.debug("Energy Wastage: %s", hourly_wastage)

                options['activities'] = []
                act_wastage_df = activities_df.groupby(['appliance']).sum()

                for appl in act_wastage_df.index:
                    options['activities'].append({'name': appl,
                                                  'wastage': act_wastage_df.ix[appl]['usage']})

    return options


def disaggregated_energy(dev_id, activity_name, start_time, end_time):
    """
    Retrieves all the entries for the selected activity within the given time interval
    """
    activities = []

    '''
    activities.append(
        {'id': 1, 'name': activity_name, 'location': 'Dining Room', "value": 320,
         "start_time": 1408086307, "end_time": 1408095726,
         "wastage_times": [{"start_time": 1408093500, "end_time": 1408093800}],
         "usage_times": [{"start_time": 1408091427, "end_time": 1408093227},
                         {"start_time": 1408094500, "end_time": 1408094726}]
         })
    activities.append(
        {'id': 2, 'name': activity_name, 'location': 'Dining Room', "value": 320,
         "start_time": 1408096865, "end_time": 1408111265,
         "wastage_times": [{"start_time": 1408105827, "end_time": 1408106727},
                           {"start_time": 1408107627, "end_time": 1408107927}],
         "usage_times": [{"start_time": 1408097100, "end_time": 1408099500},
                         {"start_time": 1408100400, "end_time": 1408104000}]
         })
    activities.append(
        {'id': 3, 'name': activity_name, 'location': 'Bedroom', "value": 120,
         "start_time": 1408165265, "end_time": 1408168865,
         "usage_times": [{"start_time": 1408165265, "end_time": 1408168865}],
         "wastage_times": [],
         })
    activities.append(
        {'id': 4, 'name': activity_name, 'location': 'Bedroom', "value": 120,
         "start_time": 1408179665, "end_time": 1408185065,
         "usage_times": [{"start_time": 1408183200, "end_time": 1408184100}],
         "wastage_times": [],
         })
    return activities
    '''

    no_of_hours = 12
    if not str(end_time).isdigit():
        end_time_str = end_time.split(" ")
        if end_time_str[2] == "hours":
            no_of_hours = int(end_time_str[1])
            logger.debug("Number of hours:%d", no_of_hours)
            end_time = time.time()
            start_time = end_time - no_of_hours * 3600

    records = mod_func.retrieve_activities(start_time, end_time, activity_name)

    if isinstance(records, bool):
        return activities

    all_activities_df = read_frame(records, verbose=False)
    all_activities_df, usage_entries_df = filter_user_activities(dev_id, all_activities_df)

    if isinstance(all_activities_df, bool):
        return activities

    if len(all_activities_df) > 0:

        activity_id_list = all_activities_df.id.tolist()

        # Wastage entries
        wastage_entries = {}
        w_entries = mod_func.retrieve_wastage_entries(dev_id, activity_id_list)
        if not isinstance(w_entries, bool) and w_entries.count() != 0:
            for act_id in activity_id_list:
                wastage_entries[act_id] = []
                for entry in w_entries:
                    wastage_entries[act_id].append({"start_time": entry.start_time,
                                                    "end_time": entry.end_time})

        # Usage entries
        usage_entries = {}
        if not isinstance(w_entries, bool):
            for act_id in activity_id_list:
                usage_entries[act_id] = []
                for idx in usage_entries_df.index:
                    entry = usage_entries_df.ix[idx]
                    usage_entries[act_id].append({"start_time": entry['start_time'],
                                                  "end_time": entry['end_time']})

        for idx in all_activities_df.index:

            aentry = all_activities_df.ix[idx]
            w_entry = []
            if len(wastage_entries) > 0:
                w_entry = wastage_entries[aentry['id']]

            u_entry = []
            if len(usage_entries) > 0:
                u_entry = usage_entries[aentry['id']]

            activities.append({"id": aentry['id'], "activity_name": aentry['name'],
                               "location": aentry['location'], "value": aentry['usage'],
                               "start_time": aentry['start_time'], "end_time": aentry['end_time'],
                               "usage_times": u_entry,
                               "wastage_times": w_entry,
                               # "shared": shared_entries[aentry['id']]
                               })

    return activities


def get_inferred_activities(dev_id):
    """
    Retrieves activities in the past n hour(s)
    Returns: validation report for ground truth with the activities in the past hour
    """
    activities = []

    '''
    # Temp code
    usage = random.randint(1000, size=7)
    activities.append(
        {'id': 1, 'name': 'TV', 'location': 'Dining Room', "usage": usage[0],
         "start_time": 1408093265, "end_time": 1408095726})
    activities.append(
        {'id': 2, 'name': 'Microwave', 'location': 'Kitchen', "usage": usage[1],
         "start_time": 1408096865, "end_time": 1408111265})
    activities.append(
        {'id': 3, 'name': 'TV', 'location': 'Bedroom', "usage": usage[2],
         "start_time": 1408165265, "end_time": 1408168865})
    activities.append(
        {'id': 4, 'name': 'AC', 'location': 'Bedroom', "usage": usage[3],
         "start_time": 1408179665, "end_time": 1408185065})

    return activities

    # '''

    report_period = 3600  # 1 hour in seconds
    end_time = time.time()
    start_time = end_time - report_period

    records = mod_func.retrieve_finished_activities(start_time, end_time)

    if isinstance(records, bool):
        return activities

    all_activities_df = read_frame(records, verbose=False)
    all_activities_df, u_entries_df = filter_user_activities(dev_id, all_activities_df)

    if isinstance(all_activities_df, bool):
        return activities

    if len(all_activities_df) > 0:
        for idx in all_activities_df.index:
            aentry = all_activities_df.ix[idx]
            activities.append({'id': aentry['id'], 'name': aentry['name'],
                               'location': aentry['location'], "usage": aentry['usage'],
                               "start_time": aentry['start_time'], "end_time": aentry['end_time']})

    return activities
