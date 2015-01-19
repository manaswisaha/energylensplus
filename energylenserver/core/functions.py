import time
import math
import pandas as pd
import numpy as np
from django_pandas.io import read_frame

from common_imports import *
from constants import WIFI_THRESHOLD, stay_duration
from constants import lower_mdp_percent_change, upper_mdp_percent_change
from energylenserver.models import functions as mod_func
from energylenserver.core import movement as acl


"""
Contains common functions
"""


def list_count_items(ilist):
    """
    Groups the items based on item and stores the counts for each
    """
    igroup = sorted(ilist.unique().tolist())
    ilist = ilist.tolist()
    idict = dict((i, ilist.count(i)) for i in igroup)

    return idict


def get_max_class(pred_label_list):
    """
    Returns the label with the maximum count
    """

    if len(pred_label_list) == 0:
        logger.debug("Predicted label list empty!")
        return "Unknown"

    pred_list = list_count_items(pred_label_list)
    logger.debug("Predicted list: %s", pred_list)

    grpcount_label = pd.DataFrame.from_dict(pred_list, orient="index")
    grpcount_label.columns = ['lcount']
    pred_label = grpcount_label[grpcount_label.lcount == grpcount_label.lcount.max()].index[0]

    # If count is greater than 50% then return the label else return Unknown
    total = 0
    for key, value in pred_list.iteritems():
        total += value
    pred_label_count = float(pred_list[pred_label])
    count_percent = (pred_label_count / total) * 100
    logger.debug("Percentage: %s", count_percent)
    if (count_percent == 50.0 and len(pred_list) == 2) or (count_percent < 50.0):
        pred_label = "Unknown"
    logger.debug("Predicted Label: %s\n", pred_label)

    return pred_label


def exists_in_metadata(apt_no, location, appliance, magnitude, metadata_df, l_logger, dev_id):
    """
    Checks if edge of specified magnitude exists in the metadata
    """

    if (appliance == "all" and location == "all") or (appliance == "not_all"
                                                      and location == "not_all"):
        mdf = metadata_df.copy()
    elif appliance != "all" and location != "all":
        # Extract metadata for the current location and appliance of the user
        mdf = metadata_df[(metadata_df.location == location) &
                          (metadata_df.appliance == appliance)]
        l_logger.debug("Metadata: \n%s", mdf)
    elif appliance == "all" and location != "all":
        # Extract metadata for the current location of the user
        mdf = metadata_df[(metadata_df.location == location)]
        l_logger.debug("Metadata: \n%s", mdf)
    elif appliance != "all" and location == "all":
            # Extract metadata for the current appliance of the user
        mdf = metadata_df[(metadata_df.appliance == appliance)]
        l_logger.debug("Metadata: \n%s", mdf)

    df_list = []
    status = []
    for md_i in mdf.index:
        md_power = mdf.ix[md_i]['power']
        md_appl = mdf.ix[md_i]['appliance']
        md_loc = mdf.ix[md_i]['location']

        min_md_power = math.floor(md_power - lower_mdp_percent_change * md_power)
        max_md_power = math.ceil(md_power + upper_mdp_percent_change * md_power)

        # Matching metadata with inferred
        if magnitude >= min_md_power and magnitude <= max_md_power:

            # Compare magnitude and metadata power draw
            l_logger.debug("Location: %s Appliance: %s Power: %s", md_loc, md_appl, md_power)
            l_logger.debug("For edge with magnitude %s :: [min_power=%s, max_power=%s]", magnitude,
                           min_md_power, max_md_power)

            md_power_diff = math.fabs(md_power - magnitude)
            if location != "all" or appliance != "all":
                df_list.append(
                    pd.DataFrame({'dev_id': dev_id, 'md_loc': md_loc, 'md_appl': md_appl,
                                  'md_power_diff': md_power_diff}, index=[magnitude]))
            else:
                df_list.append(mdf.ix[md_i])
            status.append(True)
        else:
            status.append(False)

    if True in status:
        return True, df_list
    else:
        return False, df_list


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

        # Setting the start time to be 5 minutes before the event time
        start_time = start_time - 4 * 60

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


