# Author: Manaswi Saha

import os
import time as t
import pandas as pd
from django.conf import settings
from django_pandas.io import read_frame
from energylenserver.models import functions as mod_func

# Enable Logging
import logging
logger = logging.getLogger('energylensplus_django')


def format_data(ip_df):
    """
    Summarizes data by taking an average over a minute
    """

    try:
        # Clean up data
        ip_df.time = ip_df.time.convert_objects(convert_numeric=True)
        ip_df.rssi = ip_df.rssi.convert_objects(convert_numeric=True)
        ip_df.dropna(inplace=True)

        # Convert timestamps from millisec to seconds
        ip_df[ip_df.columns[0]] = (ip_df[ip_df.columns[0]] / 1000).astype('int')

        # Take the mean of the rssi values based on mac and time
        mean_rssi = ip_df.groupby(['label', 'mac', 'time'])['rssi'].mean()
    except Exception, e:
        logger.exception("[WifiFormatException]::%s", str(e))
        logger.debug("WifiDF::\n%s", str(ip_df.head()))
        return False

    # Make map of mac to ssid
    mac_list = ip_df.mac.unique()
    mac_ssid_map = {}

    for i in mac_list:
        macid = i
        df = ip_df[ip_df.mac == macid][:1]
        idx = df.index[0]
        ssid = df.ix[idx]['ssid']
        mac_ssid_map[macid] = ssid

    time = []
    mac = []
    ssid = []
    rssi = []
    label = []

    for idx, val in enumerate(mean_rssi):
        macid = mean_rssi.index[idx][1]
        time.append(mean_rssi.index[idx][2])
        mac.append(macid)
        ssid.append(mac_ssid_map[macid])
        rssi.append(mean_rssi[idx])
        label.append(mean_rssi.index[idx][0])

    # Output frame
    op_df = pd.DataFrame(
        {'time': time, 'mac_id': mac, 'ssid': ssid, 'rssi': rssi, 'label': label},
        columns=['time', 'mac_id', 'ssid', 'rssi', 'label'])

    op_df.sort(['time'], inplace=True)

    return op_df

base_dir = settings.BASE_DIR


def format_train_data(train_df, apt_no, phone_model):
    """
    Formats training data into features
    """

    logger.debug("Training classes: %s", train_df.label.unique())

    # Output file
    dst_folder = os.path.join(base_dir, 'energylenserver/trained_models/wifi/')
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)
    filename = str(apt_no) + "_" + phone_model + "_" + str(len(train_df))
    traindata_file = dst_folder + filename + "_kNN_" + str(int(t.time())) + '.csv'

    # Feature extraction
    train_df = format_data_for_classification(train_df)

    # Saving data as a csv file
    train_df.to_csv(traindata_file, index=False)

    return train_df


def format_data_for_classification(data_df):
    """
    Converts the input data to a format suitable for classification
    Format::
    Location Fingerprint: <time, rssi1, rssi2, rssi3,..., rssiN, location>
    Number of RSSI features: number of unique SSID:MACs seen in the data
    """

    timestamp = data_df.timestamp
    mac_list = sorted(data_df.macid.unique())
    unique_time = timestamp.unique()
    logger.debug("Total rows: %d", len(data_df))

    # Output frame
    columns = ['time'] + mac_list + ['label']
    op_df = pd.DataFrame({'time': unique_time}, columns=columns, index=[unique_time])

    for idx in data_df.index:
        t = data_df.ix[idx]['timestamp']
        macid = data_df.ix[idx]['macid']
        rssi = data_df.ix[idx]['rssi']
        label = data_df.ix[idx]['label']

        op_df.ix[t, macid] = rssi
        op_df.ix[t, 'label'] = label

    op_df.reset_index(drop=True, inplace=True)

    # Create frame
    for mac in mac_list:
        op_df[mac].fillna(-200, inplace=True)

    op_df.sort(['time'], inplace=True)
    return op_df

    '''
    mac_rssi_map = {}
    for mac in mac_list:
        mac_rssi_map[mac] = []

    # Create Label list
    label_list = []
    for t in unique_time:
        filtered_df = data_df[data_df.timestamp == t]
        tmp_mac_map = {}
        for idx in filtered_df.index:
            macid = filtered_df.ix[idx]['macid']
            rssi = filtered_df.ix[idx]['rssi']

            if macid in tmp_mac_map:
                tmp_mac_map[macid] += rssi
                tmp_mac_map[macid] /= 2
            else:
                tmp_mac_map[macid] = rssi

        mac_rssi_map[macid].append(tmp_mac_map[macid])

        l = filtered_df.label.unique().tolist()
        label_list.append(l[0])

    logger.debug("Len of MACRSSIMAP: %d", len(mac_rssi_map[macid]))
    logger.debug("Len of LabelList: %d", len(label_list))
    logger.debug("Len of OPDF: %d", len(op_df))

    op_df['label'] = label_list
    '''
