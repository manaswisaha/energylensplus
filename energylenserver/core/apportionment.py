import numpy as np

from energylenserver.models.models import EnergyUsageLog, EnergyWastageLog
from energylenserver.models import functions as mod_func

# Enable Logging
from common_imports import *


def get_energy_consumption(start_time, end_time, power):
    """
    Calculates the energy consumption in a given time period
    for the specified power
    """

    return ((end_time - start_time) / 3600) * power


def calculate_consumption(user_list, presence_df, activity):
    """
    Calculates energy usage and wastage for all users
    """
    try:
        user_columns = presence_df.columns - ['start_time', 'end_time']
        col_sum = presence_df.ix[:, user_columns].sum(axis=1, numeric_only=True)
        ts_slices_ix = presence_df.index[np.where(col_sum > 1)[0]]
        time_shared_slices_df = presence_df.ix[ts_slices_ix]
        indiv_slices_df = presence_df.ix[presence_df.index - ts_slices_ix]

        # Energy Usage - for individual slices (not)
        for user in user_list:

            user_id = user.dev_id
            user_column = str(user_id)

            slices = indiv_slices_df[indiv_slices_df[user_column] == 1]

            for idx in slices.index:
                st = slices.ix[ts]['start_time']
                et = slices.ix[ts]['end_time']

                stayed_for = et - st
                usage = stayed_for * activity.power

                # Create usage entry in the log
                # Save Activity
                usage_entry = EnergyUsageLog(activity=activity,
                                             start_time=start_time, end_time=end_time,
                                             stayed_for=stayed_for, usage=usage,
                                             dev_id=user)
                usage_entry.save()
    except Exception, e:
        logger.error("[CalculateConsumpException]:: %s", e)
