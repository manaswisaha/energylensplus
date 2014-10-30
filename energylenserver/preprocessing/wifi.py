# Author: Manaswi Saha
# Date: August 27, 2014

import pandas as pd
# Enable Logging
import logging
logger = logging.getLogger('energylensplus_django')


def format_data(ip_df):
    """
    Script to convert labeled phone Wifi test data into the desired form
    Format::
    Location Fingerprint: <time, rssi1, rssi2, rssi3,..., rssiN, location>
    Number of RSSI features: number of unique SSID:MACs seen in the data

    """

    # print "Number of records before preprocessing:" + str(len(ip_df))

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

    # Output csv file
    op_df = pd.DataFrame(
        {'time': time, 'mac_id': mac, 'ssid': ssid, 'rssi': rssi, 'label': label},
        columns=['time', 'mac_id', 'ssid', 'rssi', 'label'])

    op_df.sort(['time'], inplace=True)

    # print "Number of records after preprocessing:" + str(len(op_df))

    return op_df
