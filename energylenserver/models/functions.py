import time
import json
import datetime as dt

from models import *
from DataModels import *
from energylenserver.constants import DISAGG_ENERGY_API

# Enable Logging
import logging
logger = logging.getLogger('energylensplus_django')

"""
Global variables
"""
# Model mapping with filenames

MODEL_MAP = {
    'wifi': WiFiTestData,
    'rawaudio': RawAudioTestData,
    'audio': MFCCFeatureTestSet,
    'accelerometer': AcclTestData,
    'light': LightTestData,
    'mag': MagTestData,
    'Trainingwifi': WiFiTrainData,
    'Trainingrawaudio': RawAudioTrainData,
    'Trainingaudio': MFCCFeatureTrainSet,
    'Trainingaccelerometer': AcclTrainData,
    'Traininglight': LightTrainData,
    'Trainingmag': MagTrainData
}

"""
Helper functions
"""


def modify_time(time):
    return dt.datetime.fromtimestamp(time)

"""
User Management Model methods
"""


def determine_user(reg_id):
    """
    Determine the user with the given reg id
    """
    try:
        user = RegisteredUsers.objects.get(reg_id=reg_id)
    except RegisteredUsers.DoesNotExist, e:
        logger.error("[UserDoesNotExistException Occurred] No registration found! :: %s",
                     str(e))
        return False

    return user


def get_user(dev_id):
    """
    Gets user details with the given dev_id
    """
    try:
        user = RegisteredUsers.objects.get(dev_id=dev_id)
    except RegisteredUsers.DoesNotExist, e:
        logger.error("[UserDoesNotExistException Occurred] No registration found! :: %s",
                     str(e))
        return False

    return user


def get_all_active_users():
    """
    Get all the active users
    """
    try:
        users = RegisteredUsers.objects.filter(is_active=True)
    except Exception, e:
        logger.error("[GetAllActiveUsersException Occurred]:: %s", str(e))
        return False

    return users


def get_users_for_training(apt_no, phone_model):
    """
    Get user details based on the given parameters
    Usage: For training
    """
    try:
        users = RegisteredUsers.objects.filter(
            is_active=True, apt_no=apt_no, phone_model=phone_model)
    except Exception, e:
        logger.error("[GetTrainUsersException Occurred]:: %s", str(e))
        return False

    return users


def get_users(user_list):
    """
    Get active users based on the list
    """
    try:
        users = RegisteredUsers.objects.filter(is_active=True, reg_id__in=user_list)
    except Exception, e:
        logger.error("[GetUsersException Occurred]:: %s", str(e))
        return False

    return users


def retrieve_users(apt_no):
    """
    Get all the active users of an apartment
    """
    try:
        users = RegisteredUsers.objects.filter(apt_no=apt_no, is_active=True)
    except Exception, e:
        logger.error("[GetAllUsersException Occurred]:: %s", str(e))
        return False

    return users


def mark_not_active(reg_id):
    """
    Marks the existing registration as not active
    Reason: Bad Registration
    """
    try:
        user = RegisteredUsers.objects.get(reg_id=reg_id)
        user.is_active = False
        user.save()
    except RegisteredUsers.DoesNotExist, e:
        logger.error("[UserDoesNotExistException Occurred] No registration found! :: %s",
                     str(e))
        return False

    return True


def delete_user(reg_id):
    """
    Deletes the User
    Uses: When BAD Registration response is received
    """
    try:
        user = RegisteredUsers.objects.get(reg_id=reg_id)
        user.delete()
    except RegisteredUsers.DoesNotExist, e:
        logger.error("[UserDoesNotExistException Occurred] No registration found! :: %s",
                     str(e))
        return False

    return True

"""
Meter Data Management Model methods
"""


def retrieve_meter_info(apt_no):
    try:
        meter_set = MeterInfo.objects.filter(apt_no=apt_no)
    except MeterInfo.DoesNotExist:
        logger.error("[MeterDoesNotExistException Occurred] "
                     "No meters found for the given apt no: %s", apt_no)
        return False
    except Exception, e:
        logger.error("[MeterInfoException Occurred] %s", str(e))
        return False

    meters = []
    for meter in meter_set:
        m = {}
        m['uuid'] = meter.meter_uuid
        m['type'] = meter.meter_type
        meters.append(m)

    return meters

"""
Sensor Data Management Model methods
"""


