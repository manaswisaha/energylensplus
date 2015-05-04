import os
import math
import pandas as pd
import random
from django_pandas.io import read_frame

from common_imports import *
from energylenserver.models import functions as mod_func
from classifier import classify_activity, correct_label
from functions import exists_in_metadata
from energylenserver.common_offline import *

"""
User Attribution Module
"""


def identify_user(apt_no, magnitude, location, appliance, user_list, edge):
    """
    Identifies the occupant who performed the inferred activity
    """
    logger.debug("[Identifying users]")
    logger.debug("-" * stars)

    user = {}
    m_magnitude = math.fabs(magnitude)
    edge_time = edge.timestamp

    # Get Metadata
    data = mod_func.retrieve_metadata(apt_no)
    metadata_df = read_frame(data, verbose=False)

    md_df = metadata_df.copy()

    # Get the list of appliances with their types
    md_df['appliance'] = md_df.appliance.apply(lambda s: s.split('_')[0])
    tmp_md_df = md_df.ix[:, ['appliance']].drop_duplicates()
    md_df = md_df.ix[tmp_md_df.index]
    md_df.set_index(['appliance'], inplace=True)
    md_df.ix['TV', 'audio_based'] = False
    # logger.debug("Appliances with their types: \n%s", md_df)

    audio_based = md_df[md_df.audio_based == 1].index.tolist()
    presence_based = md_df[md_df.presence_based == 1].index.tolist()
    logger.debug("Audio based appliances:: %s", audio_based)
    logger.debug("Presence based appliances:: %s", presence_based)

    users = location.keys()

    df_list = []
    for dev_id in users:
        loc_user = location[dev_id]
        logger.debug("Location: %s", loc_user)

        # Ignore if location is unknown
        if loc_user == "Unknown":
            continue

        # Check if edge exists in the metadata for the current location
        in_metadata, tmp_list = exists_in_metadata(
            apt_no, loc_user, "all", m_magnitude, metadata_df, logger, dev_id)

        df_list = df_list + tmp_list

    if len(df_list) == 0:
        logger.debug("Edge did not match with the metadata for any user.")
        logger.debug("Location classification is incorrect or Unknown")

        # Check for non-presence based appliance using the inferred appliance
        '''
        presence_status = False
        for appl in appliance.values():
            if appl in presence_based:
                presence_status = True
                break

        if not presence_status:
        '''
        # May indicate a non-presence based appliance e.g. Microwave
        # -- Use metadata i.e. meter only approach
        where, what = classify_activity(metadata_df, m_magnitude)

        user['location'] = where
        user['appliance'] = what

        if len(user_list) == 1:
            user['dev_id'] = [user_list[0]]
        else:
            user['dev_id'] = "Unknown"
        logger.debug("Matched user(s) for edge with mag %d: %s", magnitude, user)

        details = "classify both"
        # Offline processing - evaluation - START
        '''
        Check with ground truth and
        attribute reason = activity correction
        '''
        match, reason = match_ground_truth(
            apt_no, edge_time, where, what)
        if not match:
            write_reason(apt_no, "common", edge.timestamp, reason, details)
        else:
            write_reason(apt_no, "common", edge.timestamp, "correct", "")

        # Offline processing - evaluation - END

        return user

        user['dev_id'] = "Unknown"
        user['location'] = "Unknown"
        user['appliance'] = "Unknown"
        logger.debug("Matched user(s) for edge with mag %d: %s", magnitude, user)
        return user

    # Select the entry with the matching appliance for a user
    # For conflicting appliances between users, choose the one with least distance
    # from the metadata (comparing between two users)

    # DF with contending users for the edge
    poss_user = pd.concat(df_list)
    poss_user = poss_user.reset_index(drop=True)
    logger.debug("Possible User - Time Slice Contenders\n %s", poss_user)

    if len(poss_user) > 0:
        contending_users = poss_user.dev_id.unique().tolist()

        if len(contending_users) == 1:

            sel_user = contending_users[0]

            appl_list = poss_user.md_appl.unique()

            if len(appl_list) == 1:
                appl = appl_list[0]

                details = "appliance attribution"
                '''
                md_audio = poss_user.md_audio.unique()[0]
                appl_audio = md_df.ix[appliance[sel_user]]['audio_based']
                if md_audio == appl_audio:
                    appl = appl_list[0]
                elif appliance[sel_user] == "TV":
                    appl = appl_list[0]
                else:
                    appl = "Unknown"
                '''
            else:
                '''
                # Determine the ongoing events of inferred appliance in the inferred location
                on_event_records = mod_func.get_on_events_by_location(
                    apt_no, edge_time, location[sel_user])
                on_event_records_df = read_frame(on_event_records, verbose=False)
                on_event_records_df['event_time'] = on_event_records_df.event_time.astype('int')

                idx_list = []
                now_time = int(time.time())
                for idx in poss_user.index:
                    md_appliance = poss_user.ix[idx]['md_appl']
                    m_df = metadata_df[metadata_df.appliance == md_appliance]

                    # Check for ongoing events
                    on_event_records_df = on_event_records_df[
                        (on_event_records_df.appliance == md_appliance) &
                        (now_time - on_event_records_df.event_time
                         < 12 * 3600)]
                    n_on_event_records = len(on_event_records_df)
                    logger.debug("Number of ongoing events: %s", n_on_event_records)

                    if n_on_event_records > 0 and edge.type == "rising":

                        no_of_appl = m_df.ix[0]['how_many']
                        logger.debug("Count for %s in %s: %d", md_appliance,
                                     location[sel_user], no_of_appl)

                        if n_on_event_records == no_of_appl:
                            idx_list.append(idx)

                sel_idx_list = poss_user.index.tolist() - idx_list
                poss_user = poss_user.ix[sel_idx_list]
                poss_user.reset_index(inplace=True, drop=True)

                if len(poss_user) == 1:
                    logger.debug("Selecting entry that hasn't started")
                    appl = poss_user.ix[0]['md_appl']
                '''

                # If the inferred appliance is audio based then select the entry
                # that is audio based and vice versa
                appl_audio_list = poss_user.md_audio.unique()
                if len(appl_audio_list) > 1 and len(poss_user) > 2:
                    poss_user = poss_user[
                        poss_user.md_power_diff == poss_user.md_power_diff.min()]
                    poss_user = poss_user.reset_index(drop=True)

                    if len(poss_user) == 1:
                        appl = poss_user.ix[0]['md_appl']

                        user['dev_id'] = [sel_user]
                        user['location'] = location[sel_user]
                        user['appliance'] = appl

                        logger.debug("Matched user(s) for edge with mag %d: %s", magnitude, user)

                        details = "similar appliance_distance diff"
                        # Offline processing - evaluation - START
                        '''
                        Check with ground truth and
                        attribute reason = activity correction
                        '''
                        match, reason = match_ground_truth(
                            apt_no, edge_time, user['location'], user['appliance'])
                        if not match:
                            write_reason(apt_no, "common", edge.timestamp, reason, details)
                        else:
                            write_reason(apt_no, "common", edge.timestamp, "correct", "")

                        # Offline processing - evaluation - END

                        return user
                    else:
                        appl_audio_list = poss_user.md_audio.unique()
                        appl_list = poss_user.md_appl.unique()

                if len(appl_list) == 1:
                    appl = appl_list[0]
                    '''
                    md_audio = appl_audio_list[0]
                    appl_audio = md_df.ix[appliance[sel_user]]['audio_based']
                    if md_audio == appl_audio:
                        appl = appl_list[0]
                    elif appliance[sel_user] == "TV":
                        appl = appl_list[0]
                    else:
                        appl = "Unknown"
                    '''

                    details = "similar appliance"

                elif len(appl_list) > 1 and len(appl_audio_list) == 1:

                    # elif len(poss_user) > 1:
                    poss_user = poss_user[
                        poss_user.md_power_diff == poss_user.md_power_diff.min()]
                    logger.debug("Selecting random entry from different appliances")
                    sel_idx = random.choice(poss_user.index)
                    appl = poss_user.ix[sel_idx]['md_appl']

                    details = "similar appliance_distance diff"

                elif len(appl_audio_list) == 1:
                    # If both are audio based or otherwise then use correct label
                    logger.debug("Selecting random entry from multiple appliances")
                    sel_idx = random.choice(poss_user.index)
                    appl = poss_user.ix[sel_idx]['md_appl']
                    # appl = correct_label(appliance[sel_user], pd.Series([appliance[sel_user]]),
                    #                      'appliance', edge, location[sel_user])
                    details = "similar appliance_distance diff"
                else:

                    appl_audio = md_df.ix[appliance[sel_user]]['audio_based']
                    for idx in poss_user.index:
                        md_aud = poss_user.ix[idx]['md_audio']
                        md_appliance = poss_user.ix[idx]['md_appl']
                        if md_appliance == "TV":
                            md_aud = False

                        if md_aud == appl_audio:
                            appl = md_appliance
                            break
                        else:
                            appl = "Unknown"
                    if appl == "Unknown":
                        poss_user = poss_user[poss_user.md_audio == appl_audio]
                        if len(poss_user) > 0:
                            idx = poss_user.index[0]
                            appl = poss_user.ix[idx]['md_appl']

                    details = "similar appliance_audio based"

            user['dev_id'] = [sel_user]
            user['location'] = location[sel_user]
            user['appliance'] = appl

            # Offline processing - evaluation - START
            '''
            Check with ground truth and
            attribute reason = activity correction
            '''
            match, reason = match_ground_truth(
                apt_no, edge_time, user['location'], user['appliance'])
            if not match:
                write_reason(apt_no, "common", edge.timestamp, reason, details)
            else:
                write_reason(apt_no, "common", edge.timestamp, "correct", "")

            # Offline processing - evaluation - END

        else:
            # Resolving conflict by
            # selected entry with least distance to the metadata
            poss_user = poss_user[
                poss_user.md_power_diff == poss_user.md_power_diff.min()]
            poss_user.reset_index(drop=True, inplace=True)
            logger.debug(
                "Entry for multiple contending users with md_power_diff:\n %s", poss_user)
            contending_users = poss_user.dev_id.unique().tolist()

            if len(contending_users) == 1:
                # Indicates that there is single contender
                sel_user = contending_users[0]

                appl_list = poss_user.md_appl.unique()
                appl_audio_list = poss_user.md_audio.unique()

                if len(appl_list) == 1:
                    # Contending appliances are same
                    appl = appl_list[0]
                    '''
                    md_audio = appl_audio_list[0]
                    appl_audio = md_df.ix[appliance[sel_user]]['audio_based']
                    if md_audio == appl_audio:
                        appl = appl_list[0]
                    elif appliance[sel_user] == "TV":
                        appl = appl_list[0]
                    else:
                        appl = "Unknown"
                    '''
                    details = "similar appliance_multiple users_distance diff"

                elif len(appl_list) > 1 and len(appl_audio_list) == 1:
                    # Multiple contending appliances but both are audio based
                    poss_user = poss_user[
                        poss_user.md_power_diff == poss_user.md_power_diff.min()]
                    logger.debug("Selecting random entry from different appliances with mindiff")
                    sel_idx = random.choice(poss_user.index)
                    appl = poss_user.ix[sel_idx]['md_appl']

                    details = "similar appliance_multiple users_distance diff"

                elif len(appl_audio_list) == 1:
                    # Multiple contending audio based appliances
                    # If both are audio based or otherwise then use correct label
                    logger.debug("Selecting random entry")
                    sel_idx = random.choice(poss_user.index)
                    appl = poss_user.ix[sel_idx]['md_appl']
                    # appl = correct_label(appliance[sel_user], pd.Series([appliance[sel_user]]),
                    #                      'appliance', edge, location[sel_user])
                    details = "similar appliance_multiple users_distance diff"
                else:
                    # Multiple contending appliances - selecting based on appliance type
                    appl_audio = md_df.ix[appliance[sel_user]]['audio_based']
                    for idx in poss_user.index:
                        md_aud = poss_user.ix[idx]['md_audio']
                        md_appliance = poss_user.ix[idx]['md_appl']

                        if md_aud == appl_audio:
                            appl = md_appliance
                            break
                        else:
                            appl = "Unknown"
                    if appl == "Unknown":
                        poss_user = poss_user[poss_user.md_audio == appl_audio]
                        if len(poss_user) > 0:
                            idx = poss_user.index[0]
                            appl = poss_user.ix[idx]['md_appl']
                    details = "similar appliance_multiple users_audio based"

                user['dev_id'] = [sel_user]
                user['location'] = location[sel_user]
                user['appliance'] = appl

            else:
                # There are contending users for this event

                # Check if <location, appliance> is same for all
                loc_list = poss_user.md_loc.unique()
                appl_list = poss_user.md_appl.unique()

                # If all are non-audio based, then select <location,
                # appliance> pair
                audio_status = False
                for devid in contending_users:
                    if appliance[devid] == "Unknown":
                        continue
                    if appliance[devid] in audio_based:
                        audio_status = True
                        break

                # E.g. Dining Room - Fridge
                if len(loc_list) == 1 and len(appl_list) == 1 and not audio_status:
                    logger.debug("Shared event - same pair! Selecting random user..")
                    # Selecting a random user
                    sel_user = random.choice(contending_users)
                    entry_idx = poss_user[poss_user.dev_id == sel_user].index
                    user['dev_id'] = [sel_user]
                    user['location'] = loc_list[0]
                    user['appliance'] = appl_list[0]

                    details = "similar appliance"

                else:

                    # Matching appliance for resolving conflict
                    idx_list = []
                    poss_user_orig = poss_user.copy()
                    for user_i in contending_users:
                        appl = appliance[user_i]
                        logger.debug("User: %s Appl: %s", user_i, appl)
                        poss_user = poss_user_orig[(poss_user_orig.md_appl == appl) &
                                                   (poss_user_orig.dev_id == user_i)]
                        if len(poss_user) != 0:
                            idx_list += poss_user.index.tolist()
                    poss_user = poss_user_orig.ix[idx_list]

                    logger.debug("Filtered entry for multiple contending users:\n %s", poss_user)
                    contending_users = poss_user.dev_id.unique().tolist()

                    if len(contending_users) == 0:
                        logger.debug("Appliance Classification incorrect")
                        contending_users = poss_user_orig.dev_id.unique().tolist()

                        appl_audio_list = poss_user_orig.md_audio.unique()
                        appl_list = poss_user_orig.md_appl.unique()
                        loc_list = poss_user_orig.md_loc.unique()

                        if len(appl_audio_list) == 1:
                            # If both are audio based or otherwise then use correct label
                            appl = "Unknown"
                            loc = "Unknown"
                            sel_user = "Unknown"

                            details = "similar appliance_audio based confusion"

                        else:
                            appl_dict = {}
                            loc_dict = {}
                            for devid in contending_users:
                                appl_audio = md_df.ix[appliance[devid]]['audio_based']
                                for idx in poss_user_orig.index:
                                    md_aud = poss_user_orig.ix[idx]['md_audio']
                                    md_appliance = poss_user_orig.ix[idx]['md_appl']
                                    md_location = poss_user_orig.ix[idx]['md_loc']
                                    if md_appliance == 'TV':
                                        md_aud = False

                                    if md_aud == appl_audio:
                                        appl_dict[devid] = md_appliance
                                        loc_dict[devid] = md_location

                            if len(appl_dict) == 1:
                                sel_user = [appl_dict.keys[0]]
                                appl = appl_dict[sel_user]
                                loc = loc_dict[sel_user]
                            else:
                                sel_user = "Unknown"
                                loc = "Unknown"
                                appl = "Unknown"

                            details = "similar appliance_audio based"

                        user['dev_id'] = sel_user
                        user['location'] = loc
                        user['appliance'] = appl

                    elif len(contending_users) == 1:
                        # Indicates that there is single contender
                        sel_user = contending_users[0]

                        user['dev_id'] = [sel_user]
                        user['location'] = location[sel_user]
                        user['appliance'] = appliance[sel_user]

                        details = "similar appliance_audio classification"

                    else:
                        # Users share the time slice having the same magnitude
                        # users = poss_user.dev_id.unique().tolist()
                        # if len(users) > 0:
                        logger.debug("Shared event! Selecting random user..")
                        # Selecting a random user
                        sel_user = random.choice(contending_users)
                        entry_idx = poss_user[poss_user.dev_id == sel_user].index
                        user['dev_id'] = [sel_user]
                        user['location'] = location[sel_user]
                        user['appliance'] = poss_user.ix[entry_idx[0]]['md_appl']

                        details = "similar appliance"

            # Offline processing - evaluation - START
            '''
            Check with ground truth and
            attribute reason = activity correction
            '''
            match, reason = match_ground_truth(
                apt_no, edge_time, user['location'], user['appliance'])
            if not match:
                write_reason(apt_no, "common", edge.timestamp, reason, details)
            else:
                write_reason(apt_no, "common", edge.timestamp, "correct", "")

            # Offline processing - evaluation - END

    logger.debug("Matched user(s) for edge with mag %d: %s", magnitude, user)

    return user
