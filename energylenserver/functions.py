import time
import datetime as dt


def str_to_timestamp(time_str, format_string):
    t = dt.datetime.strptime(time_str, format_string)
    return time.mktime(t.timetuple())


def timestamp_to_str(time, format_string):
    return dt.datetime.fromtimestamp(time).strftime(format_string)