def get_sensor_training_data(sensor_name, apt_no, dev_id_list):
    """
    Retrieves the training data based for the specified dev id list
    for an apartment
    """

    # Set sensor data model
    model = MODEL_MAP['Training' + sensor_name]

    logger.debug("Getting training data for dev_ids: %s for apt_no: %d", dev_id_list, apt_no)

    # Get data
    try:
        data = model.objects.filter(dev_id__in=dev_id_list)
    except model.DoesNotExist:
        logger.error("[SensorTrainDataDoesNotExistException Occurred]"
                     " No training data found for the given sensor: %s",
                     sensor_name)
        return False
    except Exception, e:
        logger.error("[SensorTrainDataDoesNotExistException Occurred] %s", str(e))
        return False

    return data


def get_sensor_data(sensor_name, start_time, end_time, dev_id_list):
    """
    Retrieves the sensor data based on its type
    between the specified period
    """

    # Set sensor data model
    model = MODEL_MAP[sensor_name]

    logger.debug("Getting data between %s and %s for dev_id: %s" %
                 (time.ctime(start_time), time.ctime(end_time), dev_id_list))
    # Get data
    try:
        if dev_id_list == "all":
            data = model.objects.filter(timestamp__gte=start_time,
                                        timestamp__lte=end_time)
        else:
            data = model.objects.filter(dev_id__in=dev_id_list,
                                        timestamp__gte=start_time,
                                        timestamp__lte=end_time)
    except model.DoesNotExist:
        logger.error("[SensorDataDoesNotExistException Occurred] "
                     "No data found for the given sensor: %s",
                     sensor_name)
        return False
    except Exception, e:
        logger.error("[GetSensorDataException Occurred] %s", str(e))
        return False

    return data


def get_unlabeled_data(sensor_name, start_time, end_time, label, dev_id_list):
    """
    Retrieves the unlabeled sensor data based on its type
    between the specified period
    """

    # Set sensor data model
    model = MODEL_MAP[sensor_name]

    logger.debug("Getting unlabeled data between %s and %s for dev_id: %s" %
                 (time.ctime(start_time), time.ctime(end_time), dev_id_list))
    # Get data
    try:
        data = model.objects.filter(dev_id__in=dev_id_list,
                                    timestamp__gte=start_time,
                                    timestamp__lte=end_time,
                                    label='none')
    except model.DoesNotExist:
        logger.error("[SensorDataDoesNotExistException Occurred] "
                     "No data found for the given sensor: %s",
                     sensor_name)
        return False
    except Exception, e:
        logger.error("[GetUnlabeledDataException Occurred] %s", str(e))
        return False

    return data


def get_labeled_data(sensor_name, start_time, end_time, label, dev_id_list):
    """
    Retrieves the labeled sensor data based on its type
    between the specified period
    """

    # Set sensor data model
    model = MODEL_MAP[sensor_name]

    logger.debug("Getting labeled data between %s and %s for dev_id: %s" %
                 (time.ctime(start_time), time.ctime(end_time), dev_id_list))
    # Get data
    try:
        data = model.objects.filter(dev_id__in=dev_id_list,
                                    timestamp__gte=start_time,
                                    timestamp__lte=end_time,
                                    label=label)
    except model.DoesNotExist:
        logger.error("[SensorDataDoesNotExistException Occurred] "
                     "No data found for the given sensor: %s",
                     sensor_name)
        return False
    except Exception, e:
        logger.error("[GetLabeledDataException Occurred] %s", str(e))
        return False

    return data

"""
Metadata Management Model methods
"""


def get_access_points(apt_no):
    """
    Retrieves all the access points that are visible around the apt_no
    """
    try:
        ap = AccessPoints.objects.filter(apt_no=apt_no)
    except Exception, e:
        logger.error("[GetAPException Occurred]:: %s", str(e))
        return False

    return ap


def get_home_ap(apt_no):
    """
    Retrieves the home AP for the specified apartment
    """
    try:
        home_ap = AccessPoints.objects.get(apt_no=apt_no, home_ap=True)
    except Exception, e:
        logger.error("[GetHomeAPException Occurred]:: %s", str(e))
        return False

    return home_ap.macid


def retrieve_metadata(apt_no):
    """
    Retrieve appliances from Metadata
    """
    try:
        records = Metadata.objects.filter(apt_no=apt_no)
        logger.debug("Number of metadata entries: %s", str(records.count()))

    except Exception, e:
        logger.error("[GetMetadataException]:: %s", e)

    return records

