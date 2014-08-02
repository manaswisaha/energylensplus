"""
Preprocessing Audio before storing into the DB

Author: Manaswi Saha
"""
import pandas as pd


# Separate out individual records

def format_data(df):

    columns = ['time', 'value', 'label', 'location']

    time_l = []
    label_l = []
    location_l = []
    value_l = []
    frac = 0.0
    for idx in df.index[:-1]:
        curr_time = long(df.ix[idx]['time'])
        next_time = long(df.ix[idx + 1]['time'])
        diff = next_time - curr_time

        label = df.ix[idx]['label']
        location = df.ix[idx]['location']
        values = df.ix[idx]['values']
        values = values.split(',')
        len_values = len(values)
        # print "Length", len_values

        frac = float(diff) / len_values

        # print "diff", diff
        # print "Fraction", frac

        time_to_add = curr_time
        for j in values:
            time_l.append(long(time_to_add))
            value_l.append(j)
            label_l.append(label)
            location_l.append(location)
            time_to_add += frac

    # For the entry at the last index
    print "Last index", df.index[-1]
    idx = df.index[-1]
    curr_time = df.ix[idx]['time']
    label = df.ix[idx]['label']
    location = df.ix[idx]['location']
    values = df.ix[idx]['values']
    values = values.split(',')
    len_values = len(values)
    print "Length", len_values
    print "Fraction", frac

    time_to_add = curr_time
    for j in values:
        time_l.append(long(time_to_add))
        value_l.append(j)
        label_l.append(label)
        location_l.append(location)
        time_to_add += frac
    # print "Total number of entries", len(time_l)

    df_new = pd.DataFrame(
        {'time': time_l, 'value': value_l, 'label': label_l,
                         'location': location_l}, columns=columns)

    return df_new
