from django.db import models
from models import RegisteredUsers

import datetime as dt
from decimal import getcontext
getcontext().prec = 14

# TODO: Add the foreign key to gcm.models.reg_id (See ForeignKey.to_field in the documentation)

"""
Helper functions
"""


def modify_time(time):
    return dt.datetime.fromtimestamp(time)

"""
Models for storing phone sensor data
"""


class SensorData(models.Model):
    # timestamp = UnixTimestampField('date uploaded', unique=True)
    timestamp = models.DecimalField(unique=False, max_digits=14, decimal_places=3)
    time = models.DateTimeField('date uploaded')
    dev_id = models.ForeignKey(RegisteredUsers)

    def save_data(self, dev_id, data_list):
        time = data_list[0] / 1000.
        self.dev_id = dev_id
        self.timestamp = time
        self.time = modify_time(time)

    class Meta:
        abstract = True
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']

# WiFi


class WiFiData(SensorData):
    macid = models.CharField(max_length=200)
    ssid = models.CharField(max_length=200)
    rssi = models.IntegerField()
    label = models.CharField(max_length=200)
    # reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    def save_data(self, dev_id, data_list):
        super(WiFiData, self).save_data(self, dev_id, data_list)
        self.macid = data_list[1]
        self.ssid = data_list[2]
        self.rssi = data_list[3]
        self.label = data_list[4]

        if self.pk is not None:
            self.pk = self.pk + 1

        # print "Data Received:", data_list

        try:
            self.save(force_insert=True)
            # print "PK::", self.pk
            # TODO: How to check if record is saved?
            return True
        except Exception, e:
            print e

    class Meta(SensorData.Meta):
        abstract = True
        app_label = 'energylenserver'


class WiFiTrainData(WiFiData):

    class Meta(WiFiData.Meta):
        db_table = 'WiFiTrainData'
        app_label = 'energylenserver'


class WiFiTestData(WiFiData):

    class Meta(WiFiData.Meta):
        db_table = 'WiFiTestData'
        app_label = 'energylenserver'

# Audio


class RawAudioData(SensorData):
    values = models.TextField()
    label = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    # reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    def save_data(self, dev_id, data_list):
        super(RawAudioData, self).save_data(dev_id, data_list)
        self.values = data_list[1]
        self.label = data_list[2]
        self.location = data_list[3]

        if self.pk is not None:
            self.pk = self.pk + 1

        # print "Data Received:", data_list

        # try:
        self.save(force_insert=True)
        # print "PK::", self.pk

        # TODO: How to check if record is saved?
        return True
        # except Exception, e:
        #     print e

    class Meta(SensorData.Meta):
        abstract = True
        app_label = 'energylenserver'


class RawAudioTrainData(RawAudioData):

    class Meta(RawAudioData.Meta):
        db_table = 'RawAudioTrainData'
        app_label = 'energylenserver'


class RawAudioTestData(RawAudioData):

    class Meta(RawAudioData.Meta):
        db_table = 'RawAudioTestData'
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
    # reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    def save_data(self, dev_id, data_list):
        super(MFCCFeatureSet, self).save_data(dev_id, data_list)
        self.mfcc1 = data_list[1]
        self.mfcc2 = data_list[2]
        self.mfcc3 = data_list[3]
        self.mfcc4 = data_list[4]
        self.mfcc5 = data_list[5]
        self.mfcc6 = data_list[6]
        self.mfcc7 = data_list[7]
        self.mfcc8 = data_list[8]
        self.mfcc9 = data_list[9]
        self.mfcc10 = data_list[10]
        self.mfcc11 = data_list[11]
        self.mfcc12 = data_list[12]
        self.mfcc13 = data_list[13]
        self.label = data_list[14]
        self.location = data_list[15]

        if self.pk is not None:
            self.pk = self.pk + 1

        print "Data Received:", data_list

        try:
            self.save(force_insert=True)
            print "PK::", self.pk
            # TODO: How to check if record is saved?
            return True
        except Exception, e:
            print e

    class Meta(SensorData.Meta):
        abstract = True
        app_label = 'energylenserver'


class MFCCFeatureTrainSet(MFCCFeatureSet):

    class Meta(MFCCFeatureSet.Meta):
        db_table = 'MFCCFeatureTrainSet'
        app_label = 'energylenserver'


class MFCCFeatureTestSet(MFCCFeatureSet):

    class Meta(MFCCFeatureSet.Meta):
        db_table = 'MFCCFeatureTestSet'
        app_label = 'energylenserver'

# Light Sensor


class LightData(SensorData):
    value = models.FloatField()
    label = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    # reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    def save_data(self, dev_id, data_list):
        super(LightData, self).save_data(dev_id, data_list)
        self.value = data_list[1]
        self.label = data_list[2]
        self.location = data_list[3]

        if self.pk is not None:
            self.pk = self.pk + 1

        # print "Data Received:", data_list

        try:
            self.save(force_insert=True)
            # print "PK::", self.pk
            # TODO: How to check if record is saved?
            return True
        except Exception, e:
            print e

    class Meta(SensorData.Meta):
        abstract = True
        app_label = 'energylenserver'


class LightTrainData(LightData):

    class Meta(LightData.Meta):
        db_table = 'LightTrainData'
        app_label = 'energylenserver'


class LightTestData(LightData):

    class Meta(LightData.Meta):
        db_table = 'LightTestData'
        app_label = 'energylenserver'

# Accelerometer


class AcclData(SensorData):
    x_value = models.FloatField()
    y_value = models.FloatField()
    z_value = models.FloatField()
    label = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    # reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    def save_data(self, dev_id, data_list):
        super(AcclData, self).save_data(dev_id, data_list)
        self.x_value = data_list[1]
        self.y_value = data_list[2]
        self.z_value = data_list[3]
        self.label = data_list[4]
        self.location = data_list[5]

        if self.pk is not None:
            self.pk = self.pk + 1

        # print "Data Received:", data_list

        try:
            self.save(force_insert=True)
            # print "PK::", self.pk
            # TODO: How to check if record is saved?
            return True
        except Exception, e:
            print e

    class Meta(SensorData.Meta):
        abstract = True
        app_label = 'energylenserver'


class AcclTrainData(AcclData):

    class Meta(AcclData.Meta):
        db_table = 'AcclTrainData'
        app_label = 'energylenserver'


class AcclTestData(AcclData):

    class Meta(AcclData.Meta):
        db_table = 'AcclTestData'
        app_label = 'energylenserver'

# Magnetometer


class MagData(SensorData):
    x_value = models.FloatField()
    y_value = models.FloatField()
    z_value = models.FloatField()
    label = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    # reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    def save_data(self, dev_id, data_list):
        super(MagData, self).save_data(dev_id, data_list)
        self.x_value = data_list[1]
        self.y_value = data_list[2]
        self.z_value = data_list[3]
        self.label = data_list[4]
        self.location = data_list[5]

        if self.pk is not None:
            self.pk = self.pk + 1

        # print "Data Received:", data_list

        try:
            self.save(force_insert=True)
            # print "PK::", self.pk
            # TODO: How to check if record is saved?
            return True
        except Exception, e:
            print e

    class Meta(SensorData.Meta):
        abstract = True
        app_label = 'energylenserver'


class MagTrainData(MagData):

    class Meta(MagData.Meta):
        db_table = 'MagTrainData'
        app_label = 'energylenserver'


class MagTestData(MagData):

    class Meta(MagData.Meta):
        db_table = 'MagTestData'
        app_label = 'energylenserver'
