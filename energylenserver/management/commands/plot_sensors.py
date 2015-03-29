"""
Plot light/accl sensor data with the power data
"""

import sys
import math
import time
from pytz import timezone
import datetime as dt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as md
from django_pandas.io import read_frame


# Django imports
from django.core.management.base import BaseCommand

# EnergyLens+ imports
from common import *
from energylenserver.common_imports import *
from energylenserver.functions import *
from energylenserver.models import functions as mod_func
# from energylenserver.preprocessing import wifi as pre_p

# Enable Logging
logger = logging.getLogger('energylensplus_django')

TIMEZONE = 'Asia/Kolkata'
plt.style.use('ggplot')


def perfect_sq(no):
    sqrt = int(math.sqrt(no))
    if sqrt * sqrt == no:
        return True
    else:
        return False


class Command(BaseCommand):
    help = "Plots sensor data"

    def handle(self, *args, **options):

        try:

            # Get apt info
            m_data = mod_func.retrieve_metadata(apt_no)
            metadata_df = read_frame(m_data, verbose=False)
            rooms = metadata_df.location.unique()
            labels = dict(enumerate(['Empty'] + list(rooms)))
            rooms_dict_val = {v: k for k, v in labels.items()}

            # Get occupant info
            occupants = mod_func.retrieve_users(apt_no)
            occupants_df = read_frame(occupants, verbose=False)

            # Plot sensor data
            start_time = d_times[apt_no]['st_time']
            end_time = d_times[apt_no]['et_time']
            # start_time = int(to_time("10/2/2015T00:00:00"))
            end_time = int(to_time("12/2/2015T09:30:00"))

            for idx_user in occupants_df.index:
                dev_id = occupants_df.ix[idx_user]['dev_id']
                name = occupants_df.ix[idx_user]['name']

                # Get Wifi labeled data
                data = mod_func.get_sensor_data("wifi", start_time, end_time, [dev_id])
                df_orig = read_frame(data, verbose=False)
                pred_labels = df_orig.label.unique()
                self.stdout.write("Predicted labels:: %s" % pred_labels)

                # Localize first if labels are Unknown
                if "none" in pred_labels or "Unknown" in pred_labels:
                    self.stdout.write("Needs localization")

                # Sort, remove duplicates and change index of the original data frame
                df_orig.drop_duplicates('timestamp', take_last=True, inplace=True)
                df_orig.sort(['timestamp'], inplace=True)
                df_orig.timestamp = df_orig.timestamp.astype('int')
                df_orig.set_index("timestamp", inplace=True)
                df_orig['n_label'] = df_orig.label
                df_orig.n_label.replace(rooms_dict_val, inplace=True)

                if "none" in pred_labels or "Unknown" in pred_labels:
                    df_orig.n_label.replace({"none": 0, "Unknown": 0}, inplace=True)

                # self.stdout.write("Frame %s" % df_orig.head(100))

                # Creating plot data frame
                time_range = range(start_time, end_time + 1)
                self.stdout.write("Plotting for %s and %s" %
                                  (time.ctime(start_time), time.ctime(end_time)))
                self.stdout.write("-" * 100)
                plot_df = pd.Series([0] * len(time_range), index=time_range)
                plot_df.update(df_orig.n_label)

                self.stdout.write("Plot draft %s" % plot_df.unique())

                # Plot for n hours at a time
                st = start_time
                hrs = 12 * 60 * 60
                et = st + hrs
                flag = False
                no_sec = end_time - start_time
                no_hrs = int(math.ceil(no_sec / float(hrs)))

                '''
                if no_hrs % 2 == 0:
                    row = no_hrs / 2
                else:
                    row = no_hrs / 2 + 1
                col = 3
                '''

                # '''
                row = int(math.sqrt(no_hrs))
                if perfect_sq(no_hrs):
                    col = int(no_hrs / float(row))
                else:
                    col = int(math.ceil(no_hrs / float(row)) + (no_hrs % 2))
                # '''
                self.stdout.write("Plot variables:: No_hrs: %d R:%d C:%d" % (no_hrs, row, col))

                row_i = 0
                col_i = 0
                plot_i = 1

                '''
                labels_keys = labels.keys()
                min_label = min(labels)
                max_label = max(labels)
                '''

                fig, axes = plt.subplots(row, col, sharey=True)

                min_label = 0
                max_label = len(rooms)
                yticks_array = range(min_label, max_label + 1)

                while et <= end_time:

                    self.stdout.write("Plotting between %s and %s" %
                                      (time.ctime(st), time.ctime(et)))
                    plot_df_i = plot_df.ix[range(st, et + 1)]
                    '''
                    et_i = plot_df_i.index[np.where(plot_df_i != 0)[0][-1]]

                    self.stdout.write("New time range:: %s and %s" %
                                      (time.ctime(st), time.ctime(et_i)))
                    time_range = range(st, et_i + 1)
                    plot_df_i = plot_df_i.ix[time_range]
                    '''

                    # Plot variables

                    self.stdout.write("Plot variables:: R:%d C:%d Plot_i:%d" %
                                      (row_i, col_i, plot_i))

                    # Plot room wise
                    for room_i in reversed(sorted(labels.keys())):
                        if room_i == 0:
                            continue

                        room_idx_list = np.where(plot_df_i == room_i)[0]
                        if len(room_idx_list) == 0:
                            continue
                        start = plot_df_i.index[room_idx_list[0]]
                        end = plot_df_i.index[room_idx_list[-1]]

                        t_range = range(start, end + 1)
                        plot_df_i = plot_df_i.ix[t_range]

                        time_series = [dt.datetime.fromtimestamp(x, timezone(TIMEZONE))
                                       for x in plot_df_i.index]

                        axes[row_i, col_i].plot(time_series, plot_df_i)

                    axes[row_i, col_i].set_title('Apt ' + str(apt_no) + ":: " + name)
                    if col == 0:
                        axes[row_i, col_i].set_ylabel('Presence')
                    axes[row_i, col_i].set_xlabel('Time')
                    axes[row_i, col_i].set_ylim([min_label, max_label + 1])
                    axes[row_i, col_i].set_yticks(yticks_array)
                    axes[row_i, col_i].set_yticklabels(labels.values())
                    # axes[row_i, col_i].set_yticklabels([labels[x] for x in yticks_array])
                    axes[row_i, col_i].xaxis.set_major_formatter(
                        md.DateFormatter('%d-%mT%H:%M', timezone(TIMEZONE)))
                    plt.setp(axes[row_i, col_i].get_xticklabels(), rotation=30, ha='right')
                    # fig.autofmt_xdate()

                    self.stdout.write("Plotting complete")

                    # To break the loop when end time is reached
                    if flag:
                        break

                    # Updating time variables
                    st = et + 1
                    et = st + hrs

                    if et > end_time:
                        et = end_time
                        flag = True

                    self.stdout.write("Next: between %s and %s" %
                                      (time.ctime(st), time.ctime(et)))

                    # Updating plot variable
                    if col_i < col - 1:
                        col_i += 1
                    else:
                        row_i += 1
                        col_i = 0
                    plot_i += 1

                # Show plot in maximized window
                mng = plt.get_current_fig_manager()
                mng.window.showMaximized()
                fig.tight_layout()
                plt.show()

        except KeyboardInterrupt:
            logger.error("Interrupted by user, shutting down..")
            sys.exit(0)
        except Exception, e:
            logger.exception("[PlotSensorDataException] %s" % str(e))
        finally:
            logger.debug("End\n")
            sys.exit(0)
