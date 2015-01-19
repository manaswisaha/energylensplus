# Participating apartments
apt_no_list = ['1201', '102A', '101']  # , '1003', '1002']

# Default users
unknown_id = 123456789123456
all_id = 987654321654321

# Appliance types
appliance_dict = {'fan': {'audio': True, 'presence': True},
                  'tv': {'audio': True, 'presence': True},
                  'ac': {'audio': True, 'presence': True},
                  'microwave': {'audio': True, 'presence': False},
                  'music system': {'audio': True, 'presence': False},
                  'geyser': {'audio': False, 'presence': False},
                  'iron': {'audio': False, 'presence': True},
                  'grinder': {'audio': True, 'presence': True},
                  }

# Constants for sending response messages
ERROR_INVALID_REQUEST = {"type": "ERROR", "code": 0, "message": "Invalid request made"}

UPLOAD_SUCCESS = {"type": "SUCCESS", "code": 1, "message": "CSV file successfully uploaded"}
UPLOAD_UNSUCCESSFUL = {"type": "ERROR", "code": 2, "message": "CSV file upload unsuccessful"}

REGISTRATION_SUCCESS = {"type": "SUCCESS", "code": 3, "message": "User was successfully registered"}
REGISTRATION_UNSUCCESSFUL = {"type": "ERROR", "code": 4, "message": "User was not registered"}

REALTIMEDATA_UNSUCCESSFUL = {
    "type": "ERROR", "code": 5, "message": "Error while retrieving power data"}

TRAINING_UNSUCCESSFUL = {
    "type": "ERROR", "code": 6, "message": "Error while retrieving power data"}

REASSIGN_SUCCESS = {"type": "SUCCESS", "code": 7,
                    "message": "Inferences were sucessfully reassigned"}
REASSIGN_UNSUCCESSFUL = {"type": "ERROR", "code": 8, "message": "Inferences were not reassigned"}

# API Names
from api.constants import *

# Meter Data Processing Constants
from meter.constants import *
