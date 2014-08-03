# from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from constants import *
from models.DataModels import *
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

    # Find the sensor from the filename and choose appropriate table
    filename_l = filename.split('_')
    sensor_name = filename_l[1]
    if sensor_name == 'Training':
        sensor_name = filename_l[2]
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

    # If audio data received, the preprocess before storing
    if sensor_name in ['rawaudio']:
        df_csv = audio.format_data(df_csv)
        print "[RawAudio Data Received]: Total number of records:", len(df_csv)
        print df_csv.head(15)

    # print "Head\n", df_csv.head()

    # --Sanitize records before storing--
    # Remove NAN timestamps
    df_csv.dropna(subset=[0], inplace=True)
    # Remove rows with 'Infinity' in MFCCs created
    if sensor_name is 'audio':
        df_csv = df_csv[df_csv.mfcc1 != '-Infinity']

    # Store data in the model
    for idx in df_csv.index[:10]:
        record = list(df_csv.ix[idx])
        if sensor_name in ['rawaudio', 'audio']:
            print "\nRecord", record
        if model.save_data(record) is True:
            if sensor_name in ['rawaudio', 'audio']:
                print "[", idx, "Saved]"

    return True


@csrf_exempt
def data_upload(request):
    '''
    Receives the uploaded CSV files and stores them in the database
    '''
    # name="uploadedfile";filename="/mnt/sdcard/EnergyLens+/light_log.csv"

    try:
        if request.method == 'GET':
            return HttpResponse(json.dumps(ERROR_INVALID_REQUEST), content_type="application/json")

        if request.method == 'POST':
            print "\n[POST Request Received]"

            payload = request.FILES
            print "Files Payload:\n", payload.items()
            file_container = payload['uploadedfile']
            filename = str(file_container.name)
            csvfile = file_container
            print "Filename:", filename

            # Store in the database
            if(import_from_file(filename, csvfile)):
                return HttpResponse(json.dumps(UPLOAD_SUCCESS), content_type="application/json")

            else:
                return HttpResponse(json.dumps(UPLOAD_UNSUCCESSFUL),
                                    content_type="application/json")

    except Exception, e:

        print "[Exception Occurred]::", e
        return HttpResponse(json.dumps(UPLOAD_UNSUCCESSFUL), content_type="application/json")
