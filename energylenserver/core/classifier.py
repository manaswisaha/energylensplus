"""
Script to define the classfiers from individual sensor streams

Input: Training and Test set
Output: Classfied data frame

Date: Sep 18, 2014
Author: Manaswi Saha

"""

import os

from sklearn.externals import joblib

from energylenserver.core import audio
from energylenserver.core import location as lc
from energylenserver.core import movement as acl
from energylenserver.common_imports import *
from energylenserver.models import functions as mod_func
from energylenserver.preprocessing import wifi as pre_p
from common_imports import *
from django_pandas.io import read_frame


stars = 40


def get_trained_model(sensor, apt_no, phone_model):
    """
    Get trained model or train model if isn't trained
    """
    if sensor == "wifi":
        # Future TODO: Adding new localization models
        return
    if sensor == "audio":
        dst_folder = os.path.join(base_dir, 'energylenserver/trained_models/audio/')
        folder_listing = os.listdir(dst_folder)
        for file_i in folder_listing:
            filename_arr = file_i.split("_")
            # Use model if exists
            if filename_arr[0] == str(apt_no) and filename_arr[1] == phone_model:
                model = joblib.load(filename)
            else:
                # Else create a new training model
                filename = str(apt_no) + "_" + phone_model
                model = audio.train_audio_classfication_model(train_df, filename)
            return model


def classify_location(event_time, apt_no, start_time, end_time, user_list):
    logger.debug("[Classifying location]..")

    location_label = {}

    # Get user details
    users = mod_func.get_users(user_list)

    for user in users:
        dev_id = user.dev_id
        pmodel = user.phone_model

        # Get Wifi data
        user_list = get_users_for_training(apt_no, pmodel)
        data = mod_func.get_sensor_training_data("wifi", apt_no, user_list)
        train_df = read_frame(data, verbose=False)

        data = mod_func.get_sensor_data("wifi", "test", start_time, end_time, [dev_id])
        test_df = read_frame(data, verbose=False)

        # Format data for classification
        train_df = pre_p.format_data_for_classification(train_df)
        test_df = pre_p.format_data_for_classification(test_df)

        # Classify
        location = lc.determine_location(train_df, test_df)
        if not location:
            return
        location_label[dev_id] = location

    return location_label


def classify_appliance(event_time, apt_no, start_time, end_time, user_list):
    logger.debug("[Classifying appliance]..")

    appliance_label = {}

    # Get user details
    users = mod_func.get_users(user_list)

    for user in users:
        dev_id = user.dev_id
        pmodel = user.phone_model

        # Get trained model
        train_model = get_trained_model("audio", pmodel)

        # Get test data
        data = mod_func.get_sensor_data("audio", "test", start_time, end_time, [dev_id])
        test_df = read_frame(data, verbose=False)

        # Classify
        appliance = audio.determine_appliance(train_model, test_df)
        if not appliance:
            return
        appliance_label[dev_id] = appliance

    return appliance_label


def classify_movement(test_csv, apt_no, idx):
    logger.debug("-" * stars)
    logger.debug("[Classifying motion]..")
    logger.debug("-" * stars)
    # train_csv = acl.extract_features(train_csv, "train", apt_no, idx)
    # test_csv = acl.extract_features(test_csv, "test", apt_no, idx)
    return acl.classify_accl_thres(test_csv, apt_no, idx)
