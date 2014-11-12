from energylenserver.models import functions as mod_func

# Enable Logging
import logging
logger = logging.getLogger('energylensplus_django')


def correct_inference(user, parameters):
    """
    Reassigns an activity with the given parameters
    """

    logger.debug("Reassign called for: %s", user.name)

    try:
        # Unbundle request
        activities = parameters['activities']
        logger.debug("activities: %s", activities)
        for activity in activities:
            act_id = activity['activity_id']
            true_appl = activity['to_appliance']
            true_loc = activity['to_location']
            incorrect = activity['incorrect']
            time_of_stay = int(activity['time_of_stay'])
            to_occupant_dev_id = activity['to_occupant']

            logger.debug("ActivityID: %s", act_id)
            logger.debug("True Appliance: %s", true_appl)
            logger.debug("True Location: %s", true_loc)
            logger.debug("Incorrect Status: %s", incorrect)
            logger.debug("Time of stay: %s", time_of_stay)
            logger.debug("To Occupant: %s", to_occupant_dev_id)

            start_time = activity['start_time']
            logger.debug("To start time: %s", start_time)

            end_time = activity['end_time']
            logger.debug("To end time: %s\n", end_time)

            # Update activity
            if incorrect:
                if len(true_appl) > 0 or len(true_loc) > 0:
                    if mod_func.update_activities(act_id, true_appl, true_loc):
                        logger.debug("Update successful!")
                        return True
                    else:
                        logger.debug("Update unsuccessful!")
                        return False
            # If correct
            else:
                # Copy the predicted appliances to true columns
                pass
    except Exception, e:
        logger.error("[ReassignInferenceException]:: %s", str(e))
        return False

    return True
