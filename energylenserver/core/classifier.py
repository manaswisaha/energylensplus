"""
Script to define the classfiers from individual sensor streams

Input: Training and Test set
Output: Classfied data frame

Date: Sep 18, 2014
Author: Manaswi Saha

"""

from energylenserver.core import audio as cs
from energylenserver.core import location as lc
from energylenserver.core import movement as acl
from energylenserver.common_imports import *
from energylenserver.models import functions as mod_func


stars = 40


def classify_location(event_time, apt_no, start_time, end_time, user_list):
    logger.debug("--Classifying location--")

    # Step1: Get data from radio map (training set) and test set

    # Get Wifi data
    data = mod_func.get_sensor_training_data("wifi", apt_no, user_list)
    train_df = read_frame(data, verbose=False)

    data = mod_func.get_sensor_data("wifi", "test", start_time, end_time, user_list)
    test_df = read_frame(data, verbose=False)

    # Format data

    # Classify

    return lc.determine_location(train_df, test_df)


def classify_sound(train_csv, test_csv, apt_no, idx):
    logger.debug("--Classifying sound--")
    # test_csv = cs.extract_features(test_csv, "test", apt_no, idx)
    return cs.classify_sound(train_csv, test_csv, apt_no, idx)


def classify_accl(test_csv, apt_no, idx):
    logger.debug("-" * stars)
    logger.debug("Accelerometer Prediction Process ")
    logger.debug("-" * stars)
    # train_csv = acl.extract_features(train_csv, "train", apt_no, idx)
    # test_csv = acl.extract_features(test_csv, "test", apt_no, idx)
    return acl.classify_accl_thres(test_csv, apt_no, idx)
