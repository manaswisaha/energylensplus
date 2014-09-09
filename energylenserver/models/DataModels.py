from decimal import getcontext
getcontext().prec = 14

import os
from django.db import models
from django.db import connection

from models import RegisteredUsers
from functions import modify_time

"""
Models for storing phone sensor data
"""


class SensorData(models.Model):
    # id = BigAutoField(primary_key=True)
    # r_id = models.CharField(max_length=200, primary_key=True)
    timestamp = models.DecimalField(unique=False, max_digits=14, decimal_places=3)
    dev_id = models.ForeignKey(RegisteredUsers)
    # time = models.DateTimeField('date uploaded', auto_now_add=True)

    def save_data(self, dev_id, data_list):
        time = float(data_list[0]) / 1000.
        self.dev_id = dev_id
        self.timestamp = time
        # self.r_id = str(self.timestamp) + '_' + str(self.dev_id.dev_id)
        self.time = modify_time(time)

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
            print "Number of records inserted: " + str(records_inserted)
            os.remove(filename)
        except Exception, e:
            print "[FileSaveException] AcclData::" + str(e)

    def save_data(self, dev_id, data_list):
        super(AcclData, self).save_data(dev_id, data_list)
        self.x_value = data_list[1]
        self.y_value = data_list[2]
        self.z_value = data_list[3]
        self.label = data_list[4]
        self.location = data_list[5]

        try:
            self.save()
            return True
        except Exception, e:
            print "[Exception] AcclData::save_data",
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
            print "Number of records inserted: " + str(records_inserted)
            os.remove(filename)
        except Exception, e:
            print "[FileSaveException] WiFiData::" + str(e)

    def save_data(self, dev_id, data_list):
        super(WiFiData, self).save_data(dev_id, data_list)
        time = data_list[0]
        self.dev_id = dev_id
        self.timestamp = time
        self.time = modify_time(time)
        self.macid = data_list[1]
        self.r_id = self.r_id + '_' + self.macid
        self.ssid = data_list[2]
        self.rssi = data_list[3]
        self.label = data_list[4]

        try:
            self.save()
            return True
        except Exception, e:
            print "[Exception] WiFiData::save_data",
            print e

    # def save_data(self, dev_id, df_csv):

    #     try:
    #         list_of_objects = []
    #         for idx in df_csv.index:
    #             record = list(df_csv.ix[idx])
    #             timestamp = record[0]
    #             time = timestamp / 1000.
    #             record.insert(1, modify_time(time))
    #             record.insert(2, dev_id)

    #             r_id = str(timestamp) + '_' + str(dev_id.dev_id)
    #             obj = self(r_id=r_id, timestamp=timestamp, time=time, x_value=record[3],
    #                        y_value=record[4], z_value=record[5],
    #                        label=record[6], location=record[7])
    #             print "DeviceID:", obj.dev_id
    #             list_of_objects.append(obj)
    #         return list_of_objects

    #     except Exception, e:
    #         print "[Exception]:", e

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
            print "Number of records inserted: " + str(records_inserted)
            os.remove(filename)
        except Exception, e:
            print "[FileSaveException] RawAudioData::" + str(e)

    def save_data(self, dev_id, data_list):
        super(RawAudioData, self).save_data(dev_id, data_list)
        self.values = data_list[1]
        self.label = data_list[2]
        self.location = data_list[3]

        try:
            self.save()
            return True
        except Exception, e:
            print "[Exception] RawAudioData::save_data",
            print e

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
            print "Number of records inserted: " + str(records_inserted)
            os.remove(filename)
        except Exception, e:
            print "[FileSaveException] MFCCFeatureSet::" + str(e)

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

        try:
            self.save()
            return True
        except Exception, e:
            print "[Exception] MFCCFeatureSet::save_data",
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
            print "Number of records inserted: " + str(records_inserted)
            os.remove(filename)
        except Exception, e:
            print "[FileSaveException] LightData::" + str(e)

    def save_data(self, dev_id, data_list):
        super(LightData, self).save_data(dev_id, data_list)
        self.value = data_list[1]
        self.label = data_list[2]
        self.location = data_list[3]

        try:
            self.save()
            return True
        except Exception, e:
            print "[Exception] LightData::save_data",
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
            print "Number of records inserted: " + str(records_inserted)
            os.remove(filename)
        except Exception, e:
            print "[FileSaveException] MagData::" + str(e)

    def save_data(self, dev_id, data_list):
        super(MagData, self).save_data(dev_id, data_list)
        self.x_value = data_list[1]
        self.y_value = data_list[2]
        self.z_value = data_list[3]
        self.label = data_list[4]
        self.location = data_list[5]

        try:
            self.save()
            return True
        except Exception, e:
            print "[Exception] MagData::save_data",
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
# '''
