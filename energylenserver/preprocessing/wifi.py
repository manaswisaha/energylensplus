# Author: Manaswi Saha
# Date: August 27, 2014

import pandas as pd
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

        print ip_df.rssi.mean()
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


def format_data_for_classification(data_df):
    """
    Converts the input data to a format suitable for classification
    Format::
    Location Fingerprint: <time, rssi1, rssi2, rssi3,..., rssiN, location>
    Number of RSSI features: number of unique SSID:MACs seen in the data
    """

    timestamp = data_df.timestamp
    label = data_df.label
    mac_list = sorted(data_df.macid.unique())

    # Output frame
    columns = ['time'] + mac_list + ['label']
    op_df = pd.DataFrame({'time': timestamp, 'label': label}, columns=columns)

    mac_ssid_map = {}
    for mac in mac_list:
        mac_ssid_map[mac] = []

    for idx in data_df.index:
        macid = data_df.ix[idx]['macid']
        ssid = data_df.ix[idx]['ssid']

        mac_ssid_map[macid].append(ssid)

    # Create frame
    for mac in mac_list:
        op_df[mac] = mac_ssid_map[mac]

    op_df.sort(['time'], inplace=True)

    return op_df
