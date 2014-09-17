import numpy as np
from constants import WIFI_THRESHOLD
from energylenserver.models import functions as mod_func
from django_pandas.io import read_frame

"""
Contains common preprocessing functions
"""


def determine_user_home_status(event_time, apt_no):
    """
    Determines if user is at home by seeing if the WiFi AP is visible
    within the event time window

    :param event_time:
    :return list of users at home:
    """
    user_list = []

    p_window = 60  # window for each side of the event time (in seconds)

    start_time = event_time - p_window
    end_time = event_time + p_window

    try:
        occupants = mod_func.retrieve_users(apt_no)
        occupants_df = read_frame(occupants, verbose=False)

        dev_id_list = [occupants_df.ix[idx]['dev_id'] for idx in occupants_df.index]

        # Get Home AP
        home_ap = mod_func.get_home_ap(apt_no)

        # Get Wifi data
        data = mod_func.get_sensor_data("wifi", "test", start_time, end_time, dev_id_list)
        data_df = read_frame(data, verbose=False)

        print "Users:", data_df.dev_id.unique()
        print "Number of retrieved entries:", len(data_df)

        # Check for each user, if he/she present in the home
        for idx in occupants_df.index:
            user_id = occupants_df.ix[idx]['dev_id']
            # Filter data_df based on dev_id
            df = data_df[data_df.dev_id == user_id]

            if len(df.index) < 1:
                continue
            # Check if any mac id matches with the home ap
            match_idx_list = np.where((df.macid == home_ap) & (df.rssi > WIFI_THRESHOLD))[0]
            print("%s:%s" % (user_id, match_idx_list))
            if len(match_idx_list) > 0:
                user_list.append(user_id)

    except Exception, e:
        print "[HomeStatusException]::", str(e)

    return user_list


def determine_phone_with_user(event_time, user_list):
    """
    Determines if the phone is with the user_list
    """
    return True
