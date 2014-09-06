# from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

from constants import *
from models.DataModels import *
from models.models import *
from preprocessing import wifi
from meter.functions import *
from meter.smap import *
from energylenserver.tasks import phoneDataHandler

import os
import sys
import json
import time
import threading
import pandas as pd
import datetime as dt

# Model mapping with filenames

FILE_MODEL_MAP = {
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
# """


def user_exists(device_id):
    """
    Check whether user is registered
    """
    try:
        dev_id = RegisteredUsers.objects.get(dev_id__exact=device_id)
        return dev_id
    except RegisteredUsers.DoesNotExist, e:
        print "[UserDoesNotExistException Occurred] No registration found!:: ", e
        return False


def import_from_file(filename, csvfile):
    """
    Imports the CSV file into appropriate db model
    """
    print "File size:", csvfile.size
    # print "File content:", csvfile.read()

    # Save file in a temporary location
    # path = default_storage.save(filename, ContentFile(csvfile.read()))
    # print "Path before deletion", path, type(path)
    # tmp_file = os.path.join(settings.MEDIA_ROOT, path)
    # print "Temp location", tmp_file, type(tmp_file)

    training_status = False

    # Find the sensor from the filename and choose appropriate table
    filename_l = filename.split('_')
    device_id = int(filename_l[0])

    # Check if it is a registered user
    is_user = user_exists(device_id)
    if not is_user:
        return False
    else:
        dev_id = is_user

    sensor_name = filename_l[2]
    if sensor_name == "Training":
        sensor_name = filename_l[3]
        training_status = True
    print "Sensor:", sensor_name

    # if sensor_name != 'accelerometer':
    #     return True

    # if sensor_name is 'audio':
    # Store csv file
    #     filename = 'tmp/audio_log_' + dt.datetime.fromtimestamp(time.time()) + '.csv'

    # Get CSV data
    try:
        df_csv = pd.read_csv(csvfile)
        print "No of records::", len(df_csv)
        # Delete file
        # path = default_storage.delete(filename)
    except Exception, e:
        if str(e) == "Passed header=0 but only 0 lines in file":
            print "[Exception]:: Creation of dataframe failed! No lines found in the file!"
            return True
        else:
            print "[Exception]::", e
            return False

    # Call new celery task for importing records
    phoneDataHandler.delay(filename, sensor_name, df_csv, training_status, dev_id)

    # insertThread = threading.Thread(target=insert_records, args=(
    #     filename, sensor_name, df_csv, training_status, dev_id))
    # insertThread.start()

    return True


@csrf_exempt
def upload_data(request):
    """
    Receives the uploaded CSV files and stores them in the database
    """

    try:
        if request.method == 'GET':
            return HttpResponse(json.dumps(ERROR_INVALID_REQUEST), content_type="application/json")

        if request.method == 'POST':
            print "\n[POST Request Received] -", sys._getframe().f_code.co_name

            payload = request.FILES
            file_container = payload['uploadedfile']
            filename = str(file_container.name)
            csvfile = file_container
            print "File received:", filename

            # Store in the database
            if(import_from_file(filename, csvfile)):
                return HttpResponse(json.dumps(UPLOAD_SUCCESS), content_type="application/json")

            else:
                return HttpResponse(json.dumps(UPLOAD_UNSUCCESSFUL),
                                    content_type="application/json")

    except Exception, e:

        print "[UploadDataException Occurred]::", e
        return HttpResponse(json.dumps(UPLOAD_UNSUCCESSFUL), content_type="application/json")


@csrf_exempt
def real_time_data_access(request):
    """
    Receives real-time data access request for plots
    """

    try:
        if request.method == 'GET':
            return HttpResponse(json.dumps(ERROR_INVALID_REQUEST), content_type="application/json")

        if request.method == 'POST':

            # TODO: Get apt_no from the db based on the IMEI number
            payload = json.loads(request.body)
            print "\n[POST Request Received] -", sys._getframe().f_code.co_name

            dev_id = payload['dev_id']
            print "Requested by:", dev_id

            # Check if it is a registered user
            is_user = user_exists(dev_id)
            if not is_user:
                return HttpResponse(json.dumps(REALTIMEDATA_UNSUCCESSFUL),
                                    content_type="application/json")
            else:
                apt_no = is_user.apt_no
                print "Apartment Number:", apt_no

            # Get power data
            timestamp, total_power = get_latest_power_data(apt_no)

            payload = {}
            payload['timestamp'] = timestamp
            payload['power'] = total_power

            print "Payload", payload

            return HttpResponse(json.dumps(payload), content_type="application/json")

    except Exception, e:

            print "[RealTimeDataException Occurred]::", e
            return HttpResponse(json.dumps(REALTIMEDATA_UNSUCCESSFUL),
                                content_type="application/json")


@csrf_exempt
def training_data(request):
    """
    Receives the training data labels, computes power consumption,
    and stores them as Metadata
    """

    try:
        if request.method == 'GET':
            return HttpResponse(json.dumps(ERROR_INVALID_REQUEST), content_type="application/json")

        if request.method == 'POST':
            payload = json.loads(request.body)
            print "\n[POST Request Received] -", sys._getframe().f_code.co_name
            print payload

            dev_id = payload['dev_id']
            start_time = payload['start_time']
            end_time = payload['end_time']
            location = payload['location']
            appliance = payload['appliance']

            # Check if it is a registered user
            user = user_exists(dev_id)
            if not user:
                return HttpResponse(json.dumps(TRAINING_UNSUCCESSFUL),
                                    content_type="application/json")
            else:
                apt_no = user.apt_no
                print "Apartment Number:", apt_no

            # Compute Power
            power = training_compute_power(apt_no, start_time, end_time)
            print "Computed Power::", power

            # See if entry exists for appliance-location combination
            # Update power value if it exists
            try:
                r = Metadata.objects.get(apt_no__exact=apt_no, location__exact=location,
                                         appliance__exact=appliance)
                print "Metadata with entry:", r.apt_no, r.appliance, r.location, "exists"
                # Update power
                r.power = power
                r.save()
                print "Metadata record updated"
            except Metadata.DoesNotExist, e:

                # Store metadata
                user = Metadata(
                    apt_no=apt_no, appliance=appliance, location=location, power=power)
                user.save()
                print "Metadata creation successful"

            payload = {}
            payload['power'] = power
            return HttpResponse(json.dumps(payload),
                                content_type="application/json")

    except Exception, e:

            print "[TrainingDataException Occurred]::", e
            return HttpResponse(json.dumps(TRAINING_UNSUCCESSFUL),
                                content_type="application/json")


@csrf_exempt
def register_device(request):
    """
    Receives the registration requests from the mobile devices and
    stores user-device and meter details in the database
    """
    print "Request received:", request.method

    try:
        if request.method == 'GET':
            return HttpResponse(json.dumps(ERROR_INVALID_REQUEST), content_type="application/json")

        if request.method == 'POST':
            print "\n[POST Request Received]"

            # print request.body
            payload = json.loads(request.body)
            print "POST Payload:\n", payload

            reg_id = payload['registration_id']
            user_name = payload['user_name']
            email_id = payload['email_id']
            dev_id = payload['dev_id']
            apt_no = payload['apt_no']
            home_ap = payload['home_ap']
            other_ap = payload['other_ap']

            print "\n--User Registration Details--"
            print "RegID:", reg_id
            print "Username:", user_name
            print "Email ID:", email_id
            print "Device ID:", dev_id
            print "Apartment Number:", apt_no
            print "Home AP:", home_ap
            print "Other APs:", other_ap

            if apt_no.isdigit():

                # Store the meter details of the apt_no if the current user is the first
                # member of the house that registers

                apt_no = int(apt_no)
                user_count = RegisteredUsers.objects.filter(apt_no__exact=apt_no).count()
                print "Number of users registered for", apt_no, ":", user_count
                if user_count == 0:
                    # Get meter information for the apt_no for the apartment
                    meters = get_meter_info(apt_no)

                    # Store meter information in the DB
                    for meter in meters:
                        meter_uuid = meter['uuid']
                        meter_type = meter['type']
                        if meter_type == "Light Backup":
                            meter_type = "Light"

                        minfo_record = MeterInfo(
                            meter_uuid=meter_uuid, meter_type=meter_type, apt_no=apt_no)
                        minfo_record.save()

            try:
                r = RegisteredUsers.objects.get(dev_id__exact=dev_id)
                print "Registration with device ID", r.dev_id, "exists"
                # Store user
                r.reg_id = reg_id
                r.name = user_name
                r.modified_date = dt.datetime.fromtimestamp(time.time())
                r.save()
                print "Registration updated"
            except RegisteredUsers.DoesNotExist, e:

                # Store user
                user = RegisteredUsers(
                    dev_id=dev_id, reg_id=reg_id, apt_no=apt_no, name=user_name, email_id=email_id)
                user.save()
                print "Registration successful"
            return HttpResponse(json.dumps(REGISTRATION_SUCCESS),
                                content_type="application/json")

    except Exception, e:

        print "[DeviceRegistrationException Occurred]::", e
        print "Registration unsuccessful"
        return HttpResponse(json.dumps(REGISTRATION_UNSUCCESSFUL), content_type="application/json")


@csrf_exempt
def test_function_structure(request):
    """
    Receives the uploaded CSV files and stores them in the database
    """

    try:
        if request.method == 'GET':
            return HttpResponse(json.dumps(ERROR_INVALID_REQUEST), content_type="application/json")

        if request.method == 'POST':
            pass
    except Exception, e:

            print "[TrainingDataException Occurred]::", e
            return HttpResponse(json.dumps(TRAINING_UNSUCCESSFUL),
                                content_type="application/json")


@csrf_exempt
def test_xmppclient(request):
    pass
