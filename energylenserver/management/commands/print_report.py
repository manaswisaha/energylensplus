"""
Generate reports and print it
"""

import os
import sys

# Django imports
from django.core.management.base import BaseCommand

# EnergyLens+ imports
from common import *
from django.conf import settings
from energylenserver.common_imports import *
# from energylenserver.models import functions as mod_func

# Enable Logging
logger = logging.getLogger('energylenserver')

base_dir = settings.BASE_DIR
gt_folder = os.path.join(base_dir, 'ground_truth/')


class Command(BaseCommand):
    help = "Generates reports"

    def handle(self, *args, **options):
        """
        This command is used to generate csv reports for the deployment period for an apartment
        """

        try:

            # base_dir = settings.BASE_DIR
            # folder = os.path.join(base_dir, 'results/')

            run_no = args[0]
            apt_no = 103
            remove_missed = False

            if run_no == '1':
                running_time = 37.03
            elif run_no == '3':
                running_time = round(35.5586681843, 2)

            # Presence log
            presence_log_file = gt_folder + str(apt_no) + '_presencelog.txt'
            if not os.path.isfile(presence_log_file):
                create_presence_log(apt_no, presence_log_file)

            # sys.exit(0)

            calculate_accuracy_summary(apt_no, run_no, remove_missed, running_time)
        except KeyboardInterrupt:
            self.stdout.write("Interrupted by user, shutting down..")
            sys.exit(0)
        except Exception, e:
            self.stderr.write("[ReportGenerationException] %s" % e)
            logger.exception("[ReportGenerationException] %s" % e)