"""
Inference Management Model methods
"""


def get_on_event_by_id(index):
    """
    Gets on event by the specified id
    """
    try:
        record = EventLog.objects.get(id=index)
    except Exception, e:
        logger.error("[GetONEventByIDException]:: %s", e)
        return False

    return record


def get_on_events(apt_no, event_time):
    """
    Retrieves all the on events before the specified time in
    given apartment
    """
    try:
        records = EventLog.objects.filter(apt_no=apt_no, event_time__lt=event_time)
        logger.debug("Number of ON events: %s", str(records.count()))
    except Exception, e:
        logger.error("[GetONEventException]:: %s", e)
        return False

    return records


def retrieve_activities(dev_id, start_time, end_time, activity_name):
    """
    Retrieves all activities of a user between the time period or
    based on requested appliance
    """
    try:
        if activity_name == "all":
            # Retrieves all activities - for usage/wastage reports
            records = ActivityLog.objects.filter(dev_id=dev_id,
                                                 start_time__gte=start_time,
                                                 end_time__lte=end_time)
        else:
            # Retrieves the specified activities - for disaggregated activities
            records = ActivityLog.objects.filter(dev_id=dev_id,
                                                 start_time__gte=start_time,
                                                 end_time__lte=end_time,
                                                 appliance=activity_name)

    except Exception, e:
        logger.error("[RetrieveActivitiesException]::", e)

    return records


def retrieve_finished_activities(dev_id, start_time, end_time):
    """
    Retrieves all activities that got completed in the specified time
    period
    """
    try:
        # Retrieves all activities - for validation report generation and
        # usage/wastage reports
        records = ActivityLog.objects.filter(dev_id=dev_id,
                                             end_time__gte=start_time,
                                             end_time__lte=end_time)

    except Exception, e:
        logger.error("[RetrieveFinishedActivitiesException]::", e)

    return records


def update_activities(act_id, true_appl, true_loc):
    """
    Updates the activities with the true appl/loc pair given by the UserWarning
    """
    try:
        act_record = ActivityLog.objects.get(id=act_id)

        # Update activity
        act_record.true_appliance = true_appl
        act_record.true_location = true_loc
        act_record.save()
    except ActivityLog.DoesNotExist:
        logger.debug("[ActivityDoesNotExistException Occurred] "
                     "No activity found with the given id: %s", act_id)
        return False
    except Exception, e:
        logger.error("[UpdateActivitiesException]:: %s", str(e))
        return False

    return True


def retrieve_usage_entries(dev_id, activity_id_list):
    """
    Retrieves usage entries of the given activity id list
    """
    try:
        usage_entries = EnergyUsageLog.objects.filter(
            dev_id=dev_id, activity_id__in=activity_id_list)

    except EnergyUsageLog.DoesNotExist:
        logger.debug("[UsageDoesNotExistException Occurred] "
                     "No usage entries found for the given ids:: %s", activity_id_list)
        return False
    except Exception, e:
        logger.error("[RetrieveUsageEntriesException]:: %s", str(e))
        return False

    record_count = usage_entries.count()
    logger.debug("Number of usage entries: %s", record_count)
    u_entries = {}
    for r in usage_entries:
        u_entries[r.id] = {'usage': r.usage}
    logger.debug("Appliances::\n %s", json.dumps(u_entries))

    return u_entries


def retrieve_wastage_entries(dev_id, activity_id_list):
    """
    Retrieves wastage entries of the given activity id list
    """
    try:
        wastage_entries = EnergyWastageLog.objects.filter(
            dev_id=dev_id, activity_id__in=activity_id_list)

    except EnergyWastageLog.DoesNotExist:
        logger.debug("[WastageDoesNotExistException Occurred] "
                     "No wastage entries found for the given ids:: %s", activity_id_list)
        return False
    except Exception, e:
        logger.error("[RetrieveWastageEntriesException]:: %s", str(e))
        return False

    record_count = wastage_entries.count()
    logger.debug("Number of wastage entries: %s", record_count)
    u_entries = {}
    for r in wastage_entries:
        u_entries[r.id] = {'wastage': r.wastage}
    logger.debug("Appliances::\n %s", json.dumps(u_entries))

    return u_entries
