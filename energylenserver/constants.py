
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

# API Names
PERSONAL_ENERGY_API = "energy/personal/"
DISAGG_ENERGY_API = "energy/disaggregated/"

TRAINING_API = "data/training/"
REAL_TIME_POWER_API = "power/real-time/"

ENERGY_COMPARISON_API = "energy/comparison/"
ENERGY_WASTAGE_API = "energy/wastage/"
ENERGY_REPORT_API = "energy/report/"


# Edge Transition Window (in seconds)
# for the change to take place
# its more for simultaneous or quick sequential activity
lwinmin = 3
pwinmin = 3
# lwinmin = pwinmin

# Power Threshold (in Watts) for the magnitude of the change
lthresmin = 10   # for light meter
pthresmin = 15  # for power meter
# pthresmin = lthresmin

# Power Percent Change between rising and falling edge
percent_change = 0.31

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
    }
}

# API: realtime_power
# -- request
data = {
    "msg_type": "request",
    "api": "power/real-time/",
    "options": {}
}

# -- response
data = {
    "msg_type": "response",
    "api": "power/real-time/",
    "options": {
        "values": []
    }
}
'''