def classify_movement(apt_no, start_time, end_time, user):
    logger.debug("[Classifying motion]..")

    try:
        dev_id = user.dev_id

        # Get test data
        data = mod_func.get_sensor_data("accelerometer", start_time, end_time, [dev_id])
        test_df = read_frame(data, verbose=False)

        # Classify
        pred_label = acl.classify_accl_thres(test_df)
        test_df['label'] = pred_label

        return test_df

    except Exception, e:
        logger.exception("[ClassifyMovementException]::%s", e)
        return False


def get_presence_matrix(apt_no, user, start_time, end_time, act_location):
    """
    Determines duration of a user in each location he was in
    during an ongoing activity started by him

    Breaks the activity time slice into stay_duration slices and determines
    presence/absence in the room

    return  duration_df
    """

    dev_id = user.dev_id
    # Get classified Wifi data
    # data = mod_func.get_labeled_data("wifi", start_time, end_time, act_location, [user])
    data = mod_func.get_sensor_data("wifi", start_time, end_time, [dev_id])

    labeled_df = read_frame(data, verbose=False)
    labeled_df.sort(['timestamp'], inplace=True)

    logger.debug("Location: %s User: %s Labeled len: %d", act_location, user, len(labeled_df))

    # Get classified accl data
    accl_df = classify_movement(apt_no, start_time, end_time, user)

    if len(labeled_df) == 0:
        return pd.DataFrame()

    # Determine location change
    st_list = []
    et_list = []
    location_l = []
    prev_location = "first"
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
            # logger.debug("Between [%s] and [%s] sliced len:: %d", time.ctime(s_time),
            #              time.ctime(e_time), len(sliced_df))

            if len(sliced_df) > 0:
                location = get_max_class(sliced_df['label'])

                if location == act_location:
                    location = 1
                else:
                    location = 0

            else:
                location = 0

            # Check for location change. Accept only if accl shows movement
            if not isinstance(prev_location, str):
                accl_sliced_df = accl_df[
                    (accl_df.timestamp >= s_time) & (accl_df.timestamp <= e_time)]
                accl = get_max_class(accl_sliced_df['label'])

                if prev_location != location:
                    if accl != "On User":
                        location = prev_location

            prev_location = location

            st_list.append(s_time)
            et_list.append(e_time)
            location_l.append(location)

            s_time = e_time + 1
            e_time = s_time + stay_duration

        duration_df = pd.DataFrame({'start_time': st_list, 'end_time': et_list,
                                    'label': location_l},
                                   columns=['start_time', 'end_time', 'label'])
        duration_df.sort(['start_time'], inplace=True)
        duration_df.reset_index(drop=True, inplace=True)

        return duration_df

    except Exception, e:
        logger.exception("[StayDurationException]:: %s", e)


def merge_presence_matrix(presence_df):
    """
    Merge slices where user columns have the same value
    """
    try:
        user_columns = presence_df.columns - ['start_time', 'end_time']

        merged_presence_df = presence_df.copy()

        prev_idx = presence_df.index[0]
        for idx in presence_df.index[1:]:

            row = presence_df.ix[idx]
            prev_row = presence_df.ix[prev_idx]

            flag = True
            for col in user_columns:
                if row[col] != prev_row[col]:
                    flag = False
                    break
            # Merge
            if flag:
                merged_presence_df.ix[idx, 'start_time'] = presence_df.ix[prev_idx]['start_time']
                merged_presence_df.drop(prev_idx, inplace=True)

            prev_idx = idx

        merged_presence_df.reset_index(drop=True, inplace=True)
        return merged_presence_df

    except Exception, e:
        logger.exception("[MergePMatrixException]:: %s", e)
        return False


def determine_phone_with_user(event_time, user_list):
    """
    Determines if the phone is with the user_list
    """
    return True
