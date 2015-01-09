"""
Script to define the classfiers from individual sensor streams

Input: Training and Test set
Output: Classfied data frame

Date: Sep 18, 2014
Author: Manaswi Saha

"""

import os
import time

from django_pandas.io import read_frame
from django.conf import settings
from sklearn.externals import joblib

from common_imports import *
from energylenserver.core import audio
from energylenserver.core import location as lc
from energylenserver.core import movement as acl
from energylenserver.models.models import *
from energylenserver.models.DataModels import WiFiTestData
from energylenserver.common_imports import *
from energylenserver.core import functions as func
from energylenserver.models import functions as mod_func
from energylenserver.preprocessing import wifi as pre_p
from constants import lower_mdp_percent_change, upper_mdp_percent_change


stars = 40
base_dir = settings.BASE_DIR


def classify_activity(metadata_df, magnitude):
    """
    Uses metadata matching to determine appliance and location
    """

    # Detecting location and appliance in use
    for md_i in metadata_df.index:
        md_power = mdf.ix[md_i]['power']
        md_appl = mdf.ix[md_i]['appliance']
        md_loc = mdf.ix[md_i]['location']

        min_md_power = math.floor(md_power - lower_mdp_percent_change * md_power)
        max_md_power = math.ceil(md_power + upper_mdp_percent_change * md_power)

        # Matching metadata with inferred
        if magnitude >= min_md_power and magnitude <= max_md_power:
            md_power_diff = math.fabs(md_power - magnitude)
            if location != "all" or appliance != "all":
                df_list.append(
                    pd.DataFrame({'dev_id': dev_id, 'md_loc': md_loc, 'md_appl': md_appl,
                                  'md_power_diff': md_power_diff}, index=[magnitude]))
            else:
                df_list.append(mdf.ix[md_i])

    # Determine location and appliance
    for idx in df_list:
        md_idx = md_dict[ts_idx]['md_idx']
        md_diff = md_dict[ts_idx]['md_power_diff']
        if len(md_idx) > 0:
            print "\nMD", ts_idx, md_idx, md_diff

            min_item = min(md_diff)
            indices = [i for i, x in enumerate(md_diff) if x == min_item]
            print "Minimum Item:", min_item
            print "Minimum Indices", indices
            print "Length indices", len(indices)

            if len(indices) > 1:
                # If all the appliances and corresponding location are same,
                # then assign with it else error
                md_idxes = [md_idx[i] for i in indices]
                appl = [md_df.ix[mdid]['appliance'] for mdid in md_idxes]
                loc = [md_df.ix[mdid]['location'] for mdid in md_idxes]
                if len(set(appl)) == 1 and len(set(loc)) != 1:
                    location.append("Not Found")
                    appliance.append(md_df.ix[mdid]['appliance'])
                elif len(set(appl)) != 1 and len(set(loc)) == 1:
                    location.append(md_df.ix[mdid]['location'])
                    appliance.append("Not Found")
                elif len(set(appl)) == 1 and len(set(loc)) == 1:
                    location.append(md_df.ix[mdid]['location'])
                    appliance.append(md_df.ix[mdid]['appliance'])
                else:
                    location.append("Not Found")
                    appliance.append("Not Found")
            else:
                mdid = md_idx[indices[0]]
                location.append(md_df.ix[mdid]['location'])
                appliance.append(md_df.ix[mdid]['appliance'])
        else:
            print "\nNFMD", ts_idx, md_idx, md_diff
            location.append("Not Found")
            appliance.append("Not Found")


def correct_label(label, pred_label, label_type, edge):
    """
    Classified label correction using Metadata
    Procedure: Match with the Metadata. If doesn't match then correct based on magnitude
    """
    apt_no = edge.meter.apt_no
    magnitude = edge.magnitude
    old_label = label

    # Get Metadata
    data = mod_func.retrieve_metadata(apt_no)
    metadata_df = read_frame(data, verbose=False)

    if label_type == "location":
        in_metadata, matched_md = exists_in_metadata(
            apt_no, label, "all", magnitude, metadata_df, logger, "dummy_user")
    else:
        in_metadata, matched_md = exists_in_metadata(
            apt_no, "all", label, magnitude, metadata_df, logger, "dummy_user")

    if not in_metadata:
        # Select the one closest to the metadata

        in_metadata, matched_md = exists_in_metadata(
            apt_no, "not_all", "not_all", magnitude, metadata_df, logger, "dummy_user")

        if in_metadata:
            matched_md = matched_md[
                matched_md.md_power_diff == matched_md.md_power_diff.min()]
            logger.debug(
                "Entry with least distance from the metadata:\n %s", matched_md)
            if label_type == "location":
                unique_label = matched_md.md_loc.unique().tolist()
            else:
                unique_label = matched_md.md_appl.unique().tolist()

            if len(unique_label) == 1:
                label = unique_label[0]
            else:
                # Multiple matched entries - select the one with the
                # maximum count in the pred_label
                idict = func.list_count_items(pred_label)

                # Remove the entries not in unique label list
                filtered_l = [key for key in idict.keys() if key in unique_label]

                # Get the max count
                new_label_list = []
                for key in filtered_l:
                    for l in pred_label:
                        if key == l:
                            new_label_list.append(key)

                label = func.get_max_class(new_label_list)

        else:
            # No matching metadata found
            # Cause: different power consumption of an appliance
            # Solution: Select the one with the highest value
            new_label_list = [l for l in pred_label if l != old_label]
            label = func.get_max_class(new_label_list)

    logger.debug("Corrected Label: %s --> %s", old_label, label)

    return label


