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
        power = activity.power
        user_columns = presence_df.columns - ['start_time', 'end_time']
        col_sum = presence_df.ix[:, user_columns].sum(axis=1, numeric_only=True)
        ts_slices_ix = presence_df.index[np.where(col_sum > 1)[0]]
        time_shared_slices_df = presence_df.ix[ts_slices_ix]
        time_shared_slices_df['sum'] = col_sum
        presence_df['sum'] = col_sum

        indiv_slices_df = presence_df.ix[presence_df.index - ts_slices_ix]

        # Energy Usage - for individual slices (not shared)
        for user in user_list:

            user_id = user.dev_id
            user_column = str(user_id)

            slices = indiv_slices_df[indiv_slices_df[user_column] == 1]

            for idx in slices.index:
                st = slices.ix[idx]['start_time']
                et = slices.ix[idx]['end_time']

                stayed_for = et - st
                usage = get_energy_consumption(st, et, power)

                # Create usage entry in the log
                # Save Activity
                usage_entry = EnergyUsageLog(activity=activity,
                                             start_time=start_time, end_time=end_time,
                                             stayed_for=stayed_for, usage=usage,
                                             dev_id=user)
                usage_entry.save()

        # Energy Usage - for shared slices
        for idx in time_shared_slices_df.index:

            row = time_shared_slices_df.ix[idx]
            n_users = row['sum']
            col_idx = np.where((row == 1) is True)[0]
            u_list = time_shared_slices_df.columns[col_idx]
            users = [mod_func.get_user(int(i)) for i in u_list]

            # For each user, create an entry
            for user in users:
                st = row['start_time']
                et = row['end_time']

                stayed_for = et - st
                usage = get_energy_consumption(st, et, power) / n_users

                # Create usage entry in the log
                # Save Activity
                usage_entry = EnergyUsageLog(activity=activity,
                                             start_time=start_time, end_time=end_time,
                                             stayed_for=stayed_for, usage=usage,
                                             dev_id=user, shared=True)
                usage_entry.save()

        # Energy Wastage
        w_slices_ix = presence_df.index[np.where(col_sum == 0)[0]]

        for idx in w_slices_ix:
            w_idx = np.where(presence_df.index == idx)[0] - 1
            row = presence_df.ix[w_idx]
            if row['sum'] == 1:
                # Determine who left last
                col_idx = np.where((row == 1) is True)[0][:-1]  # Exclude sum column
                u_list = presence_df.columns[col_idx]
                users = [mod_func.get_user(int(i)) for i in u_list]
                n_users = len(u_list)

                # For each user who left room empty, create an entry
                for user in users:
                    st = row['start_time']
                    et = row['end_time']

                    left_for = et - st
                    if n_users > 1:
                        usage = get_energy_consumption(st, et, power) / n_users
                    else:
                        usage = get_energy_consumption(st, et, power)

                    # Create usage entry in the log
                    # Save log
                    wastage_entry = EnergyWastageLog(activity=activity,
                                                     start_time=start_time, end_time=end_time,
                                                     left_for=left_for, usage=usage,
                                                     dev_id=user, shared=True)
                    wastage_entry.save()

    except Exception, e:
        logger.error("[CalculateConsumptionException]:: %s", e)
        return False
