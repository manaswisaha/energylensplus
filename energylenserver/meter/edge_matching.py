"""
Edge Matching Module
"""

import math
import numpy as np
import pandas as pd
from django_pandas.io import read_frame

from energylenserver.common_imports import *
from energylenserver.models import functions as mod_func
from energylenserver.core import functions as func

from energylenserver import common_offline as off_func

# Enable Logging
logger = logging.getLogger('energylensplus_django')


def match_events_offline(off_event):
    """
    Matches the off event with the rise event
    """
    apt_no = off_event.apt_no
    off_time = off_event.timestamp
    off_mag = math.fabs(off_event.magnitude)
    off_location = off_event.location
    off_appliance = off_event.appliance

    # Extract rising edges occurring before the fall edge
    # with similar power
    on_events = off_func.get_on_events(apt_no, off_time)
    if len(on_events) == 0:
        return False

    # Filter i: Remove all on events greater than 12 hours from off event
    new_on_events = on_events[off_time - on_events.timestamp < 12 * 60 * 60]

    id_list = []
    mag_diff = []
    time_diff = []
    location = []
    appliance = []
    event_mag = []
    for idx in new_on_events.index:
        on_event = new_on_events.ix[idx]

        id_list.append(on_event.id)
        event_mag.append(on_event.magnitude)
        mag_diff.append(math.fabs(off_mag - on_event.magnitude))
        time_diff.append(math.fabs(off_time - on_event.timestamp))
        location.append(on_event.location)
        appliance.append(on_event.appliance)

    df = pd.DataFrame({'id': id_list, 'event_mag': event_mag,
                       'mag_diff': mag_diff, 'time_diff': time_diff,
                       'location': location, 'appliance': appliance},
                      columns=['id', 'event_mag', 'mag_diff', 'time_diff',
                               'location', 'appliance'])

    # logger.debug("On Events DF: \n%s", df)

    # Get Metadata
    data = mod_func.retrieve_metadata(apt_no)
    metadata_df = read_frame(data, verbose=False)

    # Range of OFF event
    power = off_mag * percent_change
    min_mag = off_mag - power
    max_mag = off_mag + power

    logger.debug("Magnitude::%s per_change: %s", off_mag, power)
    logger.debug("Between min=[%s]  max=[%s]", min_mag, max_mag)

    # Filter 1: Determine if appliance is multi-state
    if func.determine_multi_state(metadata_df, off_location, off_appliance):
        filtered_df = df[(df.location == off_location) &
                         (df.appliance == off_appliance)]
        filtered_df.sort(['id'], inplace=True)
        filtered_df.reset_index(drop=True, inplace=True)

        logger.debug("Filtered on events of a multi-state appl: \n%s", filtered_df)

        if len(filtered_df) == 0:
            return False

        if len(filtered_df) > 1:

            '''
            Version 1:

            # Filter 4: Based on power consumption
            # Taking the ON event's which is the closest to the OFF event's magnitude

            min_mag_diff = filtered_df.mag_diff.min()
            filtered_df = filtered_df[filtered_df.mag_diff == min_mag_diff]
            filtered_df.reset_index(drop=True, inplace=True)
            '''

            '''
            Version 2.1:

            # Filter 4: Based on duration of usage
            # Take the ON event which closest to the OFF event's timestamp
            min_time_diff = filtered_df.time_diff.min()
            filtered_df = filtered_df[filtered_df.time_diff == min_time_diff]
            filtered_df.reset_index(drop=True, inplace=True)
            if len(filtered_df) == 0:
                return False
            logger.debug("Final set:%s \n", filtered_df)
            '''

            '''
            Version 2.1:
            '''
            # Multiple ON events are found
            # Check if sum of ON events is equivalent to the OFF event mag
            on_mag_sum = float(filtered_df.event_mag.sum())
            print on_mag_sum
            if on_mag_sum >= min_mag and on_mag_sum <= max_mag:
                # Select first ON event
                on_event_record = new_on_events[new_on_events.id == filtered_df.ix[0]['id']]
                on_event = on_event_record.ix[on_event_record.index[0]]
                return on_event

        else:
            on_event_mag = float(filtered_df.ix[0]['event_mag'])
            if on_event_mag >= min_mag and on_event_mag <= max_mag:
                on_event_record = new_on_events[new_on_events.id == filtered_df.ix[0]['id']]
                on_event = on_event_record.ix[on_event_record.index[0]]
                return on_event
            else:
                # Extract OFF events between first ON and this OFF event
                on_event_record = new_on_events[new_on_events.id == filtered_df.ix[0]['id']]
                first_on_event = on_event_record.ix[on_event_record.index[0]]
                on_event_time = int(first_on_event.timestamp)
                off_event_df = off_func.get_off_events_by_offline(apt_no, on_event_time,
                                                                  off_time, off_location,
                                                                  off_appliance)

                if len(off_event_df) > 1:
                    off_mag_sum = float(off_event_df.magnitude.sum())

                    # Range of ON event
                    power = off_mag_sum * percent_change
                    min_mag = off_mag_sum - power
                    max_mag = off_mag_sum + power
                    if on_event_mag >= min_mag and on_event_mag <= max_mag:
                        on_event_record = new_on_events[new_on_events.id == filtered_df.ix[0]['id']]
                        on_event = on_event_record.ix[on_event_record.index[0]]
                        return on_event

        return False

    # Filter 2: Match falling with rising edges where its magnitude is between
    # a power threshold window

    filtered_df = df[(df.event_mag >= min_mag) & (df.event_mag <= max_mag)]

    # logger.debug("Filtered on events based on magnitude range: \n%s", filtered_df)

    if len(filtered_df) == 0:
        return False

    # Filter 3: Matching with the same location and appliance
    # if appliance is a presence based appliance

    metadata_df['appliance'] = metadata_df.appliance.apply(lambda s: s.split('_')[0])

    if off_appliance != "Unknown":
        metadata_df = metadata_df[metadata_df.appliance == off_appliance]
        logger.debug("Off appliance: %s metadata_df %s", off_appliance, metadata_df)
        metadata_df = metadata_df.ix[:, ['appliance', 'presence_based']].drop_duplicates()
        metadata_df.reset_index(inplace=True, drop=True)

        if not metadata_df.ix[0]['presence_based']:
            filtered_df = filtered_df[filtered_df.appliance == off_appliance]
        else:
            filtered_df = filtered_df[(filtered_df.location == off_location) &
                                      (filtered_df.appliance == off_appliance)]
    else:
        filtered_df = filtered_df[filtered_df.location == off_location]

    filtered_df.reset_index(drop=True, inplace=True)

    if len(filtered_df) == 0:
        return False

    logger.debug("Matched ON DF:\n%s", filtered_df)

    # Resolve conflicts by --
    if len(filtered_df) > 1:

        '''
        Version 1:

        # Filter 4: Based on power consumption
        # Taking the ON event's which is the closest to the OFF event's magnitude

        min_mag_diff = filtered_df.mag_diff.min()
        filtered_df = filtered_df[filtered_df.mag_diff == min_mag_diff]
        filtered_df.reset_index(drop=True, inplace=True)
        '''

        '''
        Version 2:
        '''
        # Filter 4: Based on duration of usage
        # Take the ON event which closest to the OFF event's timestamp
        min_time_diff = filtered_df.time_diff.min()
        filtered_df = filtered_df[filtered_df.time_diff == min_time_diff]
        filtered_df.reset_index(drop=True, inplace=True)

        if len(filtered_df) == 0:
            return False

        logger.debug("Final set:%s \n", filtered_df)

    on_event_record = new_on_events[new_on_events.id == filtered_df.ix[0]['id']]
    on_event = on_event_record.ix[on_event_record.index[0]]
    return on_event