def get_trained_model(sensor, apt_no, phone_model):
    """
    Get trained model or train model if isn't trained
    """
    if sensor == "wifi":
        # Future TODO: Adding new localization models
        return
    if sensor == "audio":
        dst_folder = os.path.join(base_dir, 'energylenserver/trained_models/audio/')
        folder_listing = os.listdir(dst_folder)

        for file_i in folder_listing:
            filename_arr = file_i.split("_")
            # Use model if exists
            if filename_arr[0] == str(apt_no) and filename_arr[1] == phone_model:
                model = joblib.load(dst_folder + file_i)
            # Else create a new training model
            else:
                # Get training data
                user_list = mod_func.get_users_for_training(apt_no, phone_model)
                data = mod_func.get_sensor_training_data("audio", apt_no, user_list)
                train_df = read_frame(data, verbose=False)

                filename = str(apt_no) + "_" + phone_model
                model = audio.train_audio_classfication_model(train_df, filename)
            return model

        # No model exists - Create one

        # Get training data
        user_list = mod_func.get_users_for_training(apt_no, phone_model)
        data = mod_func.get_sensor_training_data("audio", apt_no, user_list)
        train_df = read_frame(data, verbose=False)

        # Train model
        filename = str(apt_no) + "_" + phone_model
        model = audio.train_audio_classfication_model(train_df, filename)
        return model


def get_wifi_training_data(apt_no, user_list):
    data = mod_func.get_sensor_training_data("wifi", apt_no, user_list)
    train_df = read_frame(data, verbose=False)

    return train_df


def localize_new_data(apt_no, start_time, end_time, user):

    try:
        pmodel = user.phone_model
        dev_id = user.dev_id

        # Get WiFi training data
        user_list = mod_func.get_users_for_training(apt_no, pmodel)
        train_df = get_wifi_training_data(apt_no, user_list)
        logger.debug("Training classes: %s", train_df.label.unique())

        if len(train_df) == 0:
            location = "Unknown"
            return location

        '''
        # Get WiFi test data
        data = mod_func.get_sensor_data("wifi", start_time, end_time, [dev_id])
        test_df = read_frame(data, verbose=False)

        # Format data for classification
        train_df = pre_p.format_data_for_classification(train_df)
        test_df = pre_p.format_data_for_classification(test_df)

        # Classify
        pred_label = lc.determine_location(train_df, test_df)

        if isinstance(pred_label, bool):
            location = "Unknown"
            data.update(label=location)
            return location

        test_df['pred_label'] = pred_label
        logger.debug("Predicted labels: %s", test_df.pred_label.unique())

        # Save location label to the database
        # sliced_df = test_df[
        #     (test_df.timestamp >= (start_time + 45)) & (test_df.timestamp) <= end_time]

        if len(test_df) == 0:
            location = "Unknown"
        else:
            location = func.get_max_class(test_df['pred_label'])
        data.update(label=location)
        return location

        '''
        # Get test data for the past hour - for better classification
        s_time = start_time - 10 * 60       # 10 minutes

        # Get queryset of filtering later
        data_all = WiFiTestData.objects.all()

        # Get test data - filter for all queryset
        data = data_all.filter(dev_id__in=[dev_id],
                               timestamp__gte=s_time,
                               timestamp__lte=end_time)
        test_df = read_frame(data, verbose=False)

        # Format data for classification
        train_df = pre_p.format_data_for_classification(train_df)
        test_df = pre_p.format_data_for_classification(test_df)

        # Classify
        pred_label = lc.determine_location(train_df, test_df)
        test_df['label'] = pred_label

        logger.debug("%s :: Test data between [%s] and [%s] :: %s",
                     user.name, time.ctime(s_time), time.ctime(end_time),
                     func.get_max_class(test_df['label']))

        '''
        # ---- Update unlabeled records in the 1 hour slice-----
        # unlabeled_df = test_df[test_df.label == 'none']
        unlabeled_df = test_df.copy()
        # unlabeled_df = test_df.ix[sliced_df.index]

        # 44 --> Explanation:
        # start_time = event_time - 60;
        # 15 seconds to compensate for time difference between phone and meter
        # desired event time slice to label::
        # start time = start_time + 45 = (event_time - 60) + 45 = event_time - 15
        # Therefore, end time for the unlabeled set in the past hour would be
        # one second before the start time of the desired time slice
        # e_time = (start_time + 45) - 1

        # e_time = start_time + 44
        e_time = end_time
        window = 2 * 60     # 2 minutes

        st = s_time
        et = st + window
        while et <= e_time:

            diff = end_time - et
            if diff < window:
                et = et + diff

            # Get class with max class for the time slice
            sliced_df = unlabeled_df[(unlabeled_df.time >= st
                                      ) & (unlabeled_df.time) <= et]
            if len(sliced_df) == 0:
                location = "Unknown"
            else:
                logger.debug("Slice: [%s] and [%s]", time.ctime(s_time), time.ctime(end_time))
                location = func.get_max_class(sliced_df['label'])

            # Filter all queryset (to get desired time slice of the unlabeled set) and
            # Update it
            data = data_all.filter(dev_id__in=[dev_id],
                                   timestamp__gte=s_time,
                                   timestamp__lte=end_time).update(label=location)

            # Update time counter for the next loop
            st = et + 1
            et = st + window
        '''

        # Save location label to the database
        sliced_df = test_df[(test_df.time >= start_time) & (test_df.time <= end_time)]

        if len(sliced_df) == 0:
            location = "Unknown"
        else:
            location = func.get_max_class(sliced_df['label'])

        data = data_all.filter(dev_id__in=[dev_id],
                               timestamp__gte=start_time,
                               timestamp__lte=end_time).update(label=location)

        return location
        # '''

    except Exception, e:
        logger.exception("[ClassifyNewLocationDataException]:: %s", e)
        return False


