# Script to localize a user using k-NN algorithm
# Assumptions:
# 	1. Averaged over one second
# Author: Manaswi Saha
# Updated on: Sep 27, 2013


import csv
import sys
import pandas as pd
import numpy as np
# from sklearn.neighbors import KNeighborsClassifier
# from sklearn.metrics import confusion_matrix
# from sklearn.metrics import classification_report
#
# import plot_confusion_matrix as pltcm
from CONFIGURATION import WIFI_THRESHOLD
# import summarize as sm

import warnings

warnings.filterwarnings('ignore')

# Script to convert labeled phone Wifi test data into the desired form
# Format::
# Location Fingerprint: <time, rssi1, rssi2, rssi3,..., rssiN, location>
# Number of RSSI features: number of unique SSID:MACs seen in the data
# Operations done:
#	1. Averaging over a second
#	2. Conversion to proper format
#
# Author: Manaswi Saha
# Date: August 30, 2013


def wifi_location(test_csv):

    # Step1: Get data from radio map test set
    test_df = pd.read_csv(test_csv)

    # Step2: Testing Hostel access point existence
    # Retrieve unique mac_ids
    rssi_avg = 0
    loc = []
    time = []
    avg_mac_0 = []
    mac_id = pd.Series(test_df.columns[2:-2])
    mac_gnd_flr = mac_id[mac_id.str.contains('cb:5c:19:', na=False) is True]
    mac_ft_flr = mac_id[(mac_id.str.contains('c4:0a:cb:25:db:', na=False) is True) | (
        mac_id.str.contains('c4:0a:cb:25:96:', na=False) is True)]

    print "Mac ground floor"
    print mac_gnd_flr
    print "Mac first floor"
    print mac_ft_flr
    # Determine in/out(1/0) of the hospital
    for i in test_df.index:
        # Check for connection with nearest APs
        if (len(mac_gnd_flr) > 0):
            for mac_id in mac_gnd_flr:
                avg_mac_0.append(test_df.ix[i][mac_id])

            rssi_avg = np.mean(avg_mac_0)

            if (rssi_avg < 0) & (rssi_avg > WIFI_THRESHOLD):

                location = 1
                loc.append(location)
                time.append(test_df.ix[i]['timestamp'])
            else:
                print 'greater then WIFI_THRESHOLD'
                print rssi_avg
            avg_mac_0 = []
        # Check for connection with APs in affinity
        elif (len(mac_ft_flr) > 0):
            for mac_id in mac_ft_flr:
                avg_mac_0.append(test_df.ix[i][mac_id])
            rssi_avg = np.mean(avg_mac_0)

            if ((rssi_avg < 0) & (rssi_avg > WIFI_THRESHOLD)):

                location = 1
                loc.append(location)
                time.append(test_df.ix[i]['timestamp'])
            avg_mac_0 = []
        # Outside
        else:
            loc_status = 0
            loc.append(loc_status)
            time.append(test_df.ix[i]['timestamp'])

    # print time, loc
    print "test_df length", len(test_df)
    df_loc = pd.DataFrame({'timestamp': time, 'location': loc})

    return df_loc

# Author: Manaswi Saha
# Date: August 29, 2013


