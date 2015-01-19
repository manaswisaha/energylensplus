"""
Plot light/accl sensor data with the power data
"""

import os
import sys
import pandas as pd

# Django imports
from django.core.management.base import BaseCommand

# EnergyLens+ imports
from energylenserver.common_imports import *
from django.conf import settings
from energylenserver.models.models import Metadata


class Command(BaseCommand):
    help = "Validates training data"

    def handle(self, *args, **options):
        """
        This command will be used to enter metadata manually for
        appliances that are not initiated by the user
        """

        try:

            apt_no = int(args[0])
            self.stdout.write("Metadata creation for '%s' started" % apt_no)

            # Read metadata file
            base_dir = settings.BASE_DIR
            folder = os.path.join(base_dir, 'energylenserver/metadata/')
            m_metadata_df = pd.read_csv(folder + 'metadata.csv')

            md_df = m_metadata_df[m_metadata_df.apt_no == apt_no]

            for idx in md_df.index:
                entry = md_df.ix[idx]
                location = entry['location']
                appliance = entry['appliance']
                power = float(entry['power'])
                audio_based = bool(int(entry['audio_based']))
                presence_based = bool(int(entry['presence_based']))
                how_many = int(entry['how_many'])

                self.stdout.write("Location: %s -- Appliance: %s" % (location, appliance))

                # See if entry exists for appliance-location combination
                # Update power value if it exists
                try:
                    # Update power
                    records = Metadata.objects.filter(apt_no__exact=apt_no,
                                                      location__exact=location,
                                                      appliance__exact=appliance,
                                                      presence_based=presence_based,
                                                      audio_based=audio_based)
                    if records.count() == 1:
                        if how_many > records[0].how_many:
                            records.update(how_many=how_many)
                        else:
                            records.update(power=power)
                        self.stdout.write(
                            "Metadata with entry: %d %s %s exists" % (apt_no, appliance, location))
                        self.stdout.write("Metadata record updated")
                    else:
                        # Store metadata
                        metadata = Metadata(apt_no=apt_no,
                                            presence_based=presence_based, audio_based=audio_based,
                                            appliance=appliance, location=location, power=power,
                                            how_many=how_many)
                        metadata.save()
                        self.stdout.write("Metadata creation successful")
                except Metadata.DoesNotExist, e:

                    # Store metadata
                    metadata = Metadata(apt_no=apt_no,
                                        presence_based=presence_based, audio_based=audio_based,
                                        appliance=appliance, location=location, power=power,
                                        how_many=how_many)
                    metadata.save()
                    self.stdout.write("Metadata creation successful")

        except KeyboardInterrupt:
            self.stdout.write("Interrupted by user, shutting down..")
            sys.exit(0)
        except Exception, e:
            self.stderr.write("[MetadataEntryException] %s" % e)
