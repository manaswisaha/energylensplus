"""
Script to extract features and classify sound events from the
test csv containing data from a time slice
Input feature vector form: <frame_no, input features[],label>
Output: classified sound event

Author: Manaswi Saha
Updated: Sep 29, 2013
"""

import os
import csv
import sys
import pandas as pd
import numpy as np
from constants import *
# import MFCC as MFCC

from sklearn.svm import SVC
from sklearn import tree
# from sklearn.naive_bayes import GaussianNB
# from sklearn.mixture import GMM


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

"""
Classify Sound event for the data in the given time slice
and output the sound event

Input: sound data for a time frame
Output: sound event for that time frame

"""


def classify_sound(train_csv, test_csv, apt_no, idx):

    # Step1: Get data from training set and test set
    train_df = pd.read_csv(train_csv)
    test_df = pd.read_csv(test_csv)

    # train_df = train_df[train_df.label != 'Washing Machine']
    # train_df = train_df[train_df.label != 'None']

    # Using MFCC features calculated on phone
    # if 'mfcc1' in test_df.columns and 'mfcc1' in train_df.columns:
    #     train_df = train_df[train_df.mfcc1 != '-Infinity']
        # test_df = test_df[test_df.mfcc1 != '-Infinity']

    # Step2: Get features from the train_df
    features = train_df.columns[1:-1]
    # features = test_df.columns[1:-1]
    # print "Features::", features

    # Step3: Run NB/GMM/SVM algorithm to generate sound events for the data points
    # clf = GaussianNB()  # Naive Bayes
    clf = SVC()  # Linear SVM
    # clf = tree.DecisionTreeClassifier()  # Decision Tree
    clf.fit(train_df[features], train_df['label'])
    pred_label = clf.predict(test_df[features])
    # true_loc = test_df['label']

    # Step4: Store results in a csv and plot the csv with labels
    #cols_to_write = ['frame_no'] + features + ['label', 'pred_label']

    # File name generation
    train_csv_name = train_csv.split('/')[3].replace('.csv', '')
    new_csv = (test_csv.split('/')[3]).replace(
        '.csv', '_' + train_csv_name + '.csv')
    new_csv = 'Sound/output/testing/' + apt_no + "_" + new_csv
    new_df = test_df
    new_df['pred_label'] = pred_label
    new_df.to_csv(new_csv, index=False)

    # Step5: Check accuracy by comparing it with the ground truth
    # Plot confusion matrix
    print "\nSound Classification Accuracy..."
    train_classes = sorted(train_df.label.unique().tolist())
    test_classes = sorted(test_df.label.unique().tolist())
    pred_test_class = sorted(new_df.pred_label.unique().tolist())
    print "Train Classes: ", train_classes

    # Data points for the classes in the training set
    print "-" * 10, "Training Set", "-" * 10
    grp_loc_df = [train_df.iloc[np.where(train_df['label'] == i)]
                  for i in train_classes]
    for j in range(len(grp_loc_df)):
        print "Class", grp_loc_df[j].label.unique(), " : ", len(grp_loc_df[j])

    print "Test Classes: ", test_classes
    print "Predicted class::", pred_test_class

    # Selecting the label with maximum count
    pred_list = dict((i, list(pred_label).count(i)) for i in pred_test_class)
    print "Predicted list", pred_list
    grpcount_label = pd.DataFrame.from_dict(pred_list, orient="index")
    grpcount_label.columns = ['lcount']
    pred_label = grpcount_label[
        grpcount_label.lcount == grpcount_label.lcount.max()].index[0]
    print "Predicted Sound Label:", pred_label, "\n"
    return pred_label

if __name__ == '__main__':

    # Variables
    train_csv = sys.argv[1]		# training data set - train_data/train_1.csv
    test_csv = sys.argv[2]		# test data set - test_data/test_1.csv
    apt_no = sys.argv[3]
    idx = sys.argv[4]

    # Classify
    pred_label = classify_sound(train_csv, test_csv, apt_no, idx)
