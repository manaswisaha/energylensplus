"""
Script to extract features and classify sound events from the
test csv containing data from a time slice
Input feature vector form: <frame_no, input features[],label>
Output: classified sound event

Author: Manaswi Saha
Updated: Sep 29, 2013
"""

import os
import time
import random
import string

from django.conf import settings

import numpy as np
import pandas as pd
from sklearn.svm import SVC
from sklearn.externals import joblib
from django_pandas.io import read_frame

from constants import *
from common_imports import *
from energylenserver.audio.features import MFCC
from energylenserver.models import functions as mod_func
from energylenserver.preprocessing import audio as pre_p_a

base_dir = settings.BASE_DIR


def train_audio_classification_model(sensor, apt_no, phone_model):
    """
    Train Audio Classification model
    """

    # Get training data
    user_list = mod_func.get_users_for_training(apt_no, phone_model)
    data = mod_func.get_sensor_training_data(sensor, apt_no, user_list)
    train_df = read_frame(data, verbose=False)

    # Training features
    if sensor == "audio":
        features = train_df.columns[3:-2]

        # Cleaning
        if train_df.mfcc1.dtype != 'float64':
            train_df = train_df[train_df.mfcc1 != '-Infinity']
    else:
        # Format for classification
        train_df = pre_p_a.format_data_for_classification(train_df)

        # Extract features
        train_df = extract_features(train_df, "train", apt_no)
        features = train_df.columns[2:-2]

    classes = train_df['label'].unique()
    logger.debug("Appliances Classes :%s", classes)

    # Train SVM Model
    clf = SVC()
    clf.fit(train_df[features], train_df['label'].tolist())

    # Saving model into a disk
    dst_folder = os.path.join(base_dir, 'energylenserver/trained_models/audio/')
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)

    filename = str(apt_no) + "_" + phone_model + "_" + str(len(classes))
    model_file = filename + "_SVM_" + str(int(time.time()))
    joblib.dump(clf, dst_folder + model_file + '.pkl', compress=9)

    return clf


"""
Classify audio event for the data in the given time slice
and output the sound event

Input: sound data for a time frame
Output: sound event for that time frame

"""


def determine_appliance(sensor, train_model, test_df):

    try:
        if sensor == "audio":
            # Cleaning
            if test_df.mfcc1.dtype != 'float64':
                test_df = test_df[test_df.mfcc1 != '-Infinity']

            # Features
            features = test_df.columns[3:-2]
        else:
            features = test_df.columns[2:-2]

        # Run NB/GMM/SVM algorithm to predict sound events for the data points
        pred_label = train_model.predict(test_df[features])

        return pred_label

    except Exception, e:
        logger.exception("[AudioClassifierException]::%s", str(e))
        return False


def random_id():
    """
    Used for generating message ids
    Returns: a random alphanumerical id
    """

    rid = ''
    for x in range(8):
        rid += random.choice(string.ascii_letters + string.digits)
    return rid


def make_string(row):
    return row['label'] + '-' + row['location']


def extract_features(df, dataset_type, apt_no):

    try:
        dst_folder = os.path.join(base_dir, 'energylenserver/trained_models/audio/tmp/')
        if not os.path.exists(dst_folder):
            os.makedirs(dst_folder)

        if dataset_type == "train":
            # Temporary generate individual sound labeled files
            csv_files = []

            df['comb_label'] = df.apply(make_string, axis=1)
            classes = df.comb_label.unique()

            for class_i in classes:
                df_new = df[df.comb_label == class_i]
                filename = (dst_folder + str(int(time.time())) + "_" + class_i + "_" +
                            str(apt_no) + "_" + random_id() + ".csv")
                df_new.to_csv(filename, index=False)

                # Store created files in csv_files
                csv_files.append(filename)

            # logger.debug("Files: %s", csv_files)
            df_arr = [pd.read_csv(i) for i in csv_files]

            # Delete all the created csv files
            for the_file in csv_files:
                try:
                    os.unlink(the_file)
                except Exception, e:
                    logger.exception("[MFCCFileDeletionException]:: %s", e)
        else:
            df_arr = [df]

        """
        Audio Processing:
            Converting signal into frames, apply window to each frame
            and extract features from each frame
        """

        feature_vec = []
        for df_i in df_arr:

            if len(df_i) == 0:
                continue

            # Convert into 1-D numpy array
            timestamp = np.array(df_i.time)
            raw_values = np.array(df_i.value)  # audio signal
            label = np.array(df_i.label)[0]
            location = np.array(df_i.location)[0]

            """
            Preprocessing:
                framing, windowing, filtering
            """

            if raw_values.ndim > 1:
                print "INFO: Input signal has more than 1 channel; the channels will be averaged."
                raw_values = np.mean(raw_values, axis=1)

            # Framing
            frames = (len(raw_values) - MFCC.FRAME_LEN) / MFCC.FRAME_SHIFT + 1
            # logger.debug("Number of frames::%s", frames)

            # Windowing
            for f in range(frames):

                try:
                    sliced_raw_val = raw_values[
                        f * MFCC.FRAME_SHIFT: f * MFCC.FRAME_SHIFT + MFCC.FRAME_LEN]
                    frame = sliced_raw_val * MFCC.WINDOW
                except Exception, e:
                    logger.exception("WindowException: %s", e)
                    filename = dst_folder + str(time.time()) + 'rawvwindow_issue.txt'
                    sliced_raw_val.tofile(filename, sep=" ", format="%s")
                    continue

                time_val = timestamp[f * MFCC.FRAME_SHIFT: f * MFCC.FRAME_SHIFT + MFCC.FRAME_LEN]

                time_i = time_val[0]

                # f = frame number
                features = [time_i, f]

                """
                Feature Extraction(frame level):
                ZCR, Spectral {Entropy, Energy, Flux, Rolloff, Centroid}
                RMS, Energy, MFCC(13)

                """

                # Extracting MFCC Features
                mfcc_vec = MFCC.extract(frame).tolist()

                features = features + mfcc_vec + [label, location]

                # Forming a feature vector
                feature_vec.append(features)

        # Combined the individual data frames to make it into a single
        # labeled feature vector set
        feature_vec = np.row_stack(feature_vec)

        """
        Output:
            Creation of feature vector for every frame
        to be fed to the classifier with a label

        """
        lbl_list = ['mfcc_' + str(i) for i in range(1, 14)]
        feature_lbl_list = ['time', 'frame_no'] + lbl_list + ['label', 'location']
        features_df = pd.DataFrame(feature_vec, columns=feature_lbl_list)

    except Exception, e:
        logger.exception("[MFCCFeatureExtractionException]:: %s", e)
        return False

    return features_df
