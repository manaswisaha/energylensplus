"""
Localize a user using k-NN algorithm
Author: Manaswi Saha
Updated on: Sep 18, 2014
"""

import pandas as pd

from sklearn.neighbors import KNeighborsClassifier

from common_imports import *


import warnings
warnings.filterwarnings('ignore')


def train_localization_model(train_df):
    """
    Train WiFi localization model
    TODO: For future use, for new models
    """
    # Run KNN or NNSS algorithm to generate locations for the data points
    n = 5
    clf = KNeighborsClassifier(n_neighbors=n)

    return clf


def determine_location(train_df, test_df):
    """
    Determines the location of the user at the specified time
    """

    try:
        # Get RSSI columns
        train_col_names = train_df.columns[1:len(train_df.columns) - 1]
        test_col_names = test_df.columns[1:len(test_df.columns) - 1]

        # Find the common rssi columns
        features = list(set(test_col_names) & set(train_col_names))
        logger.debug("WiFi Features:: %s", features)

        # Localizing the user
        # Run KNN or NNSS algorithm to generate locations for the data points
        n = 5
        clf = KNeighborsClassifier(n_neighbors=n)
        clf.fit(train_df[features], train_df['label'])
        pred_label = clf.predict(test_df[features])

        # Return results
        pred_list = dict((i, list(pred_loc).count(i)) for i in pred_test_class)
        logger.debug("Predicted list: %s", pred_list)
        grpcount_label = pd.DataFrame.from_dict(pred_list, orient="index")
        grpcount_label.columns = ['lcount']
        pred_label = grpcount_label[
            grpcount_label.lcount == grpcount_label.lcount.max()].index[0]
        logger.debug("Predicted Location Label: %s", pred_label)
        return pred_label

    except Exception, e:
        logger.error("[WiFiClassifierException]::%s", str(e))
        return False

'''
def classify_location(train_csv, test_csv, apt_no, idx):

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
    print "-" * 30, "Using multiple access point", "-" * 30
    features = list(set(test_col_names) & set(train_col_names))

    # Testing with the residence access point
    # print "-"*30, "Using single access point", "-"*30
    # features = ['c4:0a:cb:2d:87:a0']
    # print "Training set columns::", train_col_names, "\nTest set::", test_col_names
    print "Features::", features

    # Step3: Localizing the user
    total_rows = (test_df.shape)[0]
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


def class_results(train_df, test_df, pred_df):
    """
    Calculates the localization accuracy
    """

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

    # cm = confusion_matrix(true_loc.tolist(), pred_loc.tolist())
    # print "-" * 20
    # print "Confusion Matrix:: "
    # print cm

    # Print Classification report
    # cls_report = (classification_report(true_loc.tolist(),
    #                                     pred_loc.tolist(),
    #                                     labels=classes, target_names=classes))
    # print cls_report

    # Overall Accuracy
    true = pred_df.label
    pred = pred_df.pred_label
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
'''
