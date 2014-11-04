import pandas as pd
import numpy as np

from common_imports import *
from constants import lower_mdp_percent_change, upper_mdp_percent_change
from energylenserver.models import functions as mod_func

"""
User Attribution Module
"""


def identify_user(apt_no, magnitude, location, appliance, user_list):
    """
    Identifies the occupant who performed the inferred activity
    """
    user = {}

    # Get Metadata
    data = mod_func.retrieve_metadata(apt_no)
    metadata_df = read_frame(data, verbose=False)

    magnitude = math.fabs(magnitude)

    for dev_id in user_list:
        loc_user = location[dev_id]

        # Extract metadata for the current location of the user
        mdf = metadata_df[(metadata_df.location == loc_user)]
        for md_i in mdf.index:
            md_power = mdf.ix[md_i]['power']
            md_appl = mdf.ix[md_i]['appliance']

            min_md_power = math.floor(md_power - lower_mdp_percent_change * md_power)
            max_md_power = math.ceil(md_power + upper_mdp_percent_change * md_power)

            # Compare magnitude and metadata power draw
            logger.debug("For edge with magnitude %s :: [min_power=%s, max_power=%s]", magnitude,
                         min_md_power, max_md_power)

            # Matching metadata with inferred
            if magnitude >= min_md_power and magnitude <= max_md_power:
                md_power_diff = math.fabs(md_power - magnitude)
                df_list.append(
                    pd.DataFrame({'dev_id': dev_id, 'md_appl': md_appl,
                                  'md_power_diff': md_power_diff}, index=[magnitude]))
    if len(df_list) == 0:
        logger.debug("Edge did not match with the metadata for any user.")
        logger.debug("Location classification is incorrect")

        user['dev_id'] = "not_found"
        user['location'] = "not_found"
        user['appliance'] = "not_found"
        return user

    # Select the entry with the matching appliance for a user
    # For conflicting appliances between users, choose the one with least distance
    # from the metadata (comparing between two users)

    # DF with contending users for the edge
    poss_user = pd.concat(df_list)
    poss_user = poss_user.reset_index(drop=True)
    print "Possible User - Time Slice Contenders\n", poss_user

    if len(poss_user) > 0:
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
            for user in contending_users:
                appl = appliance[user]
                poss_user = poss_user[poss_user.md_appl == appl]
                if len(poss_user) == 0:
                    idx = poss_user.index[np.where(poss_user.dev_id == user)[0]]
                    # Remove records
                    poss_user = poss_user.drop(idx)

            logger.debug("Filtered entry for multiple contending users:\n %s", poss_user)
            contending_users = poss_user.dev_id.unique().tolist()

            if len(contending_users) == 0:
                logger.debug("Appliance Classification incorrect")

                user['dev_id'] = "not_found"
                user['location'] = "not_found"
                user['appliance'] = "not_found"
            elif len(contending_users) == 1:
                # Indicates that there is single contender
                dev_id = contending_users[0]

                user['dev_id'] = [dev_id]
                user['location'] = location[dev_id]
                user['appliance'] = appliance[dev_id]

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
                    # Users share the time slice having the same magnitude
                    users = poss_user['dev_id'].unique().tolist()
                    if len(users) > 0:
                        user['dev_id'] = users
                        user['location'] = location[users[0]]
                        user['appliance'] = appliance[users[0]]
                    else:
                        user['dev_id'] = "not_found"
                        user['location'] = "not_found"
                        user['appliance'] = "not_found"

    logger.debug("Matched user(s) for edge with mag %d: %s", magnitude, user)

    return user
