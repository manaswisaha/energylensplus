"""
Setup Django Environment
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
energyplus_path = BASE_DIR
energylenserver_path = (energyplus_path + '/energylenserver')

if energyplus_path not in sys.path:
    sys.path.insert(1, energyplus_path)
    os.environ['DJANGO_SETTINGS_MODULE'] = "energylensplus.settings"

if energylenserver_path not in sys.path:
    sys.path.insert(2, energylenserver_path)


# print "SYSPATH", sys.path
