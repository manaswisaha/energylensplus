import json

from models import *
from energylenserver.constants import DISAGG_ENERGY_API


def determine_user(reg_id):
    """
    Determine the user with the given reg id
    """
    try:
        user = RegisteredUsers.objects.get(reg_id__exact=reg_id)
    except RegisteredUsers.DoesNotExist, e:
        print "[UserDoesNotExistException Occurred] No registration found!:: ", e
        return False

    return user


def retrieve_metadata(apt_no):
    """
    Retrieve appliances from Metadata
    """
    appliances = []
    try:
        records = Metadata.objects.filter(apt_no__exact=apt_no)
        print "Number of metadata entries:", records.count()
        for r in records:
            appliances.append({'location': r.location, 'appliance': r.appliance})
        print "Appliances::\n", json.dumps(appliances)

    except Exception, e:
        print "[GetMetadataException]::", DISAGG_ENERGY_API, e

    # temp code
    appliances.append(
        {'location': 'Dining Room', 'appliance': 'Light'})
    appliances.append(
        {'location': 'Dining Room', 'appliance': 'Fan'})
    appliances.append(
        {'location': 'Dining Room', 'appliance': 'AC'})
    appliances.append(
        {'location': 'Bedroom', 'appliance': 'TV'})
    appliances.append(
        {'location': 'Bedroom', 'appliance': 'Light'})
    appliances.append(
        {'location': 'Bedroom', 'appliance': 'AC'})

    return appliances
