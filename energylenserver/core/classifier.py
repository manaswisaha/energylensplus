"""
Script to define the classfiers from individual sensor streams

Input: Training and Test set
Output: Classfied data frame

Date: Sep 18, 2014
Author: Manaswi Saha

"""

import os
import time
import math
import pandas as pd

from django.conf import settings
from sklearn.externals import joblib
from django_pandas.io import read_frame

from common_imports import *
from energylenserver.core import audio
from energylenserver.core import location as lc
from energylenserver.models.models import *
from energylenserver.models.DataModels import WiFiTestData
from energylenserver.common_imports import *
from energylenserver.core import functions as func
from energylenserver.models import functions as mod_func
from energylenserver.preprocessing import wifi as pre_p_w
from energylenserver.preprocessing import audio as pre_p_a
from constants import lower_mdp_percent_change, upper_mdp_percent_change, no_test_data


base_dir = settings.BASE_DIR


def get_trained_model(sensor, apt_no, phone_model):
    """
    Get trained model or train model if isn't trained
    # Future TODO: Adding new localization models
    """
    if sensor == "wifi":

        # Get WiFi training data
        user_list = mod_func.get_users_for_training(apt_no, phone_model)
        data = mod_func.get_sensor_training_data("wifi", apt_no, user_list)
        train_df = read_frame(data, verbose=False)
        train_df.drop_duplicates(train_df.columns[1:], inplace=True)

        if len(train_df) == 0:
            return train_df

        dst_folder = os.path.join(base_dir, 'energylenserver/trained_models/wifi/')
        folder_listing = os.listdir(dst_folder)

        for file_i in folder_listing:
            filename_arr = file_i.split("_")
            # Use model if exists
            if filename_arr[0] == str(apt_no) and filename_arr[1] == phone_model:
                n_records = int(filename_arr[2])

                if n_records == len(train_df):
                    # Use existing
                    train_df = pd.read_csv(dst_folder + file_i)
                    return train_df

        # Model folder empty -- No model exists - Create one
        train_df = pre_p_w.format_train_data(train_df, apt_no, phone_model)
        return train_df

    if sensor in ["rawaudio", "audio"]:
        dst_folder = os.path.join(base_dir, 'energylenserver/trained_models/audio/')
        folder_listing = os.listdir(dst_folder)

        for file_i in folder_listing:
            filename_arr = file_i.split("_")
            # Use model if exists
            if filename_arr[0] == str(apt_no) and filename_arr[1] == phone_model:
                n_trained_appl = int(filename_arr[2])
                # Number of appliances in the metadata
                data = mod_func.retrieve_metadata(apt_no)
                metadata_df = read_frame(data, verbose=False)
                metadata_df['appliance'] = metadata_df.appliance.apply(lambda s: s.split('_')[0])
                # metadata_df = metadata_df[-metadata_df.appliance.isin(['Fridge'])]
                m_appl_count = len(metadata_df.appliance.unique())

                if n_trained_appl == m_appl_count:
                    # Use existing
                    model = joblib.load(dst_folder + file_i)
                    return model

        # Model folder empty -- No model exists - Create one
        model = audio.train_audio_classification_model(sensor, apt_no, phone_model)
        return model


