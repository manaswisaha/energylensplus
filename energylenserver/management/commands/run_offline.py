"""
Plot light/accl sensor data with the power data
"""
import os
import sys
import time
'''
import pandas as pd
import datetime as dt
from django_pandas.io import read_frame
'''

# Django imports
from django.conf import settings
from django.core.management.base import BaseCommand

# EnergyLens+ imports
from common import *
from energylenserver.common_imports import *
from energylenserver.models import functions as mod_func
from energylenserver.tasks import edgeHandler
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
            apt_no = 103
            remove_missed = False  # To include missed events or not

            self.stdout.write("Run %s started...." % run_no)
            # Run
            base_dir = settings.BASE_DIR
            folder = os.path.join(base_dir, 'results/')

            cfile = folder + "current.txt"

            # if os.path.isfile(cfile):
            f = open(cfile, 'w')
            f.write(run_no)
            f.close()

            # Create run folder
            run_folder = folder + "offline/" + run_no
            if not os.path.exists(run_folder):
                os.makedirs(run_folder)
                self.stdout.write("Folder created: %s" % run_folder)

            # Create gt_eventlog -- ground truth event log
            gt_folder = os.path.join(base_dir, 'ground_truth/')
            gt_file = gt_folder + str(apt_no) + '.csv'
            gt_df = pd.read_csv(gt_file)

            # Event and activity logs
            gt_evlog_file = gt_folder + str(apt_no) + '_eventlog.csv'
            gt_activitylog_file = gt_folder + str(apt_no) + '_activitylog.csv'

            if not os.path.isfile(gt_activitylog_file):
                create_gt_activity_log(gt_df, gt_activitylog_file)
            if not os.path.isfile(gt_evlog_file):
                create_gt_event_log(gt_df, gt_evlog_file)

            start_run_time = time.time()
            self.stdout.write("Started at %s" % time.ctime(start_run_time))
            # Get meter edges
            meters = mod_func.retrieve_meter_info(apt_no)
            meter_uuid_list = []
            for meter in meters:
                meter_uuid_list.append(meter['uuid'])
            edges = Edges.objects.filter(timestamp__gte=d_times[apt_no]['st_time'],
                                         timestamp__lte=d_times[apt_no]['et_time'],
                                         meter_id__in=meter_uuid_list)

            # Start offline processing of edges
            for edge in edges:
                edgeHandler(edge)

            end_run_time = time.time()
            self.stdout.write("Finished at %s" % time.ctime(end_run_time))
            self.stdout.write("Total time taken for a single run (Run %s): %s seconds" %
                              (run_no, (end_run_time - start_run_time)))

            sys.exit(0)

            # Call evaluation programs
            result = calculate_accuracy_summary(apt_no, run_no, remove_missed)
            self.stdout.write("Results:: \n %s...." % result)

        except KeyboardInterrupt:
            self.stdout.write("Interrupted by user, shutting down..")
            sys.exit(0)
        except Exception, e:
            logger.exception("[OfflineProcessingException] %s" % str(e))
            # self.stderr.write("[OfflineProcessingException] %s" % e)
