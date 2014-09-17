"""
Script to classify accelerometer data
Input feature vector form: <time,x,y,z,label>
Output: <time, mean, variance, svm_pred_label, rms_pred_label, label>

Author: Manaswi Saha, Shailja Thakur
Date: Sep 25, 2013
"""

# import sys
import csv
import math
import pandas as pd
import numpy as np
from sklearn.svm import SVC
from sklearn import tree
# from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
#from Accelerometer.plot_classified import plot_classified

THRESHOLD = 8.9


def extract_features(csvfile, dataset_type, apt_no, idx):

    print "Extracting Features for ", csvfile
    print "-" * 80

    # Input file
    ip_df = pd.read_csv(csvfile)

    # Dataset Type
    if dataset_type == "train":
        mod_csv = 'Accelerometer/train_data/testing/train_' + \
            apt_no + '_' + str(idx) + '.csv'
    else:
        mod_csv = 'Accelerometer/test_data/testing/test_' + \
            apt_no + '_' + str(idx) + '.csv'
    writer = csv.writer(open(mod_csv, 'w'))

    # Variables
    # length = len(list(csv.reader(open(csvfile))))
    rownum = 0
    list1 = []
    data = []
    time = 0
    mean = 0.0
    variance = 0.0
    sum1 = 0
    no_of_samples = 40

    # Creation of CSV file with features
    header = ["time", "mean", "variance", "label"]
    writer.writerow(header)

    # ............CALCULATING RMS VALUES..........

    for row in ip_df.values:
        try:

            rownum += 1
            x = float(row[1])
            y = float(row[2])
            z = float(row[3])
            rms = math.sqrt(x * x + y * y + z * z)
            # print rms, row[4]
            mean += rms

            list1.append(rms)

            if rownum == 1:

                time = row[0]

                if row[4] == "On Table":
                    label = 0

                if row[4] == "On User":
                    label = 1

            if rownum == 41:
                mean /= float(no_of_samples)

                i = 0
                sum1 = 0.0
                try:
                    # print "BLOCK", "*" * 80
                    # print len(list1)
                    while(i <= no_of_samples):
                        # print list1[i]
                        sum1 += pow((mean - list1[i]), 2)
                        i += 1

                except Exception, e:
                    print e

                variance = sum1 / no_of_samples

                data = [time, mean, variance, label]
                writer.writerow(data)

                mean = 0
                rownum = 0
                list1 = []

        except Exception, e:
            print e

    return mod_csv


def classify_accl(train_csv, test_csv, apt_no, idx):

    # Step1: Get data from training set and test set
    train_df = pd.read_csv(train_csv)
    test_df = pd.read_csv(test_csv)
    print "Training Set:: ", train_csv
    print "Test Set:: ", test_csv

    # Step2: Get features from the train_df
    features = train_df.columns[1:-1]
    print features

    # Step3: Classification

    # Using RMS Thresholding
    # print "Predicting using RMS thresholding", '.' * 10

    # i = 0
    # rms_pred = []
    # test_mean = test_df['mean']
    # while (i < len(test_mean)):

    #     if test_mean[i] <= THRESHOLD:
    #         predicted_label = 0
    #     else:
    #         predicted_label = 1
    #     rms_pred.append(predicted_label)
    #     i += 1

    # Running NB/GMM/SVM algorithm to generate sound events for the data
    # points
    print "Classifying using DT", '.' * 10

    # clf = GaussianNB()  # Naive Bayes
    # clf = SVC()	 # Linear SVM
    clf = tree.DecisionTreeClassifier()
    try:
        clf.fit(train_df[features], train_df['label'])
    except Exception, e:
        print e
    pred = clf.predict(test_df[features])
    true_loc = test_df['label']

    # Step4: Store results in a csv and plot the csv with labels
    # cols_to_write =  ['time'] + features + ['label', 'svm_pred_label', 'rms_pred_label']
    # File name generation
    train_csv_name = train_csv.split('/')[3].replace('.csv', '')
    new_csv = (test_csv.split('/')[3]).replace(
        '.csv', '_' + train_csv_name + '.csv')
    # print "New File Name", new_csv
    new_csv = 'Accelerometer/output/' + \
        apt_no + "_" + str(idx) + "_" + new_csv
    new_df = test_df
    new_df['pred_label'] = pred
    # new_df['rms_pred_label'] = rms_pred
    new_df.to_csv(new_csv, index=False)

    # Step5: Check accuracy by comparing it with the ground truth
    # Plot confusion matrix
    classes = sorted(train_df.label.unique())
    print "Classes: ", classes
    test_classes = sorted(test_df.label.unique())
    print "Test classes: ", test_classes

    # Data points for the classes in the training set
    print "-" * 10, "Training Set", "-" * 10
    grp_loc_df = [train_df.iloc[np.where(train_df['label'] == k)]
                  for k in classes]
    for j in range(len(grp_loc_df)):
        print "Class", grp_loc_df[j].label.unique(), " : ", len(grp_loc_df[j])

    # Data points for the classes in the test set
    print "-" * 10, "Test Set", "-" * 10
    grp_loc_df = [test_df.iloc[np.where(test_df['label'] == k)]
                  for k in classes]
    for j in range(len(grp_loc_df)):
        print("Class %s : %d" %
              (grp_loc_df[j].label.unique(), len(grp_loc_df[j])))

    # str_classes = ["On Table", "On User"]
    # Accuracy for RMS thresholding
    # print ""
    # print "-" * 10, "RMS Thresholding Accuracy", "-" * 10
    # cm = confusion_matrix(true_loc, rms_pred)
    # print "Confusion Matrix:: "
    # print cm

    # Print Classification report
    # rms_cls_report = (classification_report(true_loc,
    #                                         rms_pred,
    #                                         labels=classes, target_names=str_classes))
    # print "Classification Report::"
    # print rms_cls_report

    # Accuracy for DT Classification
    # print "-" * 10, "DT Classification Accuracy", "-" * 10
    # cm = confusion_matrix(true_loc, pred)
    # print "Confusion Matrix:: "
    # print cm

    # Print Classification report
    # cls_report = (classification_report(true_loc, pred))
    # print "DT Classification Report"
    # print cls_report

    # Overall Accuracy
    true = new_df.label
    # rmspred = new_df.rms_pred_label
    dtpred = new_df.pred_label
    # r_mis_labeled = (true != rmspred).sum()
    s_mis_labeled = (true != dtpred).sum()
    total = len(true)
    # r_accuracy = float(total - r_mis_labeled) / total * 100
    s_accuracy = float(total - s_mis_labeled) / total * 100
    # print("Number of mislabeled points for RMS Thres : %d" %
    #       (true != rmspred).sum())
    print("Number of mislabeled points for DT : %d" % (true != dtpred).sum())
    print("Total number of test data points: %d" % total)
    # print "Overall RMS Accuracy:", r_accuracy
    print "Overall DT Accuracy:", s_accuracy

    return new_df