def localize_new_data(apt_no, start_time, end_time, user):

    try:
        pmodel = user.phone_model
        dev_id = user.dev_id
        sensor = "wifi"

        # Get training data
        train_df = get_trained_model(sensor, apt_no, pmodel)
        if len(train_df) == 0:
            location = "Unknown"
            return location

        # Get test data for the past x min - for better classification
        s_time = start_time - 10 * 60       # 10 minutes

        # Get queryset of filtering later
        data_all = WiFiTestData.objects.all()

        # Get test data - filter for all queryset
        data = data_all.filter(dev_id__in=[dev_id],
                               timestamp__gte=s_time,
                               timestamp__lte=end_time)
        test_df = read_frame(data, verbose=False)
        test_df.drop_duplicates(test_df.columns[1:], inplace=True)

        # Format data for classification
        test_df = pre_p_w.format_data_for_classification(test_df)

        # Classify
        pred_label = lc.determine_location(train_df, test_df)
        test_df['label'] = pred_label

        # Save location label to the database
        sliced_df = test_df[(test_df.time >= start_time) & (test_df.time <= end_time)]

        if len(sliced_df) == 0:
            location = "Unknown"
        else:
            location = func.get_max_class(sliced_df['label'])

        data = data_all.filter(dev_id__in=[dev_id],
                               timestamp__gte=start_time,
                               timestamp__lte=end_time).update(label=location)

        logger.debug("%s :: Test data between [%s] and [%s] :: %s",
                     user.name, time.ctime(start_time), time.ctime(end_time),
                     location)

        return location

    except Exception, e:
        if str(e) == "(1205, 'Lock wait timeout exceeded; try restarting transaction')":
            logger.error("[ClassifyNewLocationDataException]:: %s", e)
        else:
            logger.exception("[ClassifyNewLocationDataException]:: %s", e)
        return location


def correct_label(label, pred_label, label_type, edge, act_location):
    """
    Classified label correction using Metadata
    Procedure: Match with the Metadata. If doesn't match then correct based on magnitude
    """
    logger.debug("[Correcting Labeling]")
    logger.debug("-" * stars)

    apt_no = edge.meter.apt_no
    magnitude = math.fabs(edge.magnitude)
    old_label = label

    # Get Metadata
    data = mod_func.retrieve_metadata(apt_no)
    metadata_df = read_frame(data, verbose=False)

    # Check if it matches with the metadata
    if label_type == "location":
        in_metadata, matched_md_l = func.exists_in_metadata(
            apt_no, label, "all", magnitude, metadata_df, logger, "dummy_user")
    else:
        in_metadata, matched_md_l = func.exists_in_metadata(
            apt_no, "all", label, magnitude, metadata_df, logger, "dummy_user")

    # Indicates the (label, edge_mag) does not exist --> incorrect label
    if not in_metadata:

        logger.debug("Label not found in Metadata. Checking all entries..")

        in_metadata, matched_md_list = func.exists_in_metadata(
            apt_no, "not_all", "not_all", magnitude, metadata_df, logger, "dummy_user")

        # Correction only if the inferred appliance is not audio
        if in_metadata:
            # Matched entries
            matched_md = pd.concat(matched_md_list)
            matched_md.reset_index(drop=True, inplace=True)

            # From metadata, if inferred appliance is audio or presence based
            metadata_df['appliance'] = metadata_df.appliance.apply(lambda s: s.split('_')[0])

            md_df = metadata_df.ix[:, ['appliance', 'presence_based',
                                       'audio_based']].drop_duplicates()
            md_df.reset_index(inplace=True, drop=True)

            md_audio = md_df.ix[0]['audio_based']
            md_presence = md_df.ix[0]['presence_based']

            # Non-audio based
            if not md_audio:
                # Presence based appliance
                if md_presence and act_location != "dummy":
                    matched_md = matched_md[matched_md.md_loc == act_location]
                    appl_list = matched_md.md_appl.unique()

                    if len(appl_list) == 1:
                        label = appl_list[0]
                        logger.debug("Corrected Label: %s --> %s", old_label, label)
                        return label

                # Correction process -- Select the one closest to the metadata
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

                    label = func.get_max_class(pd.Series(new_label_list))

        else:
            # No matching metadata found
            # Cause: different power consumption of an appliance
            # Solution: Select the one with the highest value

            logger.debug("No metadata found")
            new_label_list = [l for l in pred_label if l != old_label]
            label = func.get_max_class(pd.Series(new_label_list))

    logger.debug("Corrected Label: %s --> %s", old_label, label)

    return label


