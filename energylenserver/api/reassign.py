from energylenserver.models.functions import *


def correct_inference(user, parameters):
    """
    Reassigns an activity with the given parameters
    """

    print "Reassign called for:", user.name

    try:
        # Unbundle request
        activities = parameters['activities']
        for activity in activities:
            act_id = activity['activity_id']
            true_appl = activity['to_appliance']
            true_loc = activity['to_location']
            incorrect = activity['incorrect']
            time_of_stay = activity['time_of_stay']
            to_occupant_dev_id = activity['to_occupant']

            print "\nActivityID:", act_id
            print "True Appliance", true_appl
            print "True Location", true_loc
            print "Accuracy Status:", incorrect
            print "Time of stay:", time_of_stay
            print "To Occupant:", to_occupant_dev_id

            # Update activity
            # if incorrect and len(true_appl) > 0 and len(true_loc) > 0:
            #     update_activities(act_id, true_appl, true_loc)
    except Exception as e:
        print "[ReassignInferenceException]:: " + str(e)
        return False

    return True
