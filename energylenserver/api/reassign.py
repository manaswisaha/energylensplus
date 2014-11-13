import time

from energylenserver.models import functions as mod_func
from energylenserver.models.models import GroundTruthLog

# Enable Logging
import logging
logger = logging.getLogger('energylensplus_django')


def correct_inference(user, parameters):
    """
    Reassigns an activity with the given parameters
    """

    submitted_by = user
    logger.debug("Reassign called for: %s", submitted_by.name)

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
            start_time = activity['start_time']
            end_time = activity['end_time']

            logger.debug("ActivityID: %s", act_id)
            logger.debug("Start time: %s", time.ctime(start_time))
            logger.debug("End time: %s", time.ctime(end_time))
            logger.debug("True Appliance: %s", true_appl)
            logger.debug("True Location: %s", true_loc)
            logger.debug("Incorrect Status: %s", incorrect)
            logger.debug("Time of stay: %s", time_of_stay)
            logger.debug("To Occupant: %s", to_occupant_dev_id)

            # ----- TESTING -----
            if incorrect:
                logger.debug("Inference incorrect!\n")
            else:
                logger.debug("Inference correct!\n")
            continue
            # ----- TESTING -----

            try:
                # Update activity
                act_record = mod_func.get_activity_by_id(act_id)
                to_occupant = mod_func.get_user(to_occupant_dev_id)

                gt_entry = GroundTruthLog(by_dev_id=submitted_by, act_id=act_record,
                                          incorrect=incorrect,
                                          start_time=start_time, end_time=end_time,
                                          appliance=true_appl, location=true_loc,
                                          time_of_stay=time_of_stay,
                                          occupant_dev_id=to_occupant)

                gt_entry.save()

            except Exception, e:
                logger.error("[UpdateActivitiesException]:: %s", str(e))
                return False

        # TESTING CODE
        return False

    except Exception, e:
        logger.error("[ReassignInferenceException]:: %s", str(e))
        return False
    return True