def classify_location(apt_no, start_time, end_time, user, edge, n_users_at_home):
    logger.debug("[Classifying location] - %s [%d]", user, edge.magnitude)
    logger.debug("-" * stars)

    try:
        pmodel = user.phone_model
        dev_id = user.dev_id
        sensor = "wifi"

        # Get WiFi test data
        data = mod_func.get_sensor_data("wifi", start_time, end_time, [dev_id])
        test_df = read_frame(data, verbose=False)
        test_df.drop_duplicates(test_df.columns[1:], inplace=True)

        # '''
        location_list = test_df.label.unique()
        logger.debug("Pre-labeled locations: %s", location_list)
        if len(location_list) == 0:
            logger.debug("Insufficient test data")
            return no_test_data

        if "none" not in location_list and "Unknown" not in location_list:
            location = func.get_max_class(test_df['label'])
            '''
            Commented: Can't correct bcoz we need the user's location
            and not appliance location as in EnergyLens
            if n_users_at_home == 1:
                location = correct_label(location, test_df['label'], 'location', edge)
                data.update(label=location)
            '''
            return location
        # '''

        '''
        # Get queryset of filtering later
        data_all = WiFiTestData.objects.all()

        # Get test data - filter for all queryset
        data = data_all.filter(dev_id__in=[dev_id],
                               timestamp__gte=s_time,
                               timestamp__lte=end_time)
        '''

        # Format data for classification
        train_df = get_trained_model(sensor, apt_no, pmodel)
        test_df = pre_p_w.format_data_for_classification(test_df)

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

        '''
        Commented: Can't correct bcoz we need user's location for usage/detection
        and not appliance location as in EnergyLens
        if n_users_at_home == 1:
            location = correct_label(location, sliced_df['pred_label'], 'location', edge)
        '''
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
        if str(e) == "(1205, 'Lock wait timeout exceeded; try restarting transaction')":
            logger.error("[ClassifyLocationException]:: %s", e)
        else:
            logger.exception("[ClassifyLocationException]:: %s", e)
        return location


def classify_appliance(apt_no, start_time, end_time, user, edge, n_users_at_home):
    """
    Classifies appliance based on audio or metadata
    """
    logger.debug("[Classifying appliance] - %s [%d]", user, edge.magnitude)
    logger.debug("-" * stars)
    try:
        appliance = "Unknown"

        # Get Metadata
        data = mod_func.retrieve_metadata(apt_no)
        metadata_df = read_frame(data, verbose=False)

        # Check for existence
        in_metadata, matched_md = func.exists_in_metadata(
            apt_no, "not_all", "not_all", math.fabs(edge.magnitude), metadata_df,
            logger, user.dev_id)
        if in_metadata:
            # --Classify using metadata--
            md_df = pd.concat(matched_md)
            md_df.reset_index(drop=True, inplace=True)

            md_audio = md_df.md_audio.unique()
            md_presence = md_df.md_presence.unique()

            # Determine if appliance is audio based
            if len(md_audio) == 1:

                fil_md_df = md_df[md_df.md_power_diff == md_df.md_power_diff.min()]

                logger.debug("Filtered Metadata: \n %s", fil_md_df)

                if not md_audio[0] or (not md_presence[0] and edge.type == 'falling'):

                    # Not audio based or non-presence based appliance
                    appl_list = fil_md_df.md_appl.unique()

                    if len(appl_list) == 1:
                        appliance = appl_list[0]
                        logger.debug("Selected Appliance:: %s", appliance)
                # --Classify using audio--
                else:
                    appliance = classify_appliance_using_audio(apt_no, start_time, end_time,
                                                               user, edge, n_users_at_home)

            # --Classify using audio--
            else:
                appliance = classify_appliance_using_audio(apt_no, start_time, end_time,
                                                           user, edge, n_users_at_home)

        return appliance
    except Exception, e:
        if str(e) == "(1205, 'Lock wait timeout exceeded; try restarting transaction')":
            logger.error("[ClassifyApplianceException]::%s", e)
        else:
            logger.exception("[ClassifyApplianceException]::%s", e)
        return appliance