def classify_location(train_csv, test_csv, apt_no, idx):

    # Step1: Get data from radio map (training set) and test set
    train_df = pd.read_csv(train_csv)
    train_df = train_df[train_df.label != 'Bathroom1']
    train_df = train_df[train_df.label != 'Bedroom3']
    train_df = train_df[train_df.label != 'Bedroom1']
    train_df = train_df[train_df.label != 'Shared Bathroom']
    test_df = pd.read_csv(test_csv)

    # Step2: Check both sets are compatible.
    # If they are not, use the SSIDs which are common to both
    # train_col = (train_df.shape)[1]
    # test_col = (test_df.shape)[1]

    # get rssi columns from each set
    train_col_names = train_df.columns[1:len(train_df.columns) - 1]
    test_col_names = test_df.columns[1:len(test_df.columns) - 2]

    # Find the common rssi columns
    print "-" * 30, "Using multiple access point", "-" * 30
    features = list(set(test_col_names) & set(train_col_names))

    # Testing with the residence access point
    # print "-"*30, "Using single access point", "-"*30
    # features = ['c4:0a:cb:2d:87:a0']
    # print "Training set columns::", train_col_names, "\nTest set::", test_col_names
    print "Features::", features

    # Step3: Localizing the user
    total_rows = (test_df.shape)[0]
    print "Total number of test data points:", total_rows
    if len(features) == 0:
        print "Labeling it with Outside"
        pred_loc = ["Outside" * total_rows]
    else:
        # Run KNN or NNSS algorithm to generate locations for the data points
        n = 5
        print "Using n::", n
        # clf = KNeighborsClassifier(n_neighbors=n,weights='distance')
        clf = KNeighborsClassifier(n_neighbors=n)
        clf.fit(train_df[features], train_df['label'])
        pred_loc = clf.predict(test_df[features])
    true_loc = test_df['label']

    # Step4: Store results in a csv and plot the csv with labels
    # cols_to_write =  ['timestamp'] + features + ['location']
    train_csv_name = train_csv.split('/')[3].replace('.csv', '')
    new_csv = (test_csv.split('/')[3]).replace(
        '.csv', '_' + train_csv_name + '.csv')
    new_csv = 'Wifi/output/testing/' + apt_no + "_n" + str(n) + "_" + new_csv
    new_df = test_df
    new_df['pred_label'] = pred_loc
    new_df.to_csv(new_csv, index=False)

    # Step5: Check accuracy by comparing it with the ground truth
    # Plot confusion matrix
    classes = sorted(test_df.label.unique().tolist())
    print "Classes: ", classes

    # Data points for the classes in the training set
    print "-" * 10, "Training Set", "-" * 10
    grp_loc_df = [train_df.iloc[np.where(train_df['label'] == i)]
                  for i in classes]
    for j in range(len(grp_loc_df)):
        print "Class", grp_loc_df[j].label.unique(), " : ", len(grp_loc_df[j])

    # Data points for the classes in the test set
    print "-" * 10, "Test Set", "-" * 10
    grp_loc_df = [test_df.iloc[np.where(test_df['label'] == i)]
                  for i in classes]
    for j in range(len(grp_loc_df)):
        print("Class %s : %d" %
              (grp_loc_df[j].label.unique(), len(grp_loc_df[j])))

    cm = confusion_matrix(true_loc.tolist(), pred_loc.tolist())
    print "-" * 20
    print "Confusion Matrix:: "
    print cm

    # Print Classification report
    cls_report = (classification_report(true_loc.tolist(),
                                        pred_loc.tolist(),
                                        labels=classes, target_names=classes))
    print cls_report

    # Overall Accuracy
    true = new_df.label
    pred = new_df.pred_label
    mis_labeled = (true != pred).sum()
    total = len(true)
    accuracy = float(total - mis_labeled) / total * 100
    print("Number of mislabeled points : %d" % (true != pred).sum())
    print("Total number of points: %d" % total)
    print "Overall Accuracy:", accuracy

    # Show confusion matrix in a separate window
    # train_csv_name = train_csv.split('/')[3].replace('.csv', '')
    # imgname = (test_csv.split('/')[3]).replace('.csv', '.png')
    # imgname = imgname.replace(
    #     '.png', '_' + train_csv_name + '_dist_n' + str(n) + '.png')
    # print "Imagename::", imgname, "\n"
    # pltcm.plot_cm(cm, "Wifi", classes, imgname, n)

    return new_df


