import numpy as np
from constants import WIFI_THRESHOLD, stay_duration
from energylenserver.models import functions as mod_func
from django_pandas.io import read_frame

from common_imports import *
"""
Contains common functions
"""


def get_max_class(pred_label_list):
    """
    Returns the label with the maximum count
    """

    pred_test_class = sorted(pred_label_list.unique().tolist())
    pred_list = dict((i, list(pred_label_list).count(i)) for i in pred_test_class)
    logger.debug("Predicted list: %s", pred_list)

    grpcount_label = pd.DataFrame.from_dict(pred_list, orient="index")
    grpcount_label.columns = ['lcount']
    pred_label = grpcount_label[grpcount_label.lcount == grpcount_label.lcount.max()].index[0]

    # If count is greater than 50% then return the label else return Unknown
    pred_label_count = pred_label_list.count(pred_label)
    count_percent = (pred_label_count / len(pred_label_list)) * 100
    if count_percent < 50.00:
        pred_label = "Unknown"
    logger.debug("Predicted Label: %s", pred_label)

    return pred_label


def determine_user_home_status(start_time, end_time, apt_no):
    """
    Determines if user is at home by seeing if the WiFi AP is visible
    within the event time window

    :param event_time:
    :return list of users at home:
    """
    user_list = []

    try:
        occupants = mod_func.retrieve_users(apt_no)
        occupants_df = read_frame(occupants, verbose=False)

        dev_id_list = [occupants_df.ix[idx]['dev_id'] for idx in occupants_df.index]

        # Get Home AP
        home_ap = mod_func.get_home_ap(apt_no)

        # Get Wifi data
        data = mod_func.get_sensor_data("wifi", start_time, end_time, dev_id_list)
        data_df = read_frame(data, verbose=False)

        # logger.debug ("Users:%s", data_df.dev_id.unique())
        # logger.debug ("Number of retrieved entries:%s", len(data_df))

        # Check for each user, if he/she present in the home
        for idx in occupants_df.index:
            user_id = occupants_df.ix[idx]['dev_id']
            # Filter data_df based on dev_id
            df = data_df[data_df.dev_id == user_id]

            if len(df.index) < 1:
                continue
            # Check if any mac id matches with the home ap
            match_idx_list = np.where((df.macid == home_ap) & (df.rssi > WIFI_THRESHOLD))[0]
            # logger.debug("%s:%s" % (user_id, match_idx_list))
            if len(match_idx_list) > 0:
                user_list.append(user_id)

    except Exception, e:
        logger.error("[HomeStatusException]:: %s", str(e))

    return user_list


def detect_location_change(duration_df):
    """
    Determines if there are any location changes between two time slices
    """
    pass


def get_presence_matrix(apt_no, user, start_time, end_time, act_location):
    """
    Determines duration of a user in each location he was in
    during an ongoing activity started by him

    Breaks the activity time slice into stay_duration slices and determines
    presence/absence in the room

    return  duration_df
    """

    # Get classified Wifi data
    data = mod_func.get_labeled_data("wifi", start_time, end_time, act_location, [user])
    labeled_df = read_frame(data, verbose=False)
    labeled_df.sort(['timestamp'], inplace=True)

    # Determine location change
    st_list = []
    et_list = []
    location_l = []
    try:
        # Divide into stay_duration (of 5 min) slices
        s_time = start_time
        e_time = s_time + stay_duration
        while e_time <= end_time:

            diff = end_time - e_time
            if diff < stay_duration:
                e_time = e_time + diff

            # Getting location of the slice
            sliced_df = labeled_df[
                (labeled_df.timestamp >= s_time) & (labeled_df.timestamp <= e_time)]
            location = get_max_class(sliced_df['label'])
            if location == act_location:
                location = 1
            else:
                location = 0
            st_list.append(s_time)
            et_list.append(e_time)
            location_l.append(location)

            s_time = e_time + 1
            e_time = s_time + stay_duration

        duration_df = pd.DataFrame({'start_time': st_list, 'end_time': et_list,
                                    'label': location_l},
                                   columns=['start_time', 'end_time', 'label'])
        duration_df.sort(['start_time'], inplace=True)

        return duration_df

    except Exception, e:
        logger.error("[StayDurationException]:: %s", e)

    return duration_slices


def determine_phone_with_user(event_time, user_list):
    """
    Determines if the phone is with the user_list
    """
    return True
