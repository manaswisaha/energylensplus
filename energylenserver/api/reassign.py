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
        logger.debug("Activities: %s", activities)
        for activity in activities:
            act_id = activity['activity_id']

            incorrect = activity['incorrect']
            time_of_stay = int(activity['time_of_stay'])

            # Parameters that may be empty [who,what,where,when]
            start_time = activity['start_time']
            end_time = activity['end_time']
            true_loc = activity['to_location']
            true_appl = activity['to_appliance']
            to_occupant_dev_id = activity['to_occupant']

            # ----- Debugging ------
            st_str = ''
            if start_time != "":
                st_str = time.ctime(start_time)
            et_str = ''
            if end_time != "":
                et_str = time.ctime(end_time)

            logger.debug("ActivityID: %s", act_id)
            logger.debug("Start time: %s", st_str)
            logger.debug("End time: %s", et_str)
            logger.debug("True Appliance: %s", true_appl)
            logger.debug("True Location: %s", true_loc)
            logger.debug("Incorrect Status: %s", incorrect)
            logger.debug("Time of stay: %s", time_of_stay)
            logger.debug("To Occupant: %s\n", to_occupant_dev_id)
            # ----- Debugging ------

            try:
                # Update activity
                act_record = mod_func.get_activity_by_id(act_id)

                # When
                if len(str(start_time)) == 0:
                    start_time = act_record.start_time
                if len(str(end_time)) == 0:
                    end_time = act_record.end_time

                # Where
                if len(true_loc) == 0:
                    true_loc = act_record.location

                # What
                if len(true_appl) == 0:
                    true_appl = act_record.appliance

                # Who
                if len(str(to_occupant_dev_id)) == 0:
                    to_occupant = submitted_by
                else:
                    to_occupant = mod_func.get_user(to_occupant_dev_id)

                # Store entry
                gt_entry = GroundTruthLog(by_dev_id=submitted_by, act_id=act_record,
                                          incorrect=incorrect,
                                          start_time=start_time, end_time=end_time,
                                          appliance=true_appl, location=true_loc,
                                          time_of_stay=time_of_stay,
                                          occupant_dev_id=to_occupant)

                gt_entry.save()
                logger.debug("Validation report entries marked by %s saved!", submitted_by)

            except Exception, e:
                logger.exception("[UpdateActivitiesException]:: %s", str(e))
                return False
            # '''

        # TESTING CODE
        # return False

    except Exception, e:
        logger.exception("[ReassignInferenceException]:: %s", str(e))
        return False
    return True
