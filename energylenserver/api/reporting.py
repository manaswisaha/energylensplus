"""
Module for the energy reporting APIs
"""
import random as rnd
from numpy import random
from constants import PERSONAL_ENERGY_API, ENERGY_WASTAGE_REPORT_API
# , ENERGY_REPORT_API

"""
Helper Functions
"""


def constrained_sum_sample_pos(n, total):
    """Return a randomly chosen list of n positive integers summing to total.
    Each such list is equally likely to occur."""

    dividers = sorted(rnd.sample(xrange(1, total), n - 1))
    return [a - b for a, b in zip(dividers + [total], [0] + dividers)]

"""
Main Functions
"""


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
            print "Number of hours:", no_of_hours

    # Temp code
    # usage_list = [1000, 1030, 1100, 4500, 2300, 5500, 3200, 2100, 5500, 6000, 3000, 7800]
    usage_list = random.randint(1000, size=no_of_hours)
    print "Energy Usage", usage_list

    total_usage = sum(usage_list)
    perc_list = constrained_sum_sample_pos(4, 100)
    perc_list.sort()

    options = {}

    # Call either personal energy or energy wastage based on the api
    if api == PERSONAL_ENERGY_API:
        # Call API
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


def disaggregated_energy(reg_id, activity_name, start_time, end_time):
    """
    Retrieves all the entries for the selected activity within the given time interval
    """

    no_of_hours = 12
    if "last" in end_time:
        end_time_str = end_time.split(" ")
        if end_time_str[2] == "hours":
            no_of_hours = int(end_time_str[1])
            print "Number of hours:", no_of_hours

    activities = []
    # TODO: Retrieve records from the DB
    activities.append(
        {'id': 1, 'name': activity_name, 'location': 'Dining Room', "usage": 320,
         "start_time": 1408093265, "end_time": 1408095726})
    activities.append(
        {'id': 2, 'name': activity_name, 'location': 'Dining Room', "usage": 320,
         "start_time": 1408096865, "end_time": 1408111265})
    activities.append(
        {'id': 3, 'name': activity_name, 'location': 'Bedroom', "usage": 80,
         "start_time": 1408165265, "end_time": 1408168865})
    activities.append(
        {'id': 4, 'name': activity_name, 'location': 'Bedroom', "usage": 120,
         "start_time": 1408179665, "end_time": 1408185065})

    return activities
