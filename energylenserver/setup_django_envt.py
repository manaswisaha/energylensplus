"""
Setup Django Environment
"""
import os
import sys

sys.path.insert(1, '/home/manaswi/EnergyLensPlusCode/energylensplus')
# print "SYSPATH", sys.path
os.environ['DJANGO_SETTINGS_MODULE'] = "energylensplus.settings"
