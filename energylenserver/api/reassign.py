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
        for activity in activities:
            act_id = activity['activity_id']
            true_appl = activity['to_appliance']
            true_loc = activity['to_location']
            incorrect = activity['incorrect']
            time_of_stay = activity['time_of_stay'] / 1000
            to_occupant_dev_id = activity['to_occupant']

            logger.debug("ActivityID: %s", act_id)
            logger.debug("True Appliance: %s", true_appl)
            logger.debug("True Location: %s", true_loc)
            logger.debug("Accuracy Status: %s", incorrect)
            logger.debug("Time of stay: %s", time_of_stay)
            logger.debug("To Occupant: %s\n", to_occupant_dev_id)

            # Update activity
            if true_appl == "":
                logger.debug("Empty strings")
            if incorrect:
                if len(true_appl) > 0 or len(true_loc) > 0:
                    if mod_func.update_activities(act_id, true_appl, true_loc):
                        logger.debug("Update successful!")
                        return True
                    else:
                        logger.debug("Update unsuccessful!")
                        return False
    except Exception, e:
        logger.error("[ReassignInferenceException]:: %s", str(e))
        return False

    return True
