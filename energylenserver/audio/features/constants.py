from MFCC import *
# General Parameters


FS = 8000                       		# Sampling rate

# ---Frame length and frame shift calculation---
frm_len = 1024        						# Frame length e.g. 512 samples or 64ms
no_of_sec = float(frm_len) / FS 			# No of seconds in a sample
FRAME_LEN = int(no_of_sec * FS)
FRAME_SHIFT = int((no_of_sec / 2) * FS)     # Frame shift = 50% overlap
WINDOW = hamming(FRAME_LEN)        			# Window function
