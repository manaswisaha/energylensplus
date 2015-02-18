from decimal import getcontext
getcontext().prec = 14

import os
from django.db import models
from django.db import connection

from models import RegisteredUsers
import logging

# Enable Logging
logger = logging.getLogger('energylensplus_django')

"""
Models for storing phone sensor data
"""


class SensorData(models.Model):
    timestamp = models.DecimalField(unique=False, max_digits=14, decimal_places=3)
    dev_id = models.ForeignKey(RegisteredUsers)

    class Meta:
        abstract = True
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']


# Accelerometer


class AcclData(SensorData):
    x_value = models.FloatField()
    y_value = models.FloatField()
    z_value = models.FloatField()
    label = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    def insert_records(self, user, filename, model):
        """
        Inserts csv into the database directly
        """
        try:
            cursor = connection.cursor()

            records_inserted = cursor.execute("LOAD DATA LOCAL INFILE %s INTO TABLE " + model +
                                              " FIELDS TERMINATED BY ',' IGNORE 1 LINES "
                                              "(@timestamp, x_value, y_value, z_value,"
                                              " label, location) "
                                              "SET timestamp = @timestamp/1000.0, "
                                              "dev_id_id = " + str(user.dev_id), [filename])
            # logger.debug("Number of records inserted: %d", records_inserted)
        except Exception, e:
            logger.error("[FileSaveException] AcclData::%s", str(e))
        os.remove(filename)

    class Meta(SensorData.Meta):
        abstract = True
        app_label = 'energylenserver'


class AcclTrainData(AcclData):

    class Meta(AcclData.Meta):
        db_table = 'accltraindata'
        app_label = 'energylenserver'


class AcclTestData(AcclData):

    class Meta(AcclData.Meta):
        db_table = 'accltestdata'
        app_label = 'energylenserver'
# '''
# WiFi


class WiFiData(SensorData):
    macid = models.CharField(max_length=200)
    ssid = models.CharField(max_length=200)
    rssi = models.IntegerField()
    label = models.CharField(max_length=200)

    def insert_records(self, user, filename, model):
        """
        Inserts csv into the database directly
        """
        try:
            cursor = connection.cursor()

            records_inserted = cursor.execute("LOAD DATA LOCAL INFILE %s INTO TABLE " + model +
                                              " FIELDS TERMINATED BY ',' IGNORE 1 LINES "
                                              "(timestamp, macid, ssid, rssi, label) "
                                              "SET dev_id_id = " + str(user.dev_id), [filename])
            # logger.debug("Number of records inserted: %d", records_inserted)
            os.remove(filename)
        except Exception, e:
            logger.error("[FileSaveException] WiFiData::%s", str(e))

    class Meta(SensorData.Meta):
        abstract = True
        app_label = 'energylenserver'


class WiFiTrainData(WiFiData):

    class Meta(WiFiData.Meta):
        db_table = 'wifitraindata'
        app_label = 'energylenserver'


class WiFiTestData(WiFiData):

    class Meta(WiFiData.Meta):
        db_table = 'wifitestdata'
        app_label = 'energylenserver'

# Audio


class RawAudioData(SensorData):
    value = models.TextField()
    label = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    def insert_records(self, user, filename, model):
        """
        Inserts csv into the database directly
        """
        try:
            cursor = connection.cursor()

            records_inserted = cursor.execute("LOAD DATA LOCAL INFILE %s INTO TABLE " + model +
                                              " FIELDS TERMINATED BY ','"
                                              " OPTIONALLY ENCLOSED BY '`' IGNORE 1 LINES"
                                              " (@timestamp, value, label, location) "
                                              "SET timestamp = @timestamp/1000.0, "
                                              "dev_id_id = " + str(user.dev_id), [filename])
            # logger.debug("Number of records inserted: %d", records_inserted)
            os.remove(filename)
        except Exception, e:
            logger.error("[FileSaveException] RawAudioData::%s", str(e))

    class Meta(SensorData.Meta):
        abstract = True
        app_label = 'energylenserver'


class RawAudioTrainData(RawAudioData):

    class Meta(RawAudioData.Meta):
        db_table = 'rawaudiotraindata'
        app_label = 'energylenserver'


class RawAudioTestData(RawAudioData):

    class Meta(RawAudioData.Meta):
        db_table = 'rawaudiotestdata'
        app_label = 'energylenserver'


