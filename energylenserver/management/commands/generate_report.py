"""
Plot light/accl sensor data with the power data
"""

import os
import sys
import time
import pandas as pd
import datetime as dt
from django_pandas.io import read_frame

# Django imports
from django.db.models import Q
from django.conf import settings
from django.core.management.base import BaseCommand

# EnergyLens+ imports
from common import *
from energylenserver.common_imports import *
from energylenserver.models import functions as mod_func
from energylenserver.models.models import GroundTruthLog, ActivityLog, EventLog
# from energylenserver.models.models import EnergyUsageLog, EnergyWastageLog


class Command(BaseCommand):
    help = "Generates reports"

    def handle(self, *args, **options):
        """
        This command is used to generate csv reports for the deployment period for an apartment
        """

        try:

            base_dir = settings.BASE_DIR
            folder = os.path.join(base_dir, 'results/')

            for apt_no in apt_no_list:
                self.stdout.write("\nReport generation for '%s' started" % apt_no)

                # Get users
                user_records = mod_func.retrieve_users(apt_no)

                # Get meter uuid
                meters = mod_func.retrieve_meter_info(apt_no)

                # Get reports from ground truth log and correlate with activity log
                # and get a consolidated report per user with foll. fields:
                # act_id, location, appliance, power, time spent, energy_used, energy wasted

                # st_time = 1422210600
                # et_time = 1424172600

                activities = []
                for meter_i in meters:
                    uuid = meter_i['uuid']

                    activities_df = read_frame(ActivityLog.objects.filter(meter_id=uuid,
                                                                          start_time__gte=d_times[
                                                                              apt_no]['st_time'],
                                                                          end_time__lte=d_times[
                                                                              apt_no]['et_time']),
                                               verbose=False)
                    activities.append(activities_df)
                activities_df = pd.concat(activities)
                activities_df['start_time'] = [
                    dt.datetime.fromtimestamp(i) for i in activities_df['start_time']]
                activities_df['end_time'] = [
                    dt.datetime.fromtimestamp(i) for i in activities_df['end_time']]
                activities_df['correct'] = [0] * len(activities_df)

                filename = folder + str(apt_no) + ".csv"
                # new_a_df = activities_df.ix[:, activities_df.columns - ['meter', 'start_event',
                #                                                         'end_event', 'report_sent']]
                # new_a_df.to_csv(filename, index=False)

                t_events = EventLog.objects.filter(
                    apt_no=apt_no,
                    event_time__gte=d_times[apt_no]['st_time'],
                    event_time__lte=d_times[apt_no]['et_time']
                ).count()
                act_events = EventLog.objects.filter(~Q(location="Unknown"),
                                                     ~Q(appliance="Unknown"),
                                                     apt_no=apt_no,
                                                     event_time__gte=d_times[apt_no]['st_time'],
                                                     event_time__lte=d_times[apt_no]['et_time']
                                                     ).count()
                missed_events = EventLog.objects.filter(Q(location="Unknown"),
                                                        Q(appliance="Unknown"),
                                                        apt_no=apt_no,
                                                        event_time__gte=d_times[apt_no]['st_time'],
                                                        event_time__lte=d_times[apt_no]['et_time']
                                                        ).count()

                filename = folder + "n_" + str(apt_no) + ".csv"
                df = pd.read_csv(filename)
                accurate_entries = df.correct.sum()

                self.stdout.write("Number of all events for %d:: %d" %
                                  (apt_no, t_events))
                self.stdout.write("Number of actual events for %d:: %d" %
                                  (apt_no, act_events))
                self.stdout.write("Number of missed events for %d:: %d" %
                                  (apt_no, missed_events))
                self.stdout.write("Number of inferred activities for %d:: %d" %
                                  (apt_no, len(activities_df)))
                self.stdout.write("Number of accurate inferred activities for %d:: %d" %
                                  (apt_no, accurate_entries))

                gt_log = []
                for user in user_records:
                    user_id = user.dev_id
                    gt_df = read_frame(GroundTruthLog.objects.filter(
                        by_dev_id=user_id,
                        start_time__gte=d_times[apt_no]['st_time'],
                        end_time__lte=d_times[apt_no]['et_time']), verbose=False)
                    gt_log.append(gt_df)

                gt_df = pd.concat(gt_log)
                self.stdout.write(
                    "Number of automatically logged activities for %d:: %d" % (apt_no, len(gt_df)))

                # select * from activitylog where start_time >= 1422729000 and
                # start_time <= 1423744200 and
                # meter_id in (select meter_uuid from meterinfo where apt_no=103)

                # self.stdout.write(
                #     "Number of automatically logged activities for %d:: %d" %
                # (apt_no, len(gt_df)))

        except KeyboardInterrupt:
            self.stdout.write("Interrupted by user, shutting down..")
            sys.exit(0)
        except Exception, e:
            self.stderr.write("[ReportGenerationException] %s" % e)
