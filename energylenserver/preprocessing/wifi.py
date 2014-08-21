# Script to convert labeled phone Wifi test data into the desired form
# Format::
# Location Fingerprint: <time, rssi1, rssi2, rssi3,..., rssiN, location>
# Number of RSSI features: number of unique SSID:MACs seen in the data
# Operations done:
#	1.
#
# Author: Manaswi Saha
# Date: August 7, 2014

import pandas as pd


def format_data(ip_df):

    print "Number of records before preprocessing:", len(ip_df)

    # Convert timestamps from millisec to seconds
    ip_df[ip_df.columns[0]] = (ip_df[ip_df.columns[0]] / 1000).astype('int')

    # Take the mean of the rssi values based on mac and time
    mean_rssi = ip_df.groupby(['label', 'mac', 'time'])['rssi'].mean()

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

    print "Number of records after preprocessing:", len(op_df)

    return op_df

if __name__ == '__main__':
    csvfile = 'testdata/354994050433123_upload_wifi_log_07-08-2014_12-19-38.csv'
    ip_df = pd.read_csv(csvfile)
    df = format_data(ip_df)
