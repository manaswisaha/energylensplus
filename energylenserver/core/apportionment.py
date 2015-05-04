import sys
import numpy as np

from energylenserver.models.models import EnergyUsageLog, EnergyWastageLog
from energylenserver.models import functions as mod_func
from constants import wastage_threshold
from energylenserver.common_offline import *

# Enable Logging
from common_imports import *


def get_energy_consumption(start_time, end_time, power):
    """
    Calculates the energy consumption in a given time period
    for the specified power
    """
    energy = round(float(end_time - start_time) / 3600.0, 2) * power
    return energy


def calculate_consumption(user_list, presence_df, activity):
    """
    Calculates energy usage and wastage for all users
    """
    try:
        power = activity.power
        user_columns = presence_df.columns - ['start_time', 'end_time']
        presence_df['user_count'] = presence_df.ix[:, user_columns].sum(axis=1, numeric_only=True)

        time_shared_slices_df = presence_df[presence_df.user_count > 1]

        indiv_slices_df = presence_df.ix[presence_df.index - time_shared_slices_df.index]

        user_list = [mod_func.get_user(int(u)) for u in user_columns]

        # Offline processing - evaluation - START
        apt_no = activity.apt_no
        run_no = read_run_no()
        run_folder = res_folder + "offline/" + run_no

        usage_log = run_folder + '/' + str(apt_no) + '_usageLog.csv'
        wastage_log = run_folder + '/' + str(apt_no) + '_wastageLog.csv'
        # Offline processing - evaluation - END

        # Energy Usage - for individual slices (not shared)
        for user in user_list:

            user_id = user.dev_id
            user_column = str(user_id)

            slices = indiv_slices_df[indiv_slices_df[user_column] == 1]
            logger.debug("[%d] Indiv_slices::\n %s", user_id, slices)

            for idx in slices.index:
                st = slices.ix[idx]['start_time']
                et = slices.ix[idx]['end_time']

                stayed_for = et - st
                usage = get_energy_consumption(st, et, power)

                # logger.debug("User %s Activity: %s, [%s -- %s] stayed for %s used: %s Wh",
                # user, activity, st, et, stayed_for, usage)

                '''
                Commented for offline processing

                # Create usage entry in the log
                usage_entry = EnergyUsageLog(activity=activity,
                                             start_time=st, end_time=et,
                                             stayed_for=stayed_for, usage=usage,
                                             dev_id=user, shared=False)
                usage_entry.save()
                '''

                # Offline processing - evaluation - START
                if not os.path.isfile(usage_log):
                    eval_usage_df = pd.DataFrame({'id': [0], 'apt_no': [apt_no],
                                                  'activity_id': [activity.id],
                                                  'start_time': [st],
                                                  'end_time': [et],
                                                  'stayed_for': [stayed_for], 'usage': [usage],
                                                  'dev_id': [user_id], 'shared': [0]},
                                                 columns=['id', 'apt_no', 'activity_id',
                                                          'start_time', 'end_time',
                                                          'stayed_for', 'usage', 'dev_id',
                                                          'shared'])

                    eval_usage_df.to_csv(usage_log, index=False)
                else:
                    eval_usage_df = pd.read_csv(usage_log)
                    usage_i_df = pd.DataFrame({'id': [len(eval_usage_df)], 'apt_no': [apt_no],
                                               'activity_id': [activity.id],
                                               'start_time': [st],
                                               'end_time': [et],
                                               'stayed_for': [stayed_for], 'usage': [usage],
                                               'dev_id': [user_id], 'shared': [0]},
                                              columns=['id', 'apt_no', 'activity_id',
                                                       'start_time', 'end_time',
                                                       'stayed_for', 'usage', 'dev_id',
                                                       'shared'])

                    eval_usage_df = pd.concat([eval_usage_df, usage_i_df])
                    eval_usage_df.reset_index(drop=True, inplace=True)
                    eval_usage_df.to_csv(usage_log, index=False)
                # Offline processing - evaluation - END

        # Energy Usage - for shared slices
        for idx in time_shared_slices_df.index:

            row = time_shared_slices_df.ix[idx]
            n_users = row['user_count']
            col_idx = np.where((row == 1) == True)[0]
            u_list = time_shared_slices_df.columns[col_idx]
            users = [mod_func.get_user(int(i)) for i in u_list]

            # For each user, create an entry
            for user in users:
                st = row['start_time']
                et = row['end_time']

                stayed_for = et - st
                usage = get_energy_consumption(st, et, power) / n_users

                # Create usage entry in the log
                '''
                Commented for offline processing
                usage_entry = EnergyUsageLog(activity=activity,
                                             start_time=st, end_time=et,
                                             stayed_for=stayed_for, usage=usage,
                                             dev_id=user, shared=True)
                usage_entry.save()
                '''
                # Offline processing - evaluation - START
                if not os.path.isfile(usage_log):
                    eval_usage_df = pd.DataFrame({'id': [0], 'apt_no': [apt_no],
                                                  'activity_id': [activity.id],
                                                  'start_time': [st],
                                                  'end_time': [et],
                                                  'stayed_for': [stayed_for], 'usage': [usage],
                                                  'dev_id': [user.dev_id], 'shared': [1]},
                                                 columns=['id', 'apt_no', 'activity_id',
                                                          'start_time', 'end_time',
                                                          'stayed_for', 'usage', 'dev_id',
                                                          'shared'])

                    eval_usage_df.to_csv(usage_log, index=False)
                else:
                    eval_usage_df = pd.read_csv(usage_log)
                    usage_i_df = pd.DataFrame({'id': [len(eval_usage_df)], 'apt_no': [apt_no],
                                               'activity_id': [activity.id],
                                               'start_time': [st],
                                               'end_time': [et],
                                               'stayed_for': [stayed_for], 'usage': [usage],
                                               'dev_id': [user.dev_id], 'shared': [1]},
                                              columns=['id', 'apt_no', 'activity_id',
                                                       'start_time', 'end_time',
                                                       'stayed_for', 'usage', 'dev_id',
                                                       'shared'])

                    eval_usage_df = pd.concat([eval_usage_df, usage_i_df])
                    eval_usage_df.reset_index(drop=True, inplace=True)
                    eval_usage_df.to_csv(usage_log, index=False)
                # Offline processing - evaluation - END

        # Energy Wastage
        w_slices_ix = presence_df[presence_df.user_count == 0].index
        logger.debug("Wastage Slices:: %s", w_slices_ix)

        # Storing Energy Usage/Wastage in the database
        for idx in w_slices_ix:
            shared = False
            w_entry = presence_df.ix[idx]
            prev_entry = presence_df.ix[idx - 1]   # entry before the wastage period
            n_users = prev_entry['user_count']

            # Checks the room count before the wastage period and determines the person
            # responsible
            if n_users >= 1:
                # Determine who left last
                col_idx = np.where((prev_entry == 1) == True)[0]
                u_list = prev_entry.index[col_idx] - ['user_count']
                users = [mod_func.get_user(int(i)) for i in u_list]

                # Energy Wastage details
                st = w_entry['start_time']
                et = w_entry['end_time']
                left_for = et - st

                usage = get_energy_consumption(st, et, power)
                if n_users > 1:
                    usage /= n_users
                    shared = True

                # For each user who left room empty, create an entry
                for user in users:

                    # If left_for exceeds a threshold period then it is a wastage
                    if left_for >= wastage_threshold:

                        # Create wastage entry in the log
                        '''
                        Commented for offline processing

                        wastage_entry = EnergyWastageLog(activity=activity,
                                                         start_time=st, end_time=et,
                                                         left_for=left_for, wastage=usage,
                                                         dev_id=user)
                        wastage_entry.save()
                        '''
                        # Offline processing - evaluation - START
                        if not os.path.isfile(wastage_log):
                            eval_wastage_df = pd.DataFrame({'id': [0], 'apt_no': [apt_no],
                                                            'activity_id': [activity.id],
                                                            'start_time': [st],
                                                            'end_time': [et],
                                                            'left_for': [left_for],
                                                            'wastage': [usage],
                                                            'dev_id': [user.dev_id]},
                                                           columns=['id', 'apt_no', 'activity_id',
                                                                    'start_time', 'end_time',
                                                                    'left_for', 'wastage',
                                                                    'dev_id'])

                            eval_wastage_df.to_csv(wastage_log, index=False)
                        else:
                            eval_wastage_df = pd.read_csv(wastage_log)
                            wastage_i_df = pd.DataFrame({'id': [len(eval_wastage_df)],
                                                         'apt_no': [apt_no],
                                                         'activity_id': [activity.id],
                                                         'start_time': [st],
                                                         'end_time': [et],
                                                         'left_for': [left_for],
                                                         'wastage': [usage],
                                                         'dev_id': [user.dev_id]},
                                                        columns=['id', 'apt_no', 'activity_id',
                                                                 'start_time', 'end_time',
                                                                 'left_for', 'wastage',
                                                                 'dev_id'])

                            eval_wastage_df = pd.concat([eval_wastage_df, wastage_i_df])
                            eval_wastage_df.reset_index(drop=True, inplace=True)
                            eval_wastage_df.to_csv(wastage_log, index=False)
                        # Offline processing - evaluation - END
                    else:
                        # Declare it as a usage
                        '''
                        Commented for offline processing
                        usage_entry = EnergyUsageLog(activity=activity,
                                                     start_time=st, end_time=et,
                                                     stayed_for=left_for, usage=usage,
                                                     dev_id=user, shared=shared)
                        usage_entry.save()
                        '''

                        # Offline processing - evaluation - START
                        if not os.path.isfile(usage_log):
                            eval_usage_df = pd.DataFrame({'id': [0], 'apt_no': [apt_no],
                                                          'activity_id': [activity.id],
                                                          'start_time': [st],
                                                          'end_time': [et],
                                                          'stayed_for': [stayed_for],
                                                          'usage': [usage],
                                                          'dev_id': [user.dev_id],
                                                          'shared': [int(shared)]},
                                                         columns=['id', 'apt_no', 'activity_id',
                                                                  'start_time', 'end_time',
                                                                  'stayed_for', 'usage', 'dev_id',
                                                                  'shared'])

                            eval_usage_df.to_csv(usage_log, index=False)
                        else:
                            eval_usage_df = pd.read_csv(usage_log)
                            usage_i_df = pd.DataFrame({'id': [len(eval_usage_df)],
                                                       'apt_no': [apt_no],
                                                       'activity_id': [activity.id],
                                                       'start_time': [st],
                                                       'end_time': [et],
                                                       'stayed_for': [stayed_for], 'usage': [usage],
                                                       'dev_id': [user.dev_id],
                                                       'shared': [int(shared)]},
                                                      columns=['id', 'apt_no', 'activity_id',
                                                               'start_time', 'end_time',
                                                               'stayed_for', 'usage', 'dev_id',
                                                               'shared'])

                            eval_usage_df = pd.concat([eval_usage_df, usage_i_df])
                            eval_usage_df.reset_index(drop=True, inplace=True)
                            eval_usage_df.to_csv(usage_log, index=False)
                        # Offline processing - evaluation - END

    except Exception, e:
        logger.exception("[CalculateConsumptionException]:: %s", e)
        sys.exit(0)
        return False