def classify_location_piecewise(train_csv, test_csv, apt_no, idx):

    # Step1: Get data from radio map (training set) and test set
    train_df = pd.read_csv(train_csv)
    test_df = pd.read_csv(test_csv)

    # Step2: Check both sets are compatible.
    # If they are not, use the SSIDs which are common to both
    # train_col = (train_df.shape)[1]
    # test_col = (test_df.shape)[1]

    # get rssi columns from each set
    train_col_names = train_df.columns[1:len(train_df.columns) - 1]
    test_col_names = test_df.columns[1:len(test_df.columns) - 2]

    # Find the common rssi columns
    # print "-" * 30, "Using multiple access point", "-" * 30
    features = list(set(test_col_names) & set(train_col_names))

    # Testing with the residence access point
    # print "-"*30, "Using single access point", "-"*30
    # features = ['c4:0a:cb:2d:87:a0']
    # print "Training set columns::", train_col_names, "\nTest set::", test_col_names
    print "Features::", features

    # Step3: Localizing the user
    total_rows = (test_df.shape)[0]
    print "Total number of test data points:", total_rows
    if len(features) == 0:
        print "Labeling it with Outside"
        pred_loc = ["Outside" * total_rows]
    else:
        # Run KNN or NNSS algorithm to generate locations for the data points
        n = 5
        print "Using n::", n
        # clf = KNeighborsClassifier(n_neighbors=n,weights='distance')
        clf = KNeighborsClassifier(n_neighbors=n)
        clf.fit(train_df[features], train_df['label'])
        pred_loc = clf.predict(test_df[features])
    true_loc = test_df['label']

    # Step4: Store results in a csv and plot the csv with labels
    # cols_to_write =  ['timestamp'] + features + ['location']
    train_csv_name = train_csv.split('/')[3].replace('.csv', '')
    new_csv = (test_csv.split('/')[3]).replace(
        '.csv', '_' + train_csv_name + '.csv')
    new_csv = 'Wifi/output/testing/' + apt_no + "_n" + str(n) + "_" + new_csv
    new_df = test_df
    new_df['pred_label'] = pred_loc
    new_df.to_csv(new_csv, index=False)

    # Step5: Check accuracy by comparing it with the ground truth
    # Plot confusion matrix
    train_classes = sorted(train_df.label.unique().tolist())
    test_classes = sorted(test_df.label.unique().tolist())
    pred_test_class = sorted(new_df.pred_label.unique().tolist())
    print "Train Classes: ", train_classes
    print "Test Classes: ", test_classes
    print "Predicted Classes", pred_test_class

    # Data points for the classes in the training set
    print "-" * 10, "Training Set", "-" * 10
    grp_loc_df = [train_df.iloc[np.where(train_df['label'] == i)]
                  for i in test_classes]
    for j in range(len(grp_loc_df)):
        print "Class", grp_loc_df[j].label.unique(), " : ", len(grp_loc_df[j])

    # Data points for the classes in the test set
    print "-" * 10, "Test Set", "-" * 10
    grp_loc_df = [test_df.iloc[np.where(test_df['label'] == i)]
                  for i in test_classes]
    for j in range(len(grp_loc_df)):
        print("Class %s : %d" %
              (grp_loc_df[j].label.unique(), len(grp_loc_df[j])))

    # Print Classification report
    cls_report = (classification_report(true_loc.tolist(),
                                        pred_loc.tolist(),
                                        labels=test_classes, target_names=train_classes))
    print cls_report

    # Overall Accuracy
    true = new_df.label
    pred = new_df.pred_label
    mis_labeled = (true != pred).sum()
    total = len(true)
    accuracy = float(total - mis_labeled) / total * 100
    print("Number of mislabeled points : %d" % (true != pred).sum())
    print("Total number of points: %d" % total)
    print "Overall Accuracy:", accuracy

    # Show confusion matrix in a separate window
    # train_csv_name = train_csv.split('/')[3].replace('.csv', '')
    # imgname = (test_csv.split('/')[3]).replace('.csv', '.png')
    # imgname = imgname.replace(
    #     '.png', '_' + train_csv_name + '_dist_n' + str(n) + '.png')
    # print "Imagename::", imgname, "\n"
    # pltcm.plot_cm(cm, "Wifi", classes, imgname, n)

    # Selecting the label with maximum count
    pred_list = dict((i, list(pred_loc).count(i)) for i in pred_test_class)
    print "\nPredicted list", pred_list
    grpcount_label = pd.DataFrame.from_dict(pred_list, orient="index")
    grpcount_label.columns = ['lcount']
    pred_label = grpcount_label[
        grpcount_label.lcount == grpcount_label.lcount.max()].index[0]
    print "Predicted Location Label:", pred_label
    return pred_label

