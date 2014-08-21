# from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from constants import *
from models.DataModels import *
from models.models import *
from preprocessing import audio
from preprocessing import wifi
# from gcmxmppserver.messages import

import csv
import requests
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


class insertRecordThread(threading.Thread):

    def __init__(self, filename, sensorname, df, training_status, dev_id):
        threading.Thread.__init__(self)
        self.filename = filename
        self.sensor_name = sensorname
        self.df = df
        self.training_status = training_status
        self.dev_id = dev_id

    def run(self):
        print "\n---Starting ", self.filename
        insert_records(self.filename, self.sensor_name, self.df, self.training_status, self.dev_id)
        print "---Exiting ", self.filename


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


def insert_records(filename, sensor_name, df_csv, training_status, dev_id):
    """
    Function for each thread: performs some preprocessing and inserts records
    into the database
    """

    print "\n---Starting", filename, "---"

    # --Preprocess records before storing--
    if sensor_name == "wifi":
        df_csv = wifi.format_data(df_csv)

    # If audio data received, then preprocess before storing
    # if sensor_name in ['rawaudio']:
    #     print "Total records before pre-processing:", len(df_csv)
    #     df_csv = audio.format_data(df_csv)

    # Remove NAN timestamps
    df_csv.dropna(subset=[0], inplace=True)
    # Remove rows with 'Infinity' in MFCCs created
    if sensor_name == "audio":
        if str(df_csv.mfcc1.dtype) != 'float64':
            df_csv = df_csv[df_csv.mfcc1 != '-Infinity']

    print "Total number of records to insert:", len(df_csv)

    # Initialize Model
    if training_status is True:
        model = FILE_MODEL_MAP['Training' + sensor_name]
    else:
        model = FILE_MODEL_MAP[sensor_name]

    # Store data in the model
    # list_of_objects = model().save_data(dev_id, df_csv)
    # model.objects.bulk_create(list_of_objects)

    print "Inserting records..."
    for idx in df_csv.index:
        record = list(df_csv.ix[idx])
        model().save_data(dev_id, record)
        # if sensor_name in ['audio']:
        #     print "\nRecord", record
    now_time = "[" + time.ctime(time.time()) + "]"
    print now_time, "Successful Upload for", sensor_name, filename + "!!\n"


def import_from_file(filename, csvfile):
    """
    Imports the CSV file into appropriate db model
    """
    training_status = False

    print "<function called>"

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
    except Exception, e:
        if e == "Passed header=0 but only 0 lines in file":
            print "[Exception] No lines found in the file!"
            return True
    # print "Head\n", df_csv.head()

    """
    TODO: Find a better way than threading
    Try bulk_create
    """

    # Create and start new thread for inserting records
    insertThread = threading.Thread(target=insert_records, args=(
        filename, sensor_name, df_csv, training_status, dev_id))
    insertThread.start()

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
            print "\n[POST Request Received]"

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
            dev_id = payload['dev_id']
            print "Requested by:", dev_id

            # Check if it is a registered user
            is_user = user_exists(dev_id)
            if not is_user:
                return False
            else:
                pass
                # apt_no = is_user.apt_no
            apt_no = '1002'

            url = 'http://energy.iiitd.edu.in:9106/api/query'

            # Get power data
            payload = ("select data before now "
                       "where Metadata/Extra/FlatNumber ='" + apt_no + "' and "
                       "Metadata/Extra/PhysicalParameter='Power'")

            r = requests.post(url, data=payload)
            print r
            payload_body = r.json()
            print payload_body

            lpower = 0

            if len(payload_body) > 1:
                readings = payload_body[0]['Readings']
                time_1 = readings[0][0]
                power = readings[0][1]

                readings = payload_body[1]['Readings']
                time_2 = readings[0][0]
                lpower = readings[0][1]

                timestamp = max(time_1, time_2) / 1000

                # Handling power outages where meter data may not be the latest
                if abs(time_1 - time_2) > 2:
                    time_low = min(time_1, time_2) / 1000
                    now_time = time.time()

                    if abs(now_time - time_low) > 3:
                        if time_low == time_1:
                            power = 0
                        elif time_low == time_2:
                            lpower = 0

            else:
                readings = payload_body[0]['Readings']
                timestamp = readings[0][0]
                power = readings[0][1]

            total_power = power + lpower
            print "Power", power
            print "LPower", lpower
            payload = {}
            payload['time'] = timestamp
            payload['power'] = total_power

            return HttpResponse(json.dumps(payload), content_type="application/json")

    except Exception, e:

            print "[RealTimeDataException Occurred]::", e
            return HttpResponse(json.dumps(REALTIMEDATA_UNSUCCESSFUL),
                                content_type="application/json")


@csrf_exempt
def training_data(request):
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
def register_device(request):
    """
    Receives the registration requests from the mobile devices and
    stores user and device details in the database
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

            print "\n--User Registration Details--"
            print "RegID:", reg_id
            print "Username:", user_name
            print "Email ID:", email_id
            print "Device ID:", dev_id
            print "Apartment Number:", apt_no

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
                    dev_id=dev_id, reg_id=reg_id, name=user_name, email_id=email_id)
                user.save()
                print "Registration successful"
            return HttpResponse(json.dumps(REGISTRATION_SUCCESS),
                                content_type="application/json")

    except Exception, e:

        print "[DeviceRegistrationException Occurred]::", e
        print "Registration unsuccessful"
        return HttpResponse(json.dumps(REGISTRATION_UNSUCCESSFUL), content_type="application/json")


@csrf_exempt
def test_xmppclient(request):
    pass
