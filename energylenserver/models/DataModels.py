from django.db import models

# TODO: Add the foreign key to gcm.models.reg_id (See ForeignKey.to_field in the documentation)
# Models for live phone sensor data


class WiFiData(models.Model):
    timestamp = models.DateTimeField('date uploaded', unique=True)
    macid = models.CharField(max_length=200)
    ssid = models.CharField(max_length=200)
    rssi = models.IntegerField()
    label = models.CharField(max_length=200)
    reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    class Meta:
        db_table = 'WiFiData'
        app_label = 'energylenserver'
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']


class RawAudioData(models.Model):
    timestamp = models.DateTimeField('date uploaded', unique=True)
    value = models.IntegerField()
    label = models.CharField(max_length=200)
    reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    class Meta:
        db_table = 'RawAudioData'
        app_label = 'energylenserver'
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']


class MFCCFeatureSet(models.Model):
    timestamp = models.DateTimeField('date uploaded', unique=True)
    mfcc1 = models.IntegerField()
    mfcc2 = models.IntegerField()
    mfcc3 = models.IntegerField()
    mfcc4 = models.IntegerField()
    mfcc5 = models.IntegerField()
    mfcc6 = models.IntegerField()
    mfcc7 = models.IntegerField()
    mfcc8 = models.IntegerField()
    mfcc9 = models.IntegerField()
    mfcc10 = models.IntegerField()
    mfcc11 = models.IntegerField()
    mfcc12 = models.IntegerField()
    mfcc13 = models.IntegerField()
    label = models.CharField(max_length=200)
    reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    class Meta:
        db_table = 'RawAudioData'
        app_label = 'energylenserver'
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']


class AcclData(models.Model):
    timestamp = models.DateTimeField('date uploaded', unique=True)
    value = models.IntegerField()
    label = models.CharField(max_length=200)
    reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    class Meta:
        db_table = 'RawAudioData'
        app_label = 'energylenserver'
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']


class LightData(models.Model):
    timestamp = models.DateTimeField('date uploaded', unique=True)
    value = models.IntegerField()
    label = models.CharField(max_length=200)
    reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    class Meta:
        db_table = 'RawAudioData'
        app_label = 'energylenserver'
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']


class MagData(models.Model):
    timestamp = models.DateTimeField('date uploaded', unique=True)
    value = models.IntegerField()
    label = models.CharField(max_length=200)
    reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    class Meta:
        db_table = 'RawAudioData'
        app_label = 'energylenserver'
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']


# Models for training data

class TrainingWiFiData(models.Model):
    timestamp = models.DateTimeField('date uploaded', unique=True)
    macid = models.CharField(max_length=200)
    ssid = models.CharField(max_length=200)
    rssi = models.IntegerField()
    label = models.CharField(max_length=200)
    reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    class Meta:
        db_table = 'TrainingWiFiData'
        app_label = 'energylenserver'
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']


class TrainingRawAudioData(models.Model):
    timestamp = models.DateTimeField('date uploaded', unique=True)
    value = models.IntegerField()
    label = models.CharField(max_length=200)
    reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    class Meta:
        db_table = 'TrainingRawAudioData'
        app_label = 'energylenserver'
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']


class TrainingMFCCFeatureSet(models.Model):
    timestamp = models.DateTimeField('date uploaded', unique=True)
    mfcc1 = models.IntegerField()
    mfcc2 = models.IntegerField()
    mfcc3 = models.IntegerField()
    mfcc4 = models.IntegerField()
    mfcc5 = models.IntegerField()
    mfcc6 = models.IntegerField()
    mfcc7 = models.IntegerField()
    mfcc8 = models.IntegerField()
    mfcc9 = models.IntegerField()
    mfcc10 = models.IntegerField()
    mfcc11 = models.IntegerField()
    mfcc12 = models.IntegerField()
    mfcc13 = models.IntegerField()
    label = models.CharField(max_length=200)
    reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    class Meta:
        db_table = 'TrainingMFCCFeatureSet'
        app_label = 'energylenserver'
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']


class TrainingAcclData(models.Model):
    timestamp = models.DateTimeField('date uploaded', unique=True)
    value = models.IntegerField()
    label = models.CharField(max_length=200)
    reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    class Meta:
        db_table = 'TrainingAcclData'
        app_label = 'energylenserver'
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']


class TrainingLightData(models.Model):
    timestamp = models.DateTimeField('date uploaded', unique=True)
    value = models.IntegerField()
    label = models.CharField(max_length=200)
    reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    class Meta:
        db_table = 'TrainingLightData'
        app_label = 'energylenserver'
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']


class TrainingMagData(models.Model):
    timestamp = models.DateTimeField('date uploaded', unique=True)
    value = models.IntegerField()
    label = models.CharField(max_length=200)
    reg_id = models.CharField(max_length=255, verbose_name=_("Registration ID"), unique=True)

    class Meta:
        db_table = 'TrainingMagData'
        app_label = 'energylenserver'
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']
