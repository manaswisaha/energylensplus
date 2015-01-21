import math
import pandas as pd
import numpy as np
from django_pandas.io import read_frame

from common_imports import *
from energylenserver.models import functions as mod_func
from classifier import classify_activity, correct_label
from functions import exists_in_metadata

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

    # Get Metadata
    data = mod_func.retrieve_metadata(apt_no)
    metadata_df = read_frame(data, verbose=False)

    m_magnitude = math.fabs(magnitude)

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

        if magnitude < 0:
            # May indicate a non-presence based appliance e.g. Microwave
            # -- Use metadata i.e. meter only approach
            where, what = classify_activity(metadata_df, m_magnitude)

            if len(user_list) == 1:
                user['dev_id'] = user_list[0]
            user['dev_id'] = "Unknown"
            user['location'] = where
            user['appliance'] = what
            return user

        user['dev_id'] = "Unknown"
        user['location'] = "Unknown"
        user['appliance'] = "Unknown"
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
            # Indicates that there is single contender
            dev_id = contending_users[0]

            appl_list = poss_user.md_appl.unique()

            if len(appl_list) == 1:
                appliance = appl_list[0]
            else:
                appliance = correct_label(appliance[dev_id], pd.Series([appliance[dev_id]]),
                                          'appliance', edge, location[dev_id])

            user['dev_id'] = [dev_id]
            user['location'] = location[dev_id]
            user['appliance'] = appliance

        else:
            # Resolving conflict by
            # selected entry with least distance to the metadata
            poss_user = poss_user[
                poss_user.md_power_diff == poss_user.md_power_diff.min()]
            logger.debug(
                "Entry for multiple contending users with md_power_diff:\n %s", poss_user)
            contending_users = poss_user.dev_id.unique().tolist()

            if len(contending_users) == 1:
                # Indicates that there is single contender
                dev_id = contending_users[0]

                user['dev_id'] = [dev_id]
                user['location'] = location[dev_id]
                user['appliance'] = appliance[dev_id]

            else:
                # There are contending users for this edge
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

                    user['dev_id'] = "Unknown"
                    user['location'] = "Unknown"
                    user['appliance'] = "Unknown"

                elif len(contending_users) == 1:
                    # Indicates that there is single contender
                    dev_id = contending_users[0]

                    user['dev_id'] = [dev_id]
                    user['location'] = location[dev_id]
                    user['appliance'] = appliance[dev_id]

                else:
                    # Users share the time slice having the same magnitude
                    users = poss_user.dev_id.unique().tolist()
                    if len(users) > 0:
                        logger.debug("Shared event! Selecting random user..")
                        # Selecting a random user
                        user['dev_id'] = [users[0]]
                        user['location'] = location[users[0]]
                        user['appliance'] = appliance[users[0]]
                    else:
                        user['dev_id'] = "Unknown"
                        user['location'] = "Unknown"
                        user['appliance'] = "Unknown"

    logger.debug("Matched user(s) for edge with mag %d: %s", m_magnitude, user)

    return user
