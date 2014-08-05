# from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from constants import *
from models.DataModels import *
from models.models import *
from preprocessing import audio

import csv
import json
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
# '''


def import_from_file(filename, csvfile):
    '''
    Imports the CSV file into appropriate model
    '''
    training_status = False

    print "<function called>"

    # Find the sensor from the filename and choose appropriate table
    filename_l = filename.split('_')
    device_id = int(filename_l[0])
    dev_id = RegisteredUsers.objects.get(dev_id__exact=device_id)
    sensor_name = filename_l[2]
    if sensor_name == 'Training':
        sensor_name = filename_l[3]
        training_status = True
    print "Sensor:", sensor_name

    if sensor_name is 'audio':
        # Store csv file
        filename = 'tmp/audio_log_' + dt.datetime.fromtimestamp(time.time()) + '.csv'

    # Initialize Model
    if training_status is True:
        model = FILE_MODEL_MAP['Training' + sensor_name]()
    else:
        model = FILE_MODEL_MAP[sensor_name]()

    # Get CSV data
    df_csv = pd.read_csv(csvfile)
    # print "Head\n", df_csv.head()

    # --Clean records before storing--
    # If audio data received, then preprocess before storing
    # if sensor_name in ['rawaudio']:
    #     print "Total records before pre-processing:", len(df_csv)
    #     df_csv = audio.format_data(df_csv)

    # Remove NAN timestamps
    df_csv.dropna(subset=[0], inplace=True)
    # Remove rows with 'Infinity' in MFCCs created
    if sensor_name is 'audio':
        df_csv = df_csv[df_csv.mfcc1 != '-Infinity']

    print "Total number of records to insert:", len(df_csv)

    # Store data in the model
    for idx in df_csv.index:
        record = list(df_csv.ix[idx])
        if sensor_name in ['audio']:
            print "\nRecord", record
        if model.save_data(dev_id, record) is True:
            if sensor_name in ['audio']:
                print "[", idx, "Saved]"
    print "Successful Upload!!"

    return True


@csrf_exempt
def upload_data(request):
    '''
    Receives the uploaded CSV files and stores them in the database
    '''

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

        print "[Exception Occurred]::", e
        return HttpResponse(json.dumps(UPLOAD_UNSUCCESSFUL), content_type="application/json")


@csrf_exempt
def register_device(request):
    '''
    Receives the registration requests from the mobile devices and
    stores user and device details in the database
    '''
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

            print "\n--User Registration Details--"
            print "RegID:", reg_id
            print "Username:", user_name
            print "Email ID:", email_id
            print "Device ID:", dev_id

            # Store user
            user = RegisteredUsers(dev_id=dev_id, reg_id=reg_id, name=user_name, email_id=email_id)
            user.save()
            print "Registration successful"
            return HttpResponse(json.dumps(REGISTRATION_SUCCESS),
                                content_type="application/json")

    except Exception, e:

        print "[Exception Occurred]::", e
        print "Registration unsuccessful"
        return HttpResponse(json.dumps(REGISTRATION_UNSUCCESSFUL), content_type="application/json")
