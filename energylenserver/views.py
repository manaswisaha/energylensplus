# from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

from common_imports import *
from models.models import *
from models.DataModels import *
from meter.functions import *
from meter.smap import *
from functions import *
from energylenserver.preprocessing import wifi
from energylenserver.api.reassign import *
from energylenserver.tasks import phoneDataHandler

import os
import sys
import json
import time
import pandas as pd
import datetime as dt


# Enable Logging
logger = logging.getLogger('energylensplus_django')

"""
Helper functions
"""


def user_exists(device_id):
    """
    Check whether user is registered
    """
    try:
        dev_id = RegisteredUsers.objects.get(dev_id__exact=device_id)
        return dev_id
    except RegisteredUsers.DoesNotExist, e:
        logger.error("[UserDoesNotExistException Occurred] No registration found!:: %s", e)
        return False

"""
Registration API
"""


@csrf_exempt
def register_device(request):
    """
    Receives the registration requests from the mobile devices and
    stores user-device and meter details in the database
    """

    try:
        if request.method == 'GET':
            return HttpResponse(json.dumps(ERROR_INVALID_REQUEST), content_type="application/json")

        if request.method == 'POST':
            logger.info("[POST Request Received] - %s", sys._getframe().f_code.co_name)

            # print request.body
            payload = json.loads(request.body)
            logger.debug("POST Payload:\n%s", payload)

            reg_id = payload['registration_id']
            user_name = payload['user_name']
            email_id = payload['email_id']
            dev_id = payload['dev_id']
            apt_no = payload['apt_no']
            home_ap = payload['home_ap']
            other_ap = payload['other_ap']

            logger.debug("\n--User Registration Details--")
            logger.debug("RegID:%s", reg_id)
            logger.debug("Username:%s", user_name)
            logger.debug("Email ID:%s", email_id)
            logger.debug("Device ID:%s", dev_id)
            logger.debug("Apartment Number:%s", apt_no)
            logger.debug("Home AP:%s", home_ap)
            logger.debug("Other APs:%s", other_ap)

            if apt_no.isdigit():

                # Store the meter details of the apt_no if the current user is the first
                # member of the house that registers

                apt_no = int(apt_no)
                user_count = RegisteredUsers.objects.filter(apt_no__exact=apt_no).count()
                logger.debug("Number of users registered for %d:%s", apt_no, user_count)
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

                logger.debug("Home AP:%s", home_ap)

                try:
                    AccessPoints.objects.filter(apt_no__exact=apt_no).delete()

                    # Store the access point details
                    ap_record = AccessPoints(
                        apt_no=apt_no, macid=home_ap['macid'], ssid=home_ap['ssid'], home_ap=True)
                    ap_record.save()

                    for ap in other_ap:
                        ap_record = AccessPoints(
                            apt_no=apt_no, macid=ap['macid'], ssid=ap['ssid'], home_ap=False)
                        ap_record.save()
                except Exception, e:
                    logger.error("[APSaveException]::%s" % (e))

            try:
                r = RegisteredUsers.objects.get(dev_id__exact=dev_id)
                logger.debug("Registration with device ID %s exists", r.dev_id)
                # Store user
                r.reg_id = reg_id
                r.name = user_name
                r.is_active = True
                if apt_no != 0:
                    r.apt_no = apt_no
                r.modified_date = dt.datetime.fromtimestamp(time.time())
                r.save()
                logger.debug("Registration updated")
            except RegisteredUsers.DoesNotExist, e:

                # Store user
                user = RegisteredUsers(
                    dev_id=dev_id, reg_id=reg_id, apt_no=apt_no, name=user_name, email_id=email_id)
                user.save()
                logger.debug("Registration successful")
            return HttpResponse(json.dumps(REGISTRATION_SUCCESS),
                                content_type="application/json")

    except Exception, e:

        logger.error("Registration unsuccessful")
        logger.error("[DeviceRegistrationException Occurred]::%s", e)
        return HttpResponse(json.dumps(REGISTRATION_UNSUCCESSFUL), content_type="application/json")

"""
Training API
"""


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
            logger.info("[POST Request Received] - %s", sys._getframe().f_code.co_name)
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
                logger.debug("Apartment Number:%d", apt_no)

            # Compute Power
            power = training_compute_power(apt_no, start_time, end_time)
            logger.debug("Computed Power::%f", power)

            # See if entry exists for appliance-location combination
            # Update power value if it exists
            try:
                r = Metadata.objects.get(apt_no__exact=apt_no, location__exact=location,
                                         appliance__exact=appliance)
                logger.debug(
                    "Metadata with entry:%d %s %s exists", r.apt_no, r.appliance, r.location)
                # Update power
                r.power = power
                r.save()
                logger.debug("Metadata record updated")
            except Metadata.DoesNotExist, e:

                # Store metadata
                user = Metadata(
                    apt_no=apt_no, appliance=appliance, location=location, power=power)
                user.save()
                logger.debug("Metadata creation successful")

            payload = {}
            payload['power'] = power
            return HttpResponse(json.dumps(payload),
                                content_type="application/json")

    except Exception, e:

        logger.error("[TrainingDataException Occurred]::%s", e)
        return HttpResponse(json.dumps(TRAINING_UNSUCCESSFUL),
                            content_type="application/json")


