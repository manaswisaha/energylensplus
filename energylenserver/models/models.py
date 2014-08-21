from django.db import models

"""
Models for the rest of the application
"""


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
    email_id = models.CharField(max_length=100, verbose_name=("Email ID"), blank=True, null=True)

    class Meta(Devices.Meta):
        db_table = 'RegisteredUsers'
        app_label = 'energylenserver'


class PowerEdges(object):

    """docstring for PowerEdges"""

    def __init__(self, arg):
        super(PowerEdges, self).__init__()
        self.arg = arg
