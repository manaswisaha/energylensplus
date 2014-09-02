"""
Setup Django Environment
"""
import os
import sys

energyplus_path = '/home/manaswi/EnergyLensPlusCode/energylensplus'
energylenserver_path = '/home/manaswi/EnergyLensPlusCode/energylensplus/energylenserver'

if energyplus_path not in sys.path:
    sys.path.insert(0, energyplus_path)
    os.environ['DJANGO_SETTINGS_MODULE'] = "energylensplus.settings"

if energylenserver_path not in sys.path:
    sys.path.insert(1, energylenserver_path)


# print "SYSPATH", sys.path
