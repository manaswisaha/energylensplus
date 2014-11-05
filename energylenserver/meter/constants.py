# Meter Sampling Rate
sampling_rate = 2
# Edge Transition Window (in seconds)
# for the change to take place
# its more for simultaneous or quick sequential activity
lwinmin = 3
pwinmin = 3
# lwinmin = pwinmin

# Common for both edges
if sampling_rate in [1, 2, 3]:
    winmin = 3
    winmax = 6
else:
    winmin = 1
    winmax = 3

# Power Threshold (in Watts) for the magnitude of the change
lthresmin = 10   # for light meter
pthresmin = 15  # for power meter
# pthresmin = lthresmin
thresmin = 15

# Power Percent Change between rising and falling edge
percent_change = 0.31

# Time difference the phone with the meter data
time_diff = 5