def match_events(apt_no, off_event):
    """
    Matches the off event with the rise event
    """
    off_time = off_event.event_time
    off_mag = math.fabs(off_event.edge.magnitude)
    off_location = off_event.location
    off_appliance = off_event.appliance

    # Extract rising edges occurring before the fall edge
    # with similar power
    on_events = mod_func.get_on_events(apt_no, off_time)
    if on_events.count() == 0:
        return False

    # Filter i: Remove all on events greater than 24 hours from off event
    new_on_events = []
    for event in on_events:
        on_time = event.event_time
        if (off_time - on_time) < 12 * 60 * 60:
            new_on_events.append(event)

    id_list = []
    mag_diff = []
    location = []
    appliance = []
    event_mag = []
    for on_event in new_on_events:
        id_list.append(on_event.id)
        event_mag.append(on_event.edge.magnitude)
        mag_diff.append(math.fabs(off_mag - on_event.edge.magnitude))
        location.append(on_event.location)
        appliance.append(on_event.appliance)

    df = pd.DataFrame({'id': id_list, 'event_mag': event_mag, 'mag_diff': mag_diff,
                       'location': location, 'appliance': appliance},
                      columns=['id', 'event_mag', 'mag_diff', 'location', 'appliance'])

    # logger.debug("On Events DF: \n%s", df)

    # Get Metadata
    data = mod_func.retrieve_metadata(apt_no)
    metadata_df = read_frame(data, verbose=False)

    # Range of OFF event
    power = off_mag * percent_change
    min_mag = off_mag - power
    max_mag = off_mag + power

    logger.debug("Magnitude::%s per_change: %s", off_mag, power)
    logger.debug("Between min=[%s]  max=[%s]", min_mag, max_mag)

    # Filter 1: Determine if appliance is multi-state
    if func.determine_multi_state(metadata_df, off_location, off_appliance):
        filtered_df = df[(df.location == off_location) &
                         (df.appliance == off_appliance)]
        filtered_df.reset_index(drop=True, inplace=True)

        logger.debug("Filtered on events of a multi-state appl: \n%s", filtered_df)

        if len(filtered_df) == 0:
            return False

        return mod_func.get_on_event_by_id(filtered_df.ix[0]['id'])

    # Filter 2: Match falling with rising edges where its magnitude is between
    # a power threshold window

    filtered_df = df[(df.event_mag >= min_mag) & (df.event_mag <= max_mag)]

    # logger.debug("Filtered on events based on magnitude range: \n%s", filtered_df)

    if len(filtered_df) == 0:
        return False

    # Filter 3: Matching with the same location and appliance
    # if appliance is a presence based appliance

    metadata_df['appliance'] = metadata_df.appliance.apply(lambda s: s.split('_')[0])

    if off_appliance != "Unknown":
        metadata_df = metadata_df[metadata_df.appliance == off_appliance]
        metadata_df = metadata_df.ix[:, ['appliance', 'presence_based']].drop_duplicates()
        metadata_df.reset_index(inplace=True, drop=True)

        if not metadata_df.ix[0]['presence_based']:
            filtered_df = filtered_df[filtered_df.appliance == off_appliance]
        else:
            filtered_df = filtered_df[(filtered_df.location == off_location) &
                                      (filtered_df.appliance == off_appliance)]
    else:
        filtered_df = filtered_df[filtered_df.location == off_location]

    filtered_df.reset_index(drop=True, inplace=True)

    if len(filtered_df) == 0:
        return False

    logger.debug("Matched ON DF:\n%s", filtered_df)

    # Resolve conflicts by --
    # Filter 4: Taking the rising edge which is the closest to the off magnitude

    min_mag_diff = filtered_df.mag_diff.min()
    filtered_df = filtered_df[filtered_df.mag_diff == min_mag_diff]
    filtered_df.reset_index(drop=True, inplace=True)

    if len(filtered_df) == 0:
        return False

    logger.debug("Final set:%s \n", filtered_df)

    return mod_func.get_on_event_by_id(filtered_df.ix[0]['id'])