if __name__ == '__main__':

    # Variables
    # train_csv = sys.argv[1]		# training data set - Wifi/radiomap/apt_no_idx.csv
    # test_csv = sys.argv[2]		# test data set - Wifi/test_data/apt_no_idx.csv
    # apt_no = sys.argv[3]
    # idx = sys.argv[4]

    train_csv = ('CompleteDataSets/Apartment/'
                 '23Sep - Wifi_TrainingSet/Wifi_1BHK_102A.csv')
    test_csv = ('CompleteDataSets/Apartment/'
                '23Sep - Meter_Wifi_Sound_Accl/Wifi_1BHK_102A.csv')
    apt_no = '102A'
    idx = 3
    # Classify
    train_csv = format_data(train_csv, "train", apt_no, idx)
    test_csv = format_data(test_csv, "test", apt_no, idx)
    output_df = classify_location(train_csv, test_csv, apt_no, idx)

    # ------------------------------------------------------------------------
    # TESTING: To check which n gives the highest overall accuracy
    # results = []
    # true_loc = test_df['true_label']

    # for n in range(1, 101, 2):
    #     clf = KNeighborsClassifier(n_neighbors=n,weights='distance')
    #     clf = KNeighborsClassifier(n_neighbors=n)
    #     clf.fit(train_df[features], train_df['location'])
    #     pred_loc = clf.predict(test_df[features])

    #     accuracy = (np.where(pred_loc==test_df['true_label'],
    #						    1, 0).sum() / float(len(test_df.index)))
    #     print "Neighbors: %d, Accuracy: %3f" % (n, accuracy)

    #     results.append([n, accuracy])

    # results = pd.DataFrame(results, columns=["n", "accuracy"])

    # pl.plot(results.n, results.accuracy)
    # pl.title("Accuracy with Increasing K with weights parameter " + test_csv)
    # pl.show()

    # TESTING: To check which n gives the highest accuracy class wise
    # results = []
    # true_loc = test_df['true_label']
    # true_loc = train_df['location']
    # classes = sorted(test_df.true_label.unique().tolist())
    # print "Classes: ", classes
    # no_of_classes = len(classes)
    # print "Number of classes", no_of_classes
    # acc_col_name = ['accuracy'+str(i) for i in range(no_of_classes)]
    # accuracy = []
    # total_no = test_df.groupby(['true_label']).size()
    # total_no = train_df.groupby(['location']).size()
    # print total_no

    # for n in range(1, 101, 2):
    # 	print "------Classifying with n = ", n ,"--------------"
    # clf = KNeighborsClassifier(n_neighbors=n,weights='distance')
    # 	clf = KNeighborsClassifier(n_neighbors=n)
    # 	clf.fit(train_df[features], train_df['location'])
    # clf.fit(test_df[features], test_df['true_label'])
    # 	pred_loc = clf.predict(test_df[features])

    # 	cm = confusion_matrix(true_loc, pred_loc)
    # 	print cm

    # 	for i, row in enumerate(cm):
    # 		percent = (float(row[i]) / float(total_no[i])) * 100
    # 		accuracy.append(percent)
    # 	results.append([n] + accuracy)
    # 	accuracy = []

    # cols = ["n"] + acc_col_name
    # results = pd.DataFrame(results, columns=cols)
    # for i in range(3):
    # 	pl.plot(results['n'], results['accuracy'+str(i)])
    # pl.title("Accuracy with Increasing K with weights parameter for " + test_csv)
    # pl.title("Accuracy with Increasing K " + test_csv)
    # pl.legend(classes,loc='upper left')
    # pl.show()
