"""
Edge Matching Module
"""

import math
import numpy as np
import pandas as pd
from django_pandas.io import read_frame

from energylenserver.common_imports import *
from energylenserver.models import functions as mod_func

# Enable Logging
logger = logging.getLogger('energylensplus_django')


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
        if (off_time - on_time) <= 24 * 60 * 60:
            new_on_events.append(event)

    # Filter 1: Match falling with rising edges where its magnitude is between
    # a power threshold window
    power = off_mag * percent_change
    min_mag = off_mag - power
    max_mag = off_mag + power

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

    logger.debug("Magnitude::%s per_change: %s", off_mag, power)
    logger.debug("Between min=[%s]  max=[%s]", min_mag, max_mag)
    # logger.debug("On Events DF: \n%s", df)

    filtered_df = df[(df.event_mag >= min_mag) & (df.event_mag <= max_mag)]

    logger.debug("Filtered on events based on magnitude range: \n%s", filtered_df)

    if len(filtered_df) == 0:
        return False

    # Filter 2: Matching with the same location and appliance
    # if appliance is a presence based appliance

    # Get Metadata
    data = mod_func.retrieve_metadata(apt_no)
    metadata_df = read_frame(data, verbose=False)

    metadata_df['appliance'] = metadata_df.appliance.apply(lambda s: s.split('_')[0])
    metadata_df = metadata_df[metadata_df.appliance == off_appliance]
    metadata_df = metadata_df.ix[:, ['appliance', 'presence_based']].drop_duplicates()
    metadata_df.reset_index(inplace=True, drop=True)

    if not metadata_df.ix[0]['presence_based']:
        filtered_df = filtered_df[filtered_df.appliance == off_appliance]
    else:
        filtered_df = filtered_df[(filtered_df.location == off_location) &
                                  (filtered_df.appliance == off_appliance)]
    filtered_df.reset_index(drop=True, inplace=True)

    if len(filtered_df) == 0:
        return False

    logger.debug("Matched ON DF:\n%s", filtered_df)

    # Resolve conflicts by --
    # Filter 3: Taking the rising edge which is the closest to the off magnitude

    min_mag_diff = filtered_df.mag_diff.min()
    filtered_df = filtered_df[filtered_df.mag_diff == min_mag_diff]

    if len(filtered_df) == 0:
        return False

    logger.debug("Final set:%s \n", filtered_df)

    return mod_func.get_on_event_by_id(filtered_df.ix[0]['id'])
