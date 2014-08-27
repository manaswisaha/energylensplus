"""
Script to retrieve meter data from smap db using republish API
and pass them to the edge_detection API on the EnergyLens+ Server

Input: apt number
Output: csv file with timestamped power values of all phases
Format: <timestamp, powerphase1, powerphase2, powerphase3, power>

Author: Manaswi Saha
Date: 20th Aug 2014
"""

import requests
import numpy as np
import pandas as pd
import datetime
import pycurl
import json

TIMEZONE = 'Asia/Kolkata'

"""
Time range syntax: %m/%d/%Y, %m/%d/%Y %H:%M, or %Y-%m-%dT%H:%M:%S.
For instance 10/16/1985 and 2/29/2012 20:00 are valid

Example query:
payload="select data in (now -5minutes, now) where
Metadata/Extra/FlatNumber ='103' and Metadata/Extra/PhysicalParameter='PowerPhase1'
and Metadata/Extra/Type='Power'"

Refer: http://www.cs.berkeley.edu/~stevedh/smap2/archiver.html
# curl -XPOST -d 'Metadata/Extra/FlatNumber ="1002" and Metadata/Extra/PhysicalParameter="Power"
and Metadata/Extra/Type="Power"' http://energy.iiitd.edu.in:9106/republish

"""

# Input
apt_no = '1002'

# Destination Folder for the output files
dst_folder = 'data/meter/' + apt_no + '/'

# Processing: Get data
power = []
lpower = []
url = "http://energy.iiitd.edu.in:9106/republish"
#------------------------------------------------------------------------------

# Payload
payload = ("Metadata/Extra/FlatNumber ='" + apt_no + "' and "
           "Metadata/Extra/PhysicalParameter='Power'")
print "[" + payload + "]"

class Client:
  def __init__(self):
    self.buffer = ""
    self.conn = pycurl.Curl()
    self.conn.setopt(pycurl.USERPWD, "%s:%s" % (USER, PASS))
    self.conn.setopt(pycurl.URL, STREAM_URL)
    self.conn.setopt(pycurl.WRITEFUNCTION, self.on_receive)
    self.conn.perform()

  def on_receive(self, data):
    self.buffer += data
    if data.endswith("rn") and self.buffer.strip():
      content = json.loads(self.buffer)
      self.buffer = ""
      print content


client = Client()

def on_receive(r):
    print "Data"
    print r

    # r = json.loads(r)
    #
    # readings = np.array(r[0]['Readings'])
    # print readings

    # df1 = (
    #     pd.DataFrame(
    #         np.zeros((len(readings), 6)), columns=['time', 'powerphase1', 'powerphase2',
    #                                                'powerphase3', 'power', 'powerfactor']))
    # df1['time'] = time = readings[:, 0] / 1000
    # df1['power'] = pwr = readings[:, 1]
    # tp = np.array([datetime.datetime.fromtimestamp(x) for x in time])

conn = pycurl.Curl()
conn.setopt(pycurl.URL, url)
conn.setopt(pycurl.WRITEFUNCTION, on_receive)
conn.setopt(pycurl.HTTPPOST)
conn.perform()
'''
    # Get Power Factor
    payload = ("select * "
               "limit 200000 "
               "where Metadata/LoadLocation/FlatNumber ='" + apt_no + "' and "
               "Metadata/Extra/PhysicalParameter='PowerFactor' and Metadata/Instrument/SupplyType='Power'")
    print payload

    r = requests.post(url, data=payload)
    # print r.json()
    readings = np.array(r.json()[0]['Readings'])

    df1['powerfactor'] = readings[:, 1]

    # Get three power phases
    for i in range(1, 4):
        payload = ("select * "
                   "limit 200000 "
                   "where Metadata/Extra/FlatNumber ='" + apt_no + "' and "
                   "Metadata/Extra/PhysicalParameter='PowerPhase" + str(i) +
                   "' and Metadata/Instrument/SupplyType='Power'")
        print payload

        r = requests.post(url, data=payload)
        # print r
        readings = np.array(r.json()[0]['Readings'])
        df1['powerphase' + str(i)] = p = readings[:, 1]
        power.append(p)

    #------------------------------------------------------------------------------

    # Store lighting power
    payload = ("select * "
               "limit 200000 "
               "where Metadata/Extra/FlatNumber ='" + apt_no + "' and "
               "Metadata/Extra/PhysicalParameter='Power' and Metadata/Instrument/SupplyType='Light Backup'")

    r = requests.post(url, data=payload)
    readings = np.array(r.json()[0]['Readings'])

    df2 = (pd.DataFrame(np.zeros((len(readings), 6)),
           columns=['time', 'lightphase1', 'lightphase2', 'lightphase3', 'lightpower', 'powerfactor']))
    df2['time'] = time = readings[:, 0] / 1000
    df2['lightpower'] = lpwr = readings[:, 1]
    tl = np.array([datetime.datetime.fromtimestamp(x) for x in time])

    # Get Power Factor
    payload = ("select * "
               "limit 200000 "
               "where Metadata/LoadLocation/FlatNumber ='" + apt_no + "' and "
               "Metadata/Extra/PhysicalParameter='PowerFactor' and Metadata/Instrument/SupplyType='Light Backup'")
    print payload

    r = requests.post(url, data=payload)
    readings = np.array(r.json()[0]['Readings'])
    df2['powerfactor'] = readings[:, 1]

    # Get three power phases
    for i in range(1, 4):
        # payload = ("select data in ('9/21/2013 18:30', '9/21/2013 21:30') "
        #   "where Metadata/Extra/FlatNumber ='"+ apt_no + "' and "
        #   "Metadata/Extra/PhysicalParameter='PowerPhase"+ str(i) +
        # "' and Metadata/Instrument/SupplyType='Power'")
        payload = ("select * "
                   "limit 200000 "
                   "where Metadata/Extra/FlatNumber ='" + apt_no + "' and "
                   "Metadata/Extra/PhysicalParameter='PowerPhase" + str(i) +
                   "' and Metadata/Instrument/SupplyType='Light Backup'")
        print payload

        r = requests.post(url, data=payload)
        # print r
        readings = np.array(r.json()[0]['Readings'])
        df2['lightphase' + str(i)] = p = readings[:, 1]
        lpower.append(p)
'''
