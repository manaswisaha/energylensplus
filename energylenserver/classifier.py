"""
Script to define the classfiers from individual sensor streams

Input: Training and Test set
Output: Classfied data frame

Date: Sep 25, 2013
Author: Manaswi Saha

"""

import audio.classify_sound as cs
import localize as lc
import classify_accl as acl


stars = 40


def classify_sound(train_csv, test_csv, apt_no, idx):

    test_csv = cs.extract_features(test_csv, "test", apt_no, idx)
    return cs.classify_sound(train_csv, test_csv, apt_no, idx)


def classify_location(train_csv, test_csv, apt_no, idx):
    train_csv = lc.format_data(train_csv, "train", apt_no, idx)
    test_csv = lc.format_data(test_csv, "test", apt_no, idx)
    return lc.classify_location(train_csv, test_csv, apt_no, idx)


def classify_location_slice(train_csv, test_csv, apt_no, idx):
    test_csv = lc.format_data(test_csv, "test", apt_no, idx)
    return lc.classify_location_piecewise(train_csv, test_csv, apt_no, idx)


def classify_accl(test_csv, apt_no, idx):
    print "-" * stars
    print "Accelerometer Prediction Process "
    print "-" * stars
    # train_csv = acl.extract_features(train_csv, "train", apt_no, idx)
    # test_csv = acl.extract_features(test_csv, "test", apt_no, idx)
    return acl.classify_accl_thres(test_csv, apt_no, idx)