def classify_location(apt_no, start_time, end_time, user, edge, n_users_at_home):
    logger.debug("[Classifying location]..")

    try:
        pmodel = user.phone_model
        dev_id = user.dev_id

        # Get WiFi test data
        data = mod_func.get_sensor_data("wifi", start_time, end_time, [dev_id])
        test_df = read_frame(data, verbose=False)

        # '''
        location_list = test_df.label.unique()
        logger.debug("Pre-labeled locations: %s", location_list)
        if len(location_list) == 0:
            logger.debug("Insufficient test data")
            return False

        if "none" not in location_list and "Unknown" not in location_list:
            location = func.get_max_class(test_df['label'])
            if n_users_at_home == 1:
                location = correct_label(location, test_df['label'], edge)
                data.update(label=location)
            return location
        # '''

        # Get WiFi training data
        user_list = mod_func.get_users_for_training(apt_no, pmodel)
        train_df = get_wifi_training_data(apt_no, user_list)

        '''
        # Get queryset of filtering later
        data_all = WiFiTestData.objects.all()

        # Get test data - filter for all queryset
        data = data_all.filter(dev_id__in=[dev_id],
                               timestamp__gte=s_time,
                               timestamp__lte=end_time)
        '''

        # Format data for classification
        train_df = pre_p.format_data_for_classification(train_df)
        test_df = pre_p.format_data_for_classification(test_df)

        # Classify
        pred_label = lc.determine_location(train_df, test_df)
        test_df['pred_label'] = pred_label

        # Save location label to the database
        sliced_df = test_df[
            (test_df.time >= (start_time + 60)) & (test_df.time) <= end_time]

        if len(sliced_df) == 0:
            location = "Unknown"
        else:
            location = func.get_max_class(sliced_df['pred_label'])

        if n_users_at_home == 1:
            location = correct_label(location, sliced_df['pred_label'], edge)
        data.update(label=location)

        # data = data_all.filter(dev_id__in=[dev_id],
        # timestamp__gte=s_time,
        # timestamp__lte=end_time).update(label=location)

        # Update
        # sliced_df = test_df[(test_df.time >= (start_time + 45)
        #                      ) & (test_df.time) <= end_time]
        # location = func.get_max_class(pred_label)
        return location

    except Exception, e:
        logger.exception("[ClassifyLocationException]:: %s", e)
        return False

    return location


def classify_appliance(apt_no, start_time, end_time, user, edge):
    logger.debug("[Classifying appliance]..")
    logger.debug("-" * stars)

    try:
        pmodel = user.phone_model
        dev_id = user.dev_id

        # Get trained model
        train_model = get_trained_model("audio", apt_no, pmodel)

        # Get test data
        data = mod_func.get_sensor_data("audio", start_time, end_time, [dev_id])
        test_df = read_frame(data, verbose=False)

        # Classify
        pred_label = audio.determine_appliance(train_model, test_df)
        test_df['pred_label'] = pred_label

        # Save appliance label to the database
        sliced_df = test_df[
            (test_df.timestamp >= (start_time + 45)) & (test_df.timestamp) <= end_time]

        if len(sliced_df) == 0:
            appliance = "Unknown"
        else:
            appliance = func.get_max_class(sliced_df['pred_label'])

        if n_users_at_home == 1:
            appliance = correct_label(appliance, sliced_df['pred_label'], edge)
        data.update(label=appliance)
        return appliance

    except Exception, e:
        logger.exception("[ClassifyApplianceException]::%s", e)
        return False

    return appliance
