"""
Module for the energy reporting APIs
"""
import json
import time
import random as rnd
from numpy import random
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


def determine_hourly_consumption(no_of_hours, activities, consumption_entries):
    """
    Determines the hourly usage/wastage based on activities
    """
    hourly_consumption = []
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
            logger.debug("Number of hours:%d", no_of_hours)
    end_time = time.time()
    start_time = end_time - no_of_hours * 3600

    options = {}

    # Temp
    usage_list = random.randint(1000, size=no_of_hours)
    logger.debug("Energy Usage:%s", usage_list)
    total_usage = sum(usage_list)
    perc_list = constrained_sum_sample_pos(4, 100)
    perc_list.sort()

    # Retrieve records from the db
    activities = mod_func.retrieve_activities(dev_id, start_time, end_time, activity_name="all")
    logger.debug("Detected Activities: %s", activities)

    if api == PERSONAL_ENERGY_API:

        options['total_consumption'] = total_usage
        options['hourly_consumption'] = usage_list.tolist()

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

        if activities:
            usage_entries = mod_func.retrieve_usage_entries(activities.keys())
            hourly_usage = determine_hourly_consumption(no_of_hours, activities, usage_entries)

            if len(hourly_usage) > 0:
                total_usage = sum(hourly_usage)
                options['total_consumption'] = total_usage
                options['hourly_consumption'] = hourly_usage

                logger.debug("Energy Usage:%s", hourly_usage)

    elif api == ENERGY_WASTAGE_REPORT_API:

        options['total_wastage'] = total_usage
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

        if activities:
            wastage_entries = mod_func.retrieve_wastage_entries(activities.keys())
            hourly_wastage = determine_hourly_consumption(no_of_hours, activities, wastage_entries)

            if len(hourly_wastage) > 0:
                total_wastage = sum(hourly_wastage)
                options['total_consumption'] = total_wastage
                options['hourly_consumption'] = hourly_wastage

                logger.debug("Energy Wastage: %s", hourly_wastage)

    return options


def get_inferred_activities(dev_id):
    """
    Retrieves activities in the past n hour(s)
    Returns: validation report for ground truth with the activities in the past hour
    """
    activities = []

    report_period = 3600  # 1 hour
    end_time = time.time()
    start_time = end_time - report_period

    all_activities = []
    records = mod_func.retrieve_finished_activities(dev_id, start_time, end_time)

    for r in records:
        all_activities[r.id] = {'name': r.appliance, 'location': r.location,
                                'usage': r.power, 'start_time': r.start_time,
                                'end_time': r.end_time}
    logger.debug("Appliances::\n %s", json.dumps(all_activities))

    if len(all_activities) > 0:
        for act_id, aentry in all_activities.iteritems():
            activities.append({'id': act_id, 'name': aentry['name'], 'location': aentry['location'],
                               "usage": aentry['usage'], "start_time": aentry['start_time'],
                               "end_time": aentry['end_time']})

    return activities


def disaggregated_energy(dev_id, activity_name, start_time, end_time):
    """
    Retrieves all the entries for the selected activity within the given time interval
    """

    no_of_hours = 12
    if not str(end_time).isdigit():
        end_time_str = end_time.split(" ")
        if end_time_str[2] == "hours":
            no_of_hours = int(end_time_str[1])
            logger.debug("Number of hours:%d", no_of_hours)
            end_time = time.time()
            start_time = end_time - no_of_hours * 3600

    activities = []
    # '''
    activities.append(
        {'id': 1, 'name': activity_name, 'location': 'Dining Room', "value": 320,
         "start_time": 1408086307, "end_time": 1408095726,
         "wastage_times": [{"start_time": 1408093500, "end_time": 1408093800}],
         "shared": [{"start_time": 1408091427, "end_time": 1408093227, "value": 320},
                    {"start_time": 1408094500, "end_time": 1408094726, "value": 320}]
         })
    activities.append(
        {'id': 2, 'name': activity_name, 'location': 'Dining Room', "value": 320,
         "start_time": 1408096865, "end_time": 1408111265,
         "wastage_times": [{"start_time": 1408105827, "end_time": 1408106727},
                           {"start_time": 1408107627, "end_time": 1408107927}],
         "shared": [{"start_time": 1408097100, "end_time": 1408099500, "value": 320},
                    {"start_time": 1408100400, "end_time": 1408104000, "value": 320}]
         })
    activities.append(
        {'id': 3, 'name': activity_name, 'location': 'Bedroom', "value": 120,
         "start_time": 1408165265, "end_time": 1408168865,
         "wastage_times": [],
         "shared": []
         })
    activities.append(
        {'id': 4, 'name': activity_name, 'location': 'Bedroom', "value": 120,
         "start_time": 1408179665, "end_time": 1408185065,
         "wastage_times": [{"start_time": 1408183200, "end_time": 1408184100}],
         "shared": []
         })
    return activities

    # '''

    records = mod_func.retrieve_activities(dev_id, start_time, end_time, activity_name)

    record_count = records.count()
    logger.debug("Number of activities: %s", record_count)
    '''
    {'id': 1, 'name': activity_name, 'location': 'Dining Room', "value": 320,
         "start_time": 1408086307, "end_time": 1408095726,
         "wastage_times": [{"start_time": 1408093500, "end_time": 1408093800}],
         "shared": [{"start_time": 1408094100, "end_time": 1408094400, value: 160}]
         })
    '''
    for r in records:
        activities.append = {'id': r.id, 'name': r.appliance, 'location': r.location,
                             'usage': r.power, 'start_time': r.start_time, 'end_time': r.end_time}
    logger.debug("Appliances::\n %s", json.dumps(activities))

    return activities
