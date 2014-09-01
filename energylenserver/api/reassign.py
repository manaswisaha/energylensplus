import sys
print sys.path
from models.functions import *


def correct_inference(reg_id, parameters):
    """
    Reassigns an activity with the given parameters
    """

    # Unbundle request
    act_id = parameters['activity_id']
    start_time = parameters['start_time']
    end_time = parameters['end_time']
    to_appl = parameters['to_appliance']
    to_loc = parameters['to_location']

    user = determine_user(reg_id)
    if not user:
        return False

    print "Reassign called for:", user.name

    print "ActivityID:", act_id
    print "Start Time:", start_time
    print "End Time", end_time
    print "To Appliance", to_appl
    print "To Location", to_loc

    # TODO: Add editing the existing activity with the new details

    return True
