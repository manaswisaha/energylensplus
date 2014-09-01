from django.db import models

"""
Models for the rest of the application
"""


class Devices(models.Model):

    dev_id = models.BigIntegerField(max_length=15, verbose_name=("Device ID"), primary_key=True)
    reg_id = models.CharField(max_length=255, verbose_name=("Registration ID"), unique=True)
    name = models.CharField(max_length=50, verbose_name=("Name"), blank=True, null=True)
    apt_no = models.IntegerField()
    is_active = models.BooleanField(verbose_name=("Is active?"), default=True)
    creation_date = models.DateTimeField(verbose_name=("Creation date"), auto_now_add=True)
    modified_date = models.DateTimeField(verbose_name=("Modified date"), auto_now=True)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name_plural = ("Devices")
        ordering = ['-modified_date']


class RegisteredUsers(Devices):

    """
    Keeps track of all the registered users
    """
    email_id = models.CharField(max_length=100, verbose_name=("Email ID"), blank=True, null=True)

    class Meta(Devices.Meta):
        db_table = 'RegisteredUsers'
        app_label = 'energylenserver'


class Metadata(models.Model):

    """
    Stores the metadata for each apartment
    """
    apt_no = models.IntegerField()
    appliance = models.CharField(max_length=50, verbose_name=("Appliance"), blank=False, null=False)
    location = models.CharField(max_length=50, verbose_name=("Location"), blank=False, null=False)
    power = models.FloatField()

    def __unicode__(self):
        return self.dev_id.apt_no + "-" + self.appliance + "-" + self.location

    class Meta:
        db_table = 'Metadata'
        app_label = 'energylenserver'


class MeterInfo(models.Model):

    """
    Stores the meter details in each apartment
    """
    meter_uuid = models.CharField(max_length=255, verbose_name=("Meter UUID"), primary_key=True)
    meter_type = models.CharField(max_length=20, verbose_name=("Meter Type"), blank=True, null=True)
    apt_no = models.IntegerField()

    class Meta:
        db_table = 'MeterInfo'
        app_label = 'energylenserver'


class Edges(models.Model):

    """
    Stores the light and power edges from the smart meter data
    """
    timestamp = models.DecimalField(unique=False, max_digits=14, decimal_places=3)
    time = models.DateTimeField('edge time')
    magnitude = models.FloatField()
    type = models.CharField(max_length=10)
    curr_power = models.FloatField()
    meter = models.ForeignKey(MeterInfo)

    class Meta:
        db_table = 'Edges'
        app_label = 'energylenserver'


class ActivityLog(models.Model):

    """
    Stores the inferred activities
    """
    index = models.IntegerField()
    start_time = models.DecimalField(unique=False, max_digits=14, decimal_places=3)
    end_time = models.DecimalField(unique=False, max_digits=14, decimal_places=3)
    appliance = models.CharField(max_length=50, verbose_name=("Appliance"), blank=False, null=False)
    location = models.CharField(max_length=50, verbose_name=("Location"), blank=False, null=False)
    power = models.FloatField()
    meter = models.ForeignKey(MeterInfo)

    class Meta:
        db_table = 'ActivityLog'
        app_label = 'energylenserver'
