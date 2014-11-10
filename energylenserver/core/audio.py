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
import sys

from django.conf import settings

import numpy as np
import pandas as pd
from sklearn.svm import SVC
from sklearn.externals import joblib

from constants import *
from common_imports import *

base_dir = settings.BASE_DIR


def train_audio_classfication_model(train_df, filename):
    """
    Train Audio Classification model
    """

    # Training features
    features = train_df.columns[1:-1]

    # Cleaning
    train_df = train_df[train_df.mfcc1 != '-Infinity']

    # Train SVM Model
    clf = SVC()
    clf.fit(train_df[features], train_df['label'])

    # Saving model into a disk
    dst_folder = os.path.join(base_dir, 'energylenserver/trained_models/audio/')
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)

    model_file = filename + "_SVM_" + str(int(time.time()))
    joblib.dump(clf, dst_folder + model_file + '.pkl', compress=9)

    return clf


"""
Classify audio event for the data in the given time slice
and output the sound event

Input: sound data for a time frame
Output: sound event for that time frame

"""


def determine_appliance(train_model, test_df):

    try:
        # Cleaning
        test_df = test_df[test_df.mfcc1 != '-Infinity']

        # Features
        features = test_df.columns[1:-1]

        # Run NB/GMM/SVM algorithm to generate sound events for the data points
        clf = train_model
        clf.fit(train_df[features], train_df['label'])
        pred_label = clf.predict(test_df[features])

        return pred_label

    except Exception, e:
        logger.error("[AudioClassifierException]::%s", str(e))
        return False


def extract_features(csvfile, dataset_type, apt_no, idx):

    # Input file
    df_ip = pd.read_csv(csvfile)

    # Output file
    feat_csv = ('Sound/' + dataset_type + '_data/testing/' + dataset_type + '_' +
                apt_no + '_' + str(idx) + '.csv')

    # Autogenerate ground truth information
    gfile = ''
    if dataset_type == "train":
        gfile = ("EnergyLens+/102A/ground_truth/" + dataset_type +
                 "_" + apt_no + "_1.csv")
    else:
        gfile = ("EnergyLens+/102A/ground_truth/" + dataset_type +
                 "_" + apt_no + "_" + str(idx) + ".csv")
    # gfile = ("Sound/ground_truth/testing/" + dataset_type +
    #          "_" + apt_no + "_" + str(idx) + ".csv")
    '''
    gfile_fp = open(gfile, 'w')
    writer = csv.writer(gfile_fp)
    gfile_header = ['start_time', 'end_time', 'label']
    writer.writerow(gfile_header)
    start_time = 0
    end_time = 0
    plabel = ''
    ptime = 0
    for i, row in enumerate(df_ip.values):
        time = row[0]
        label = row[2]
        if i == 0:
            start_time = time
            end_time = time
        elif plabel != label or (plabel == label and i == (len(df_ip) - 1)):
            end_time = ptime
            row_to_write = [start_time, end_time, plabel]
            writer.writerow(row_to_write)
            # print row_to_write
            start_time = time
        ptime = time
        plabel = label

    gfile_fp.close()
    '''
    # else:
    #     gfile = "CompleteDataSets/Apartment/Evaluation/ground_truth/test_102A_" + idx + ".csv"

    # Temporary generate individual sound labeled files
    csv_files = []
    df_gt = pd.read_csv(gfile)

    # if dataset_type == 'train':
    #     classes = df_gt.label.unique()
    # else:
    #     classes = df_gt.slabel.unique()

    classes = df_gt.slabel.unique()
    print classes
    for i in classes:
        df_new = df_ip[df_ip.label == i]
        new_loc = ('labeled_tmp/' + dataset_type + "_" + str(idx) + "_" + i + "_" +
                   apt_no + ".csv")
        df_new.to_csv(new_loc, index=False)

        # Store created files in csv_files
        csv_files.append(new_loc)

    # for i, row in enumerate(df_gt.values):
    #     df_new_tmp = df_ip.iloc[np.where(df_ip.time >= long(row[0]))]
    #     df_new = df_new_tmp.iloc[np.where(df_new_tmp.time <= long(row[1]))]
    #     label = row[2]
    #     new_loc = ('Sound/labeled_tmp/' + dataset_type + "_" + str(idx) + "_" + label + "_" +
    #                apt_no + "_" + str(i) + ".csv")
    #     df_new.to_csv(new_loc, index=False)

    # Store created files in csv_files
    #     csv_files.append(new_loc)

    print csv_files

    """
    Audio Processing:
        Converting signal into frames, apply window to each frame
        and extract features from each frame

    """

    df_arr = [pd.read_csv(i) for i in csv_files]
    feature_vec = []

    # print "FRAME_LEN", FRAME_LEN, "FRAME_SHIFT", FRAME_SHIFT
    for df_i in df_arr:

        if len(df_i) == 0:
            continue
        # Convert into 1-D numpy array
        time = np.array(df_i.time)     # timestamps

        # x is a wave signal saved in a 1-D numpy array
        x = np.array(df_i.value)

        label = np.array(df_i.label)[0]  # label

        """
        Preprocessing:
            framing, windowing, filtering

        """
        # Parameters (defined in audio_param.py)
        # FS = 8000                               # Sampling rate
        # FRAME_LEN = int(0.064 * FS)             # Frame length = 512 samples or 64ms
        # FRAME_SHIFT = int(0.032 * FS)           # Frame shift = 256
        # FFT_SIZE = 1024                         # How many points for FFT
        # WINDOW = MFCC.hamming(FRAME_LEN)        # Window function

        if x.ndim > 1:
            print "INFO: Input signal has more than 1 channel; the channels will be averaged."
            x = np.mean(x, axis=1)

        # Framing
        frames = (len(x) - FRAME_LEN) / FRAME_SHIFT + 1
        # print "Number of frames::", frames

        for f in range(frames):
            features = [f]

            # Windowing
            frame = x[f * FRAME_SHIFT: f * FRAME_SHIFT + FRAME_LEN] * WINDOW

            """
            Feature Extraction(frame level):
            ZCR, Spectral {Entropy, Energy, Flux, Rolloff, Centroid}
            RMS, Energy, MFCC(13)

            """

            # Extracting MFCC Features
            mfcc_vec = MFCC.extract(frame).tolist()

            features = features + mfcc_vec + [label]
            # features.append(label)

            # Forming a feature vector
            feature_vec.append(features)
            # print "Before:", feature_vec, f
            # feature_vec = list(itertools.chain.from_iterable(feature_vec))
            # print "After:", feature_vec

    # Combined the individual data frames to make it into a single
    # labeled feature vector set
    feature_vec = np.row_stack(feature_vec)
    # print feature_vec

    """
    Output:
        Creation of feature vector for every frame
    to be fed to the classifier with a label

    """
    lbl_list = ['mfcc_' + str(i) for i in range(1, 14)]
    feature_lbl_list = ['frame_no'] + lbl_list + ['label']
    new_df = pd.DataFrame(feature_vec, columns=feature_lbl_list)
    new_df.to_csv(feat_csv, index=False)

    # Delete all the created csv files
    folder_path = "Sound/labeled_tmp/"
    for the_file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, the_file)
        try:
            # if os.path.isfile(file_path):
            os.unlink(file_path)
        except Exception, e:
            print e

    return feat_csv
