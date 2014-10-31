import pandas as pd
import numpy as np
from common_imports import *

"""
User Attribution Module
"""


def identify_user(location, appliance, user_list):
    """
    Identifies the occupant who performed the inferred activity
    """
    user = {}
    user['dev_id'] = "devid"
    user['location'] = "room"
    user['appliance'] = "appliance"

    return user
