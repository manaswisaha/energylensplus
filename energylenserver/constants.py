
# Constants for sending response messages
ERROR_INVALID_REQUEST = {"type": "ERROR", "code": 0, "message": "Invalid request made"}

UPLOAD_SUCCESS = {"type": "SUCCESS", "code": 1, "message": "Data was successfully uploaded"}
UPLOAD_UNSUCCESSFUL = {"type": "ERROR", "code": 2, "message": "Data was not uploaded"}

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

'''
# JSON Messages: Request/Response Format

# API: power/real-time/
# -- request
payload = {"dev_id": <IMEI number>}

# -- response
payload = {"timestamp" : <>, "value": <>}


# API: data/training/
# -- request
payload = {
    "dev_id": <IMEI number>,
    "start_time": <start time of training>,
    "end_time": <end time of training>,
    "location": <location label>,
    "appliance": <appliance label>
}

# -- response
payload = {"power" : <power consumed by the appliance>}


# General structure
data = {
    "msg_type": "request/ response",
    "api": "energy/personal/; energy/disaggregated/; power/real-time/; energy/comparison/;"
    "energy/wastage/; energy/report/",
    "options": "{...}"
}

# API: personal_energy
#  -- request
data = {
    "msg_type": "request",
    "api": "energy/personal/",
    "options": {
        "start_time": "<start_time in epoch or strings such as 'now'>",
        "end_time": "<end_time in epoch or strings such as 'last n hours/days/weeks'>"

    }
}

# -- response
data = {
    "msg_type": "response",
    "api": "energy/personal/",
    "options": {
                "total_consumption": "<total energy consumption in kWh>",
                "hourly_consumption": ['hour_1', 'hour_2', ..., 'hour_n'],
                "activities": [
                    {"name": "TV", "usage": "in kWh"},
                    {"name": "AC", "usage": "in kWh"}, ...,
                    {"name": "ApplN", "usage": "in kWh"}
                ]
    }
}

# API: disaggregated_energy
# -- request
data = {
    "msg_type": "request",
    "api": "energy/disaggregated/",
    "options": {
        "activity_name": "TV"
        "start_time": "<start_time in epoch or strings such as 'now'>",
        "end_time": "<end_time in epoch or strings such as 'last n hours/days/weeks'>"

    }
}

# -- response
data = {
    "msg_type": "response",
    "api": "energy/disaggregated/",
    "options": {
        "activities": [
            {"id": 123,
             "name": "TV",
             "location": "Bedroom/ Dining Room/ etc."
             "usage": "in kWh",
             "start_time": "epoch_time",
             "end_time": "epoch_time"
             }, {}, ..., {}
        ]
        "appliances": [
            {"location" : "Dining Room",
             "appliance": "TV"},
            {}, {}
        ]
    }
}

# API: reassign
# -- request
data = {
    "msg_type": "request",
    "api": "inference/reassign/",
    "options": {
        "activity_id": <activity id>,
        "start_time": <time in epoch>,
        "end_time": <time in epoch>,
        "to_appliance": <selected appliance>,
        "to_location": <selected location>
    }
}

# -- response
data = {
    "msg_type": "response",
    "api": "inference/reassign/",
    "options": {
        "values": []
    }
}
'''
