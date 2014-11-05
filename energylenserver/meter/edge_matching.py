"""
Edge Matching Module
"""

import numpy as np
import pandas as pd

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

    # Filter 1: Match falling with rising edges where its magnitude is between
    # a power threshold window
    power = off_mag * percent_change
    min_mag = off_mag - power
    max_mag = off_mag - power

    filtered_on_events = [{'id': on_event.id, 'mag_diff': math.fabs(off_mag -
                                                                    on_events.edge.magnitude),
                           'location': on_event.location, 'appliance': on_event.appliance}
                          for on_event in on_events
                          if on_events.edge.magnitude >= min_mag
                          and on_events.edge.magnitude <= max_mag]
    logger.debug("Filtered on events based on magnitude range: %s", filtered_on_events)

    # Resolve conflicts by --
    # Filter 2: Taking the rising edge which is the closest to the off magnitude

    id_list = []
    mag_diff = []
    location = []
    appliance = []
    for event in filtered_on_events:
        id_list.append(event.get('id'))
        mag_diff.append(event.get('mag_diff'))
        location.append(event.get('location'))
        appliance.append(event.get('appliance'))

    filtered_df = pd.DataFrame({'id': id_list, 'mag_diff': mag_diff,
                                'location': location, 'appliance': appliance})
    min_mag_diff = filtered_df.mag_diff.min()
    filtered_df = filtered_df.ix[np.where(filtered_df.mag_diff == min_mag_diff)[0]]

    logger.debug("Matched ON DF:%s \n", filtered_df)

    # Filter 3: Matching with the same location and appliance
    filtered_df = filtered_df[(filtered_df.location == off_location) &
                              (filtered_df.appliance == off_appliance)]
    filtered_df.reset_index(inplace=True)

    if len(filtered_df) == 0:
        return False

    logger.debug("Final set:%s \n", filtered_df)

    return mod_func.get_on_event_by_id(filtered_df.ix[0]['id'])
