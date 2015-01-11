"""
Preprocessing Audio for feature extraction

Author: Manaswi Saha
"""
# Enable Logging
import logging
logger = logging.getLogger('energylensplus_django')

import pandas as pd


def format_data_for_classification(df):
    """
    Formats raw audio data: Separate out individual records
    """

    columns = ['time', 'value', 'label', 'location']

    time_l = []
    label_l = []
    location_l = []
    value_l = []
    frac = 0.0
    for idx in df.index[:-1]:
        curr_time = float(df.ix[idx]['timestamp'])
        next_time = float(df.ix[idx + 1]['timestamp'])
        diff = next_time - curr_time

        label = df.ix[idx]['label']
        location = df.ix[idx]['location']
        values = df.ix[idx]['value']
        values = values.split(',')
        len_values = len(values)
        # logger.debug("Length: %s", len_values)

        frac = float(diff) / len_values

        # print "diff", diff
        # print "Fraction", frac

        time_to_add = curr_time
        for j in values:
            time_l.append(float(time_to_add))
            value_l.append(j)
            label_l.append(label)
            location_l.append(location)
            time_to_add += frac

    # For the entry at the last index
    idx = df.index[-1]
    curr_time = df.ix[idx]['timestamp']
    label = df.ix[idx]['label']
    location = df.ix[idx]['location']
    values = df.ix[idx]['value']
    values = values.split(',')
    len_values = len(values)
    logger.debug("Length: %s", len_values)
    logger.debug("Fraction: %s", frac)

    time_to_add = curr_time
    for j in values:
        time_l.append(float(time_to_add))
        value_l.append(j)
        label_l.append(label)
        location_l.append(location)
        time_to_add += frac
    # logger.debug("Total number of entries", len(time_l))

    df = pd.DataFrame(
        {'time': time_l, 'value': value_l, 'label': label_l,
                         'location': location_l}, columns=columns)

    return df
