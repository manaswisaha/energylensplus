"""
Module for the energy reporting APIs
"""
import time
import random as rnd
from numpy import random
from constants import PERSONAL_ENERGY_API, ENERGY_WASTAGE_REPORT_API
from energylenserver.models.functions import *


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

    rid = ''
    for x in range(8):
        rid += random.choice(string.digits)
    return rid

"""
Main Functions
"""


def determine_hourly_usage(no_of_hours, activities, usage_entries):
    """
    Determines the hourly usage/wastage based on activities
    """
    pass


def get_energy_report(reg_id, api, start_time, end_time):
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

    # Temp code
    # usage_list = [1000, 1030, 1100, 4500, 2300, 5500, 3200, 2100, 5500, 6000, 3000, 7800]
    usage_list = random.randint(1000, size=no_of_hours)
    logger.debug("Energy Usage:%s", usage_list)

    total_usage = sum(usage_list)
    perc_list = constrained_sum_sample_pos(4, 100)
    perc_list.sort()

    options = {}

    if api == PERSONAL_ENERGY_API:
        # Retrieve records from the db
        # activities = retrieve_activities(reg_id, start_time, end_time)
        # if activities:
            # usage_entries = retrieve_usage_entries(activities.keys())
            # hourly_usage = determine_hourly_usage(no_of_hours, activities, usage_entries)
            # logger.debug "Detected Activities:\n " + activities

        # Temp code
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

    elif api == ENERGY_WASTAGE_REPORT_API:
        # Call API
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


def get_inferred_activities(reg_id):
    """
    Retrieves activities in the past n hour(s)
    Returns: validation report for ground truth with the activities in the past hour
    """
    activities = []

    report_period = 3600  # 1 hour
    end_time = time.time()
    start_time = end_time - report_period
    # activities = retrieve_activities(reg_id, start_time, end_time, "all")

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
    activities.append(
        {'id': 5, 'name': 'Kettle', 'location': 'Kitchen', "usage": usage[4],
         "start_time": 1408056865, "end_time": 1408151265})
    activities.append(
        {'id': 6, 'name': 'Kettle', 'location': 'Kitchen', "usage": usage[5],
         "start_time": 1409815593, "end_time": 1409819193})
    activities.append(
        {'id': 7, 'name': 'AC', 'location': 'Sitting Room', "usage": usage[6],
         "start_time": 1409790393, "end_time": 1409793993})
    return activities


def disaggregated_energy(reg_id, activity_name, start_time, end_time):
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
    # activities = retrieve_activities(reg_id, start_time, end_time, activity_name)
    activities.append(
        {'id': 1, 'name': activity_name, 'location': 'Dining Room', "value": 320,
         "start_time": 1408086307, "end_time": 1408095726,
         "wastage_times": [{"start_time": 1408093500, "end_time": 1408093800},
                           {"start_time": 1408094100, "end_time": 1408094400}]})
    activities.append(
        {'id': 2, 'name': activity_name, 'location': 'Dining Room', "value": 320,
         "start_time": 1408096865, "end_time": 1408111265,
         "wastage_times": [{"start_time": 1408097100, "end_time": 1408099500},
                           {"start_time": 1408100400, "end_time": 1408104000}]})
    activities.append(
        {'id': 3, 'name': activity_name, 'location': 'Bedroom', "value": 120,
         "start_time": 1408165265, "end_time": 1408168865,
         "wastage_times": []})
    activities.append(
        {'id': 4, 'name': activity_name, 'location': 'Bedroom', "value": 120,
         "start_time": 1408179665, "end_time": 1408185065,
         "wastage_times": [{"start_time": 1408183200, "end_time": 1408184100}]})

    return activities