class MFCCFeatureSet(SensorData):
    mfcc1 = models.FloatField()
    mfcc2 = models.FloatField()
    mfcc3 = models.FloatField()
    mfcc4 = models.FloatField()
    mfcc5 = models.FloatField()
    mfcc6 = models.FloatField()
    mfcc7 = models.FloatField()
    mfcc8 = models.FloatField()
    mfcc9 = models.FloatField()
    mfcc10 = models.FloatField()
    mfcc11 = models.FloatField()
    mfcc12 = models.FloatField()
    mfcc13 = models.FloatField()
    label = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    def insert_records(self, user, filename, model):
        """
        Inserts csv into the database directly
        """
        try:
            cursor = connection.cursor()

            records_inserted = cursor.execute("LOAD DATA LOCAL INFILE %s INTO TABLE " + model +
                                              " FIELDS TERMINATED BY ',' IGNORE 1 LINES "
                                              "(@timestamp, mfcc1, mfcc2, mfcc3, mfcc4, "
                                              "mfcc5, mfcc6, mfcc7, mfcc8, mfcc9, mfcc10, "
                                              "mfcc11, mfcc12, mfcc13, label, location) "
                                              "SET timestamp = @timestamp/1000.0, "
                                              " dev_id_id = " + str(user.dev_id), [filename])
            # logger.debug("Number of records inserted: %d", records_inserted)
            os.remove(filename)

        except Exception, e:
            logger.error("[FileSaveException] MFCCFeatureSet::%s", str(e))

    class Meta(SensorData.Meta):
        abstract = True
        app_label = 'energylenserver'


class MFCCFeatureTrainSet(MFCCFeatureSet):

    class Meta(MFCCFeatureSet.Meta):
        db_table = 'mfccfeaturetrainset'
        app_label = 'energylenserver'


class MFCCFeatureTestSet(MFCCFeatureSet):

    class Meta(MFCCFeatureSet.Meta):
        db_table = 'mfccfeaturetestset'
        app_label = 'energylenserver'

# Light Sensor


class LightData(SensorData):
    value = models.FloatField()
    label = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    def insert_records(self, user, filename, model):
        """
        Inserts csv into the database directly
        """
        try:
            cursor = connection.cursor()

            records_inserted = cursor.execute("LOAD DATA LOCAL INFILE %s INTO TABLE " + model +
                                              " FIELDS TERMINATED BY ',' IGNORE 1 LINES "
                                              "(@timestamp, value, label, location) "
                                              "SET timestamp = @timestamp/1000.0, "
                                              " dev_id_id = " + str(user.dev_id), [filename])
            # logger.debug("Number of records inserted: %d", records_inserted)
            os.remove(filename)
        except Exception, e:
            logger.error("[FileSaveException] LightData::%s", str(e))

    class Meta(SensorData.Meta):
        abstract = True
        app_label = 'energylenserver'


class LightTrainData(LightData):

    class Meta(LightData.Meta):
        db_table = 'lighttraindata'
        app_label = 'energylenserver'


class LightTestData(LightData):

    class Meta(LightData.Meta):
        db_table = 'lighttestdata'
        app_label = 'energylenserver'

# Magnetometer


class MagData(SensorData):
    x_value = models.FloatField()
    y_value = models.FloatField()
    z_value = models.FloatField()
    label = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    def insert_records(self, user, filename, model):
        """
        Inserts csv into the database directly
        """
        try:
            cursor = connection.cursor()

            records_inserted = cursor.execute("LOAD DATA LOCAL INFILE %s INTO TABLE " + model +
                                              " FIELDS TERMINATED BY ',' IGNORE 1 LINES "
                                              "(@timestamp, x_value, y_value, z_value, "
                                              "label, location) "
                                              "SET timestamp = @timestamp/1000.0, "
                                              " dev_id_id = " + str(user.dev_id), [filename])
            # logger.debug("Number of records inserted: %d", records_inserted)
            os.remove(filename)
        except Exception, e:
            logger.error("[FileSaveException] MagData::%s", str(e))

    class Meta(SensorData.Meta):
        abstract = True
        app_label = 'energylenserver'


class MagTrainData(MagData):

    class Meta(MagData.Meta):
        db_table = 'magtraindata'
        app_label = 'energylenserver'


class MagTestData(MagData):

    class Meta(MagData.Meta):
        db_table = 'magtestdata'
        app_label = 'energylenserver'
# '''
