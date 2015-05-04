"""
Plot light/accl sensor data with the power data
"""
import os
import sys
import time
import fnmatch
import shutil
'''
import pandas as pd
import datetime as dt
from django_pandas.io import read_frame
'''

# Django imports
# from django.conf import settings
from django.core.management.base import BaseCommand

# EnergyLens+ imports
from common import *
from energylenserver.common_imports import *
from energylenserver.models import functions as mod_func
from energylenserver.tasks import edgeHandler as v1
from energylenserver.version_2 import edgeHandler as v2
from energylenserver.models.models import *

# Enable Logging
logger = logging.getLogger('energylensplus_django')


class Command(BaseCommand):
    help = "For offline processing"

    def handle(self, *args, **options):
        """
        This command is used for offline processing of the data
        """

        try:
            run_no = args[0]
            remove_missed = False  # To include missed events (False) or not (True)

            '''
            Cleanup
            '''
            # Empty Log file
            django_log = '/energylens.log'
            main_logfile = base_dir + "/logs" + django_log
            with open(main_logfile, "w"):
                pass

            self.stdout.write("Run %s started at %s...." % (run_no, time.ctime(time.time())))
            # Run folder
            folder = os.path.join(base_dir, 'results/')

            cfile = folder + "current.txt"
            rfile = folder + "missed.txt"

            f = open(cfile, 'w')
            f.write(run_no)
            f.close()

            f = open(rfile, 'w')
            f.write(str(remove_missed))
            f.close()

            run_folder = folder + "offline/" + run_no
            if not os.path.exists(run_folder):
                # Create run folder
                os.makedirs(run_folder)
                self.stdout.write("Folder created: %s" % run_folder)

            '''
            Start offline processing for each apartment
            '''
            # for apt_no in apt_no_list:
            for apt_no in [103]:

                # Empty files related to the apt_no
                files = os.listdir(run_folder)
                sub_str = str(apt_no) + '_' + '*'
                filtered_files = fnmatch.filter(files, sub_str)
                for the_file in filtered_files:
                    file_path = os.path.join(run_folder, the_file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                        # elif os.path.isdir(file_path): shutil.rmtree(file_path)
                    except Exception, e:
                        print e
                self.stdout.write("Folder emptied for apartment %s" % apt_no)

                # Create gt_eventlog -- ground truth event log
                gt_folder = os.path.join(base_dir, 'ground_truth/')
                gt_file = gt_folder + str(apt_no) + '.csv'
                gt_df = pd.read_csv(gt_file)

                # Event and activity logs
                gt_evlog_file = gt_folder + str(apt_no) + '_eventlog.csv'
                gt_activitylog_file = gt_folder + str(apt_no) + '_activitylog.csv'

                if remove_missed:
                    gt_df = gt_df[(gt_df.st_missed != 1) & (gt_df.et_missed != 1)]
                    gt_df.reset_index(drop=True, inplace=True)

                    gt_evlog_file = gt_folder + str(apt_no) + '_missed_eventlog.csv'
                    gt_activitylog_file = gt_folder + str(apt_no) + '_missed_activitylog.csv'

                if not os.path.isfile(gt_activitylog_file):
                    create_gt_activity_log(gt_df, gt_activitylog_file)
                if not os.path.isfile(gt_evlog_file):
                    create_gt_event_log(gt_df, gt_evlog_file)

                self.stdout.write(
                    "Removed missed events. Total number of activities: %s" % len(gt_df))

                # Presence log
                presence_log_file = gt_folder + str(apt_no) + '_presencelog.txt'
                if not os.path.isfile(presence_log_file):
                    create_presence_log(apt_no, presence_log_file)

                start_run_time = time.time()
                # Get meter edges
                meters = mod_func.retrieve_meter_info(apt_no)
                meter_uuid_list = []
                for meter in meters:
                    meter_uuid_list.append(meter['uuid'])
                edges = Edges.objects.filter(timestamp__gte=d_times[apt_no]['st_time'],
                                             timestamp__lte=d_times[apt_no]['et_time'],
                                             # timestamp__lte=1422849360,
                                             meter_id__in=meter_uuid_list).order_by('timestamp')

                # Start offline processing of edges
                for edge in edges:
                    # if int(run_no) == 5:
                    #     v2(edge)
                    # else:
                    v1(edge)

                end_run_time = time.time()
                self.stdout.write("Started at %s" % time.ctime(start_run_time))
                self.stdout.write("Finished at %s" % time.ctime(end_run_time))

                time_taken = end_run_time - start_run_time

                time_unit = "seconds"
                if time_taken >= 60:
                    time_taken /= 60
                    time_unit = "minutes"
                time_taken = round(time_taken, 2)
                self.stdout.write("Total time taken for a single run (Run %s): %s %s" %
                                  (run_no, time_taken, time_unit))

                # Copy django log file in the resp. run folder
                run_logfile = run_folder + django_log
                open(run_logfile, 'a').close()
                shutil.copyfile(main_logfile, run_logfile)

                # sys.exit(0)

                # Call evaluation programs
                calculate_accuracy_summary(apt_no, run_no, remove_missed, time_taken)

        except KeyboardInterrupt:
            self.stdout.write("Interrupted by user, shutting down..")
            sys.exit(0)
        except Exception, e:
            logger.exception("[OfflineProcessingException] %s" % str(e))
            # self.stderr.write("[OfflineProcessingException] %s" % e)