def classify_accl_thres(csvfile, apt_no, idx):

        # Input
    ip_df = pd.read_csv(csvfile)

    label = []
    pred_label = []
    for row in ip_df.values:
        try:
            x = row[1]
            y = row[2]
            z = row[3]
            if (float(x) >= -2 and float(x) <= 1 and float(y) >= -2
                    and float(y) <= 1 and float(z) >= 8 and float(z) <= 10):
                pred_label.append(0)
            else:
                pred_label.append(1)

            if row[4] == "On Table":
                label.append(0)
            else:
                label.append(1)

        except Exception, e:
            print e

    # Store results in a csv and plot the csv with labels
    # cols_to_write =  ['time'] + features + ['label', 'svm_pred_label', 'rms_pred_label']
    # File name generation
    name_split = csvfile.split('/')
    print "Name split", name_split
    if len(name_split) > 5:
        new_csv = name_split[4] + "_" + name_split[5]
    if len(name_split) > 4:
        new_csv = name_split[3] + "_" + name_split[4]
    else:
        new_csv = name_split[2] + "_" + name_split[3]
    new_csv = 'Accelerometer/output/testing/' + new_csv
    new_df = ip_df
    new_df['label'] = label
    new_df['pred_label'] = pred_label
    new_df.to_csv(new_csv, index=False)

    true = new_df.label
    pred = new_df.pred_label

    # Print Classification report
    cls_report = classification_report(true, pred)
    print "Classification Report"
    print cls_report

    # Overall Accuracy
    mis_labeled = (true != pred).sum()
    total = len(true)
    accuracy = float(total - mis_labeled) / total * 100
    print("Number of mislabeled points: %d" % (true != pred).sum())
    print("Total number of test data points: %d" % total)
    print "Overall Accuracy:", accuracy

    return new_df

if __name__ == '__main__':

    # Variables
    # train_csv = sys.argv[1]		# training data set - train_data/train_1.csv
    # test_csv = sys.argv[2]		# test data set - test_data/test_1.csv
    # apt_no = sys.argv[3]		# apartment number

    # Raw input files
    train_csv = ('CompleteDataSets/Apartment/'
                 '23Sep - Wifi_TrainingSet/Accl_1BHK_102A.csv')
    test_csv = ('CompleteDataSets/Apartment/'
                '30_9_17_58_30_9_20_16/Accl_1BHK_102A.csv')
    idx = 5

    # Input files for the classifier
    # train_csv = extract_features(train_csv, "train", idx)
    # test_csv = extract_features(test_csv, "test", idx)
    apt_no = '102A'

    # Classify
    output_df = classify_accl(train_csv, test_csv, apt_no, idx)
    thres_output_df = classify_accl_thres(test_csv, apt_no, idx)
    print "Predicted Class::", thres_output_df.pred_label.unique()

    # Plot
    #plot_classified(output_df, thres_output_df, test_csv)