def classify_appliance_using_audio(apt_no, start_time, end_time, user, edge, n_users_at_home):

    try:
        pmodel = user.phone_model
        dev_id = user.dev_id
        sensor = "rawaudio"

        # Get trained model
        train_model = get_trained_model(sensor, apt_no, pmodel)

        # Get test data
        data = mod_func.get_sensor_data(sensor, start_time, end_time, [dev_id])
        test_df = read_frame(data, verbose=False)
        test_df.drop_duplicates(test_df.columns[1:], inplace=True)

        if len(test_df) == 0:
            logger.debug("No audio test data")
            return no_test_data

        # Format data for classification
        test_df = pre_p_a.format_data_for_classification(test_df)

        # Extract features
        test_df = audio.extract_features(test_df, "test", apt_no)

        # Classify
        pred_label = audio.determine_appliance(sensor, train_model, test_df)
        test_df['pred_label'] = pred_label

        appliance = func.get_max_class(test_df['pred_label'])

        if n_users_at_home == 1:
            appliance = correct_label(appliance, test_df['pred_label'], 'appliance', edge, "dummmy")

        if appliance == "Unknown":

            # Select appliance with maximum count
            appl_count_df = test_df.ix[:, ['pred_label']]
            appl_count_df['count'] = [0] * len(appl_count_df)
            appl_count_df = appl_count_df.groupby(['pred_label']).count()
            appl_count_df.sort(['count'], ascending=False, inplace=True)
            appliance = appl_count_df.index[0]
            logger.debug("Selected max count appliance:: %s", appliance)

        '''
        sliced_df = test_df[
            (test_df.timestamp >= (start_time + 60)) & (test_df.timestamp) <= end_time]

        if len(sliced_df) == 0:
            appliance = "Unknown"
        else:
            appliance = func.get_max_class(sliced_df['pred_label'])
        '''

        # Save appliance label to the database
        data.update(label=appliance)
        return appliance

    except Exception, e:
        logger.exception("[ClassifyApplianceAudioException]::%s", e)
        return appliance


def classify_activity(metadata_df, magnitude):
    """
    Uses metadata matching to determine appliance and location for only
    non-presence based appliance
    """
    logger.debug("[Classifying activity] - [%d]", magnitude)
    logger.debug("-" * stars)

    # Check for existence
    md_list = []
    metadata_df['appliance'] = metadata_df.appliance.apply(lambda s: s.split('_')[0])

    metadata_df = metadata_df[metadata_df.presence_based == 0]
    for md_i in metadata_df.index:
        md_power = metadata_df.ix[md_i]['power']
        md_appl = metadata_df.ix[md_i]['appliance']
        md_loc = metadata_df.ix[md_i]['location']

        min_md_power = math.floor(md_power - lower_mdp_percent_change * md_power)
        max_md_power = math.ceil(md_power + upper_mdp_percent_change * md_power)

        # Matching metadata with inferred
        if magnitude >= min_md_power and magnitude <= max_md_power:
            md_power_diff = math.fabs(md_power - magnitude)
            md_list.append(pd.DataFrame({'md_loc': md_loc, 'md_appl': md_appl,
                                         'md_power_diff': md_power_diff},
                                        index=[magnitude]))

    # Determine location and appliance in use
    fil_md_df = pd.concat(md_list)
    fil_md_df.reset_index(drop=True, inplace=True)

    if len(fil_md_df) == 0:
        location = "Unknown"
        appliance = "Unknown"
        return location, appliance

    fil_md_df = fil_md_df[fil_md_df.md_power_diff == fil_md_df.md_power_diff.min()]
    fil_md_df.reset_index(drop=True, inplace=True)

    if len(fil_md_df) > 1:
        # If all the appliances and corresponding location are same,
        # then assign with it else error
        u_appl_count = len(fil_md_df.md_appl.unique().tolist())
        u_loc_count = len(fil_md_df.md_loc.unique().tolist())

        # Appliance assignment
        if u_appl_count == 1:
            appliance = fil_md_df.ix[0]['md_appl']
        else:
            appliance = "Unknown"

        # Location assignment
        if u_loc_count == 1:
            location = fil_md_df.ix[0]['md_loc']
        else:
            location = "Unknown"

    else:
        location = fil_md_df.ix[0]['md_loc']
        appliance = fil_md_df.ix[0]['md_appl']

    return location, appliance
