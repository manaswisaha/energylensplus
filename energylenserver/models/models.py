from django.db import models

"""
Models for the rest of the application
"""

app_label_str = 'energylenserver'


class Devices(models.Model):

    dev_id = models.BigIntegerField(max_length=15, verbose_name=("Device ID"), primary_key=True)
    reg_id = models.CharField(max_length=255, verbose_name=("Registration ID"), unique=True)
    name = models.CharField(max_length=50, verbose_name=("Name"), blank=True, null=True)
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
    apt_no = models.IntegerField()
    email_id = models.CharField(max_length=100, verbose_name=("Email ID"), null=True)

    class Meta(Devices.Meta):
        db_table = 'RegisteredUsers'
        app_label = app_label_str


class Metadata(models.Model):

    """
    Stores the metadata for each apartment
    """
    apt_no = models.IntegerField()
    appliance = models.CharField(max_length=50, verbose_name=("Appliance"))
    location = models.CharField(max_length=50, verbose_name=("Location"))
    power = models.FloatField()

    def __unicode__(self):
        return self.dev_id.apt_no + "-" + self.appliance + "-" + self.location

    class Meta:
        db_table = 'Metadata'
        app_label = app_label_str


class MeterInfo(models.Model):

    """
    Stores the meter details in each apartment
    """
    meter_uuid = models.CharField(max_length=255, verbose_name=("Meter UUID"), primary_key=True)
    meter_type = models.CharField(max_length=20, verbose_name=("Meter Type"), null=True)
    apt_no = models.IntegerField()

    class Meta:
        db_table = 'MeterInfo'
        app_label = app_label_str


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
        app_label = app_label_str


class EventLog(models.Model):

    """
    Stores all the detected events associated with the inferred "who", "what", "where" and "when"
    """
    edge_id = models.ForeignKey(Edges)
    event_time = models.DecimalField(unique=False, max_digits=14, decimal_places=3)  # when
    appliance = models.CharField(max_length=50, verbose_name=("Appliance"), null=True)  # what
    location = models.CharField(max_length=50, verbose_name=("Location"), null=True)  # where
    dev_id = models.ForeignKey(RegisteredUsers)  # who
    event_type = models.CharField(max_length=20, verbose_name=("ON/OFF"), null=True)

    class Meta:
        db_table = 'EventLog'
        app_label = app_label_str


class ActivityLog(models.Model):

    """
    Stores the inferred activities irrespective of the person responsible
    """
    start_time = models.DecimalField(unique=False, max_digits=14, decimal_places=3)
    end_time = models.DecimalField(unique=False, max_digits=14, decimal_places=3)
    appliance = models.CharField(max_length=50, verbose_name=("Appliance"), null=False)
    location = models.CharField(max_length=50, verbose_name=("Location"), null=False)
    power = models.FloatField()  # Average of magnitude of the matched edges
    meter = models.ForeignKey(MeterInfo)
    start_event = models.ForeignKey(EventLog)
    end_event = models.ForeignKey(EventLog)

    class Meta:
        db_table = 'ActivityLog'
        app_label = app_label_str


class EnergyUsageLog(models.Model):

    """
    Stores energy usage for each user for every activity
    """
    activity_id = models.ForeignKey(ActivityLog)
    usage = models.FloatField()
    dev_id = models.ForeignKey(RegisteredUsers)

    class Meta:
        db_table = 'EnergyUsageLog'
        app_label = app_label_str


class EnergyWastageLog(models.Model):

    """
    Stores energy wastage for each user for every activity
    """
    activity_id = models.ForeignKey(ActivityLog)
    wastage = models.FloatField()
    dev_id = models.ForeignKey(RegisteredUsers)

    class Meta:
        db_table = 'EnergyWastageLog'
        app_label = app_label_str


class EnergyWastageNotif(models.Model):

    """
    Stores the real-time wastage detected
    """
    dev_id = models.ForeignKey(RegisteredUsers)
    time = models.DecimalField(unique=False, max_digits=14, decimal_places=3)
    appliance = models.CharField(max_length=50, verbose_name=("Appliance"), null=False)
    location = models.CharField(max_length=50, verbose_name=("Location"), null=False)
    message = models.CharField(max_length=255, verbose_name=("Message"), null=False)

    class Meta:
        db_table = 'EnergyWastageNotif'
        app_label = app_label_str


"""
Models for maintaining usage stats for the mobile application
"""


class UsageLogScreens(models.Model):

    """
    Stores the usage stats of each screen of the app
    """
    dev_id = models.ForeignKey(RegisteredUsers)
    time_of_day = models.DecimalField(unique=False, max_digits=14, decimal_places=3)
    tod_time = models.DateTimeField('edge time')
    screen_name = models.CharField(
        max_length=50, verbose_name=("Screen Name"), blank=True, null=False)
    time_of_stay = models.DecimalField(unique=False, max_digits=10, decimal_places=3)

    class Meta:
        db_table = 'UsageLogScreens'
        app_label = app_label_str


class UsageLogNotifs(models.Model):

    """
    Stores the usage stats of each notification of the app
    """
    dev_id = models.ForeignKey(RegisteredUsers)
    received_at = models.DecimalField(unique=False, max_digits=14, decimal_places=3)
    notif_id = models.CharField(
        max_length=50, verbose_name=("NotificationID"), blank=True, null=False)
    seen_at = models.DecimalField(unique=False, max_digits=10, decimal_places=3)

    class Meta:
        db_table = 'UsageLogNotifs'
        app_label = app_label_str
