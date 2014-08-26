import numpy as np
import datetime as dt

from smap import get_meter_data_for_time_slice
from edge_detection import *


def compute_power(apt_no, start_time, end_time):
    """
    Computes the power consumption in the given time interval
    """

    print "Computing power..."
    power = np.random.randn()

    # Retrieve power data from smap server for both meters
    # at <start_time> and <end_time>
    s_time = int(start_time) / 1000 - 200
    s_time = dt.datetime.fromtimestamp(s_time).strftime("%Y-%m-%dT%H:%M:%S")

    e_time = int(end_time) / 1000 + 10
    e_time = dt.datetime.fromtimestamp(e_time).strftime("%Y-%m-%dT%H:%M:%S")

    print "Start time:", s_time
    print "End time:", e_time

    df = get_meter_data_for_time_slice(apt_no, s_time, e_time)
    print df

    # Detect edges for both
    # check_if_edge(df)
    # Compute power
    return power

if __name__ == '__main__':
    # m1, m2 = get_meter_info(1002)
    # Light Edge: st = 17.34.04 et =  17.37.39
    # st = 17.43.17 et = 17.44.01
    compute_power(1002, )
    # Power Edge
    compute_power(1002, )