"""
Upload API
"""


def determine_user(filename):
    """
    Determines existence of user based on dev_id
    """
    # Find the sensor from the filename and choose appropriate table
    filename_l = filename.split('_')
    device_id = int(filename_l[0])

    # Check if it is a registered user
    is_user = user_exists(device_id)
    return is_user


def import_from_file(filename, csvfile):
    """
    Imports the CSV file into appropriate db model
    """

    filename_l = filename.split('_')

    user = determine_user(filename)
    if not user:
        return False

    logger.debug("User: %s", user.name)
    logger.debug("File size: %s", csvfile.size)

    training_status = False

    sensor_name = filename_l[2]
    if sensor_name == "Training":
        sensor_name = filename_l[3]
        training_status = True
    logger.debug("Sensor:%s", sensor_name)

    # Save file in a temporary location
    new_filename = ('data_file_' + sensor_name + '_' + str(
        user.dev_id) + '_' + time.ctime(time.time()) + '.csv')
    path = default_storage.save(new_filename, ContentFile(csvfile.read()))
    filepath = os.path.join(settings.MEDIA_ROOT, path)

    # Create a dataframe for preprocessing
    if sensor_name != 'rawaudio':
        try:
            df_csv = pd.read_csv(filepath)
            t = df_csv.label

            # --Preprocess records before storing--
            if sensor_name == 'wifi':
                df_csv = wifi.format_data(df_csv)

                if df_csv is False:
                    os.remove(filepath)
                    logger.error("[DataFileFormatIncorrect] "
                                 "Incorrect wifi file sent. Upload not successful!")
                    return False

                # Create temp wifi csv file
                os.remove(filepath)
                df_csv.to_csv(filepath, index=False)

        except Exception, e:
            if str(e) == "Passed header=0 but only 0 lines in file":
                logger.error(
                    "[Exception]:: Creation of dataframe failed! No lines found in the file!")
                os.remove(filepath)
                return False
            else:
                logger.error("[DataFileFormatIncorrect] Header missing!::%s", str(e))
                os.remove(filepath)
                return False

    # Call new celery task for importing records
    phoneDataHandler.delay(filename, sensor_name, filepath, training_status, user)

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
            logger.info("[POST Request Received] - %s" % sys._getframe().f_code.co_name)

            payload = request.FILES
            file_container = payload['uploadedfile']
            filename = str(file_container.name)
            csvfile = file_container
            logger.debug("File received:%s", filename)

            # Store in the database
            if(import_from_file(filename, csvfile)):
                return HttpResponse(json.dumps(UPLOAD_SUCCESS), content_type="application/json")

            else:
                return HttpResponse(json.dumps(UPLOAD_UNSUCCESSFUL),
                                    content_type="application/json")

    except Exception, e:

        logger.error("[UploadDataException Occurred]::%s", e)
        return HttpResponse(json.dumps(UPLOAD_UNSUCCESSFUL), content_type="application/json")


@csrf_exempt
def upload_stats(request):
    """
    Receives the uploaded notification CSV files and stores them in the database
    """

    try:
        if request.method == 'GET':
            return HttpResponse(json.dumps(ERROR_INVALID_REQUEST), content_type="application/json")

        if request.method == 'POST':
            logger.info("[POST Request Received] - %s", sys._getframe().f_code.co_name)

            payload = request.FILES
            file_container = payload['uploadedfile']
            filename = str(file_container.name)
            csvfile = file_container
            logger.debug("File received:%s", filename)

            # --- Saving file in the database ---
            # Check if it is a registered user
            user = determine_user(filename)
            if not user:
                return False

            # Save file in a temporary location
            new_filename = ('stats_screenlog_' + str(
                user.dev_id) + '_' + time.ctime(time.time()) + '.csv')
            path = default_storage.save(new_filename, ContentFile(csvfile.read()))
            filepath = os.path.join(settings.MEDIA_ROOT, path)

            # Store in the database
            UsageLogScreens().save_stats(user, filepath)
            return HttpResponse(json.dumps(UPLOAD_SUCCESS), content_type="application/json")

    except Exception, e:

        logger.error("[UploadStatsException Occurred]::%s", e)
        return HttpResponse(json.dumps(UPLOAD_UNSUCCESSFUL), content_type="application/json")

