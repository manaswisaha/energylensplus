import json
import datetime as dt

from models import *
from DataModels import *
from energylenserver.constants import DISAGG_ENERGY_API

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
        print("[UserDoesNotExistException Occurred] No registration found! for %d::%s " %
             (reg_id, str(e)))
        return False

    return user


def get_all_users():
    """
    Determine all the users
    """
    try:
        users = RegisteredUsers.objects.filter(is_active=True)
    except Exception, e:
        print "[GetAllUsersException Occurred]:: " + str(e)
        return False

    return users


def retrieve_users(apt_no):
    """
    Determine all the users
    """
    try:
        users = RegisteredUsers.objects.filter(apt_no=apt_no)
    except Exception, e:
        print "[GetAllUsersException Occurred]:: " + str(e)
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
        print("[UserDoesNotExistException Occurred] No registration found! for %d::%s " %
             (reg_id, str(e)))
        return False

    return True

"""
Meter Data Management Model methods
"""


def retrieve_meter_info(apt_no):
    try:
        meter_set = MeterInfo.objects.filter(apt_no=apt_no)
    except MeterInfo.DoesNotExist:
        print("[MeterDoesNotExistException Occurred] No meters found for the given apt no: "
              + apt_no)
        return False
    except Exception, e:
        print "[MeterInfoException Occurred] " + str(e)
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


def get_sensor_data(sensor_name, dataset_type, start_time, end_time, dev_id_list):
    """
    Retrieves the sensor data based on its type and the dataset type
    between the specified period
    """

    # Determine sensor data model
    if dataset_type == "train":
        model = MODEL_MAP['Training' + sensor_name]
    else:
        model = MODEL_MAP[sensor_name]

    # Get data
    try:
        if dev_id_list == "all":
            data = model.objects.filter(start_time__gte=start_time,
                                        end_time__gte=end_time)
        else:
            data = model.objects.filter(dev_id__in=dev_id_list,
                                        start_time__gte=start_time,
                                        end_time__gte=end_time)
    except model.DoesNotExist:
        print("[SensorDataDoesNotExistException Occurred] No data found for the given sensor: "
              + sensor_name)
        return False
    except Exception, e:
        print "[GetSensorDataException Occurred] " + str(e)
        return False

    return data


"""
Metadata Management Model methods
"""


def retrieve_metadata(apt_no):
    """
    Retrieve appliances from Metadata
    """
    appliances = []
    try:
        records = Metadata.objects.filter(apt_no=apt_no)
        print "Number of metadata entries: " + str(records.count())
        for r in records:
            appliances.append({'location': r.location, 'appliance': r.appliance})

    except Exception, e:
        print "[GetMetadataException]:: " + DISAGG_ENERGY_API, e

    # temp code
    appliances.append(
        {'location': 'Dining Room', 'appliance': 'Light'})
    appliances.append(
        {'location': 'Dining Room', 'appliance': 'Fan'})
    appliances.append(
        {'location': 'Dining Room', 'appliance': 'AC'})
    appliances.append(
        {'location': 'Bedroom', 'appliance': 'TV'})
    appliances.append(
        {'location': 'Bedroom', 'appliance': 'Light'})
    appliances.append(
        {'location': 'Bedroom', 'appliance': 'AC'})

    return appliances

"""
Inference Management Model methods
"""


def retrieve_activities(dev_id, start_time, end_time, activity_name):
    """
    Retrieves all activities between the time period or
    based on requested appliance
    """
    try:
        if activity_name == "all":
            # Retrieves all activities - for validation report generation
            records = ActivityLog.objects.filter(dev_id=dev_id,
                                                 end_time__gte=start_time,
                                                 end_time__lte=end_time)
        else:
            # Retrieves the specified activities - for disaggregated activities
            records = ActivityLog.objects.filter(dev_id=dev_id,
                                                 start_time__gte=start_time,
                                                 end_time__lte=end_time,
                                                 appliance=activity_name)

    except Exception, e:
        print "[RetrieveActivitiesException]::", e

    record_count = records.count()
    print "Number of activities: " + record_count
    activities = {}
    for r in records:
        activities[r.id] = {'name': r.appliance, 'location': r.location,
                            'usage': r.power, 'start_time': r.start_time,
                            'end_time': r.end_time}
    print "Appliances::\n " + json.dumps(activities)

    return activities


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
        print("[ActivityDoesNotExistException Occurred] No activity found with the given id: "
              + act_id)
        return False
    except Exception, e:
        print "[UpdateActivitiesException]:: " + str(e)
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
        print("[UsageDoesNotExistException Occurred] No usage entries found for the given ids:: "
              + activity_id_list)
        return False
    except Exception, e:
        print "[RetrieveUsageEntriesException]:: " + str(e)
        return False

    record_count = usage_entries.count()
    print "Number of usage entries: " + record_count
    u_entries = {}
    for r in usage_entries:
        u_entries[r.id] = {'usage': r.usage}
    print "Appliances::\n " + json.dumps(u_entries)

    return u_entries
