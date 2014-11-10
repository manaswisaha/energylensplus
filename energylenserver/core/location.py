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

        return pred_label

    except Exception, e:
        logger.error("[WiFiClassifierException]::%s", str(e))
        return False