"""
Real Time Power Plots API
"""


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
            logger.info("[POST Request Received] - %s", sys._getframe().f_code.co_name)

            dev_id = payload['dev_id']
            logger.debug("Requested by:%s", dev_id)

            # Check if it is a registered user
            is_user = user_exists(dev_id)
            if not is_user:
                return HttpResponse(json.dumps(REALTIMEDATA_UNSUCCESSFUL),
                                    content_type="application/json")
            else:
                apt_no = is_user.apt_no
                logger.debug("Apartment Number:%d", apt_no)

            # Get power data
            timestamp, total_power = get_latest_power_data(apt_no)

            payload = {}
            payload[timestamp] = total_power

            logger.debug("Payload: %s", payload)

            return HttpResponse(json.dumps(payload), content_type="application/json")

    except Exception, e:

        logger.error("[RealTimeDataException Occurred]::%s", e)
        return HttpResponse(json.dumps(REALTIMEDATA_UNSUCCESSFUL),
                            content_type="application/json")


@csrf_exempt
def real_time_past_data(request):
    """
    Receives first real-time data access request for plots
    """

    try:
        if request.method == 'GET':
            return HttpResponse(json.dumps(ERROR_INVALID_REQUEST), content_type="application/json")

        if request.method == 'POST':

            payload = json.loads(request.body)
            logger.info("[POST Request Received] - %s", sys._getframe().f_code.co_name)

            dev_id = payload['dev_id']
            minutes = int(payload['minutes'])
            logger.debug("Requested by:%d", dev_id)
            logger.debug("For %d minutes", minutes)

            # Check if it is a registered user
            is_user = user_exists(dev_id)
            if not is_user:
                return HttpResponse(json.dumps(REALTIMEDATA_UNSUCCESSFUL),
                                    content_type="application/json")
            else:
                apt_no = is_user.apt_no
                logger.debug("Apartment Number:%s", apt_no)

            # Get power data
            end_time = time.time()
            start_time = end_time - 60 * minutes

            s_time = timestamp_to_str(start_time, date_format)
            e_time = timestamp_to_str(end_time, date_format)
            data_df_list = get_meter_data_for_time_slice(apt_no, s_time, e_time)

            if len(data_df_list) == 0:
                logger.debug("No data to send")
                return HttpResponse(json.dumps({}), content_type="application/json")

            # Creation of the payload
            payload = {}
            if len(data_df_list) > 1:
                # Combine the power and light streams
                df = combine_streams(data_df_list)
            else:
                df = data_df_list[0].copy()

            for idx in df.index:
                payload[df.ix[idx]['time']] = df.ix[idx]['power']

            payload_body = {}
            # Sorting payload
            for key in sorted(payload.iterkeys()):
                payload_body[key] = payload[key]

            logger.debug("Payload Size:%s", len(payload_body))
            # logger.debug("Payload", json.dumps(payload_body, indent=4)

            return HttpResponse(json.dumps(payload_body), content_type="application/json")

    except Exception, e:
        logger.error("[RealTimePastDataException Occurred]::%s", e)
        return HttpResponse(json.dumps(REALTIMEDATA_UNSUCCESSFUL),
                            content_type="application/json")


"""
Reassigning Inferences API
"""


@csrf_exempt
def reassign_inference(request):
    """
    Receives the ground truth validation report with corrected labels
    """
    try:
        if request.method == 'GET':
            return HttpResponse(json.dumps(ERROR_INVALID_REQUEST), content_type="application/json")

        if request.method == 'POST':
            payload = json.loads(request.body)
            logger.info("[POST Request Received] - %s", sys._getframe().f_code.co_name)

            dev_id = payload['dev_id']

            # Check if it is a registered user
            user = user_exists(dev_id)
            if not user:
                return HttpResponse(json.dumps(REASSIGN_UNSUCCESSFUL),
                                    content_type="application/json")
            else:
                apt_no = user.apt_no
                logger.debug("Apartment Number:%s", apt_no)

            logger.debug("\nCorrecting inferences..")
            options = payload['options']

            # Reassign the specified activity and update the db
            status = correct_inference(user, options)

            payload = {}
            payload['status'] = status

            logger.debug("\nSending status for correction of inferences..")

            return HttpResponse(json.dumps(payload),
                                content_type="application/json")

    except Exception, e:
        logger.error("[ReassignInferenceException Occurred]::", e)
        return HttpResponse(json.dumps(REASSIGN_UNSUCCESSFUL),
                            content_type="application/json")


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

        logger.error("[TrainingDataException Occurred]::", e)
        return HttpResponse(json.dumps(TRAINING_UNSUCCESSFUL),
                            content_type="application/json")


@csrf_exempt
def test_xmppclient(request):
    pass
