"""
TODO:
1. Implement exponential backoff for retries
2. Implement rest of the code (handling errors, exception etc.)
    to completely implement CCS
"""

"""
Main XMPP CCS Client file

Usage: start the XMPP client on a different terminal along with
Django server running simultaneously

"""

import ast
import time
import json
import xmpp

from energylenserver.setup_django_envt import *

# EnergyLens+ imports
from energylenserver.api.reporting import *
from energylenserver.api.reassign import *
from energylenserver.models import functions as mod_func

from gcmxmppclient.messages import create_message, create_control_message
from gcmxmppclient.settings import *

from energylenserver.common_imports import *

# Enable Logging
logger = logging.getLogger('energylensplus_gcm')
exception_logger = logging.getLogger('energylensplus_error')


"""
Main XMPP Message Client
"""


class MessageClient:
    client = None

    def __init__(self):
        self.pong = 0
        self.unacked_messages_quota = 100
        self.unacked_messages_counter = 0
        self.start_time = time.time()
        self.prev_req_time = None
        self.backoff = 1
        self.backoff_msg = 2
        self.logger = logger
        self.elogger = exception_logger

        """
        Maintain a queue of all the unACKed sent messages
        Format of the queue:
        sent_queue = {
            "<msg_id>" : { "reg_id": "<reg_id>",
                           "message": "<message>"},...
        }
        """
        self.sent_queue = {}

        # Connect to Google server
        if not self.connect_to_gcm_server():
            logger.error("Authentication failed! Try again!")
            sys.exit(1)

    def connect_to_gcm_server(self):
        """
        Create a persistent XMPP connection to Google CCS Server
        """
        if self.client is None or not self.client.isConnected():
            logger.debug("Not connected")
            self.client = xmpp.Client(SERVER, debug=['socket'])
            self.client.connect(server=(SERVER, PORT), secure=1, use_srv=False)
            auth = self.client.auth(USERNAME, PASSWORD)
            if not auth:
                return False
        return True

    def start(self):
        """
        Establishes connection and runs the infinite loop
        """
        logger.debug("Starting GCM Server..")
        while True:
            try:
                self.client.Process(1)
                # Restore connection if connection broken
                if not self.client.isConnected():
                    logger.debug("Reconnecting..")
                    if not self.connect_to_gcm_server():
                        self.logger.error("Authentication failed! Try again!")
                        sys.exit(1)
                    else:
                        logger.debug("Reconnected Successfully!")
                        self.register_handlers()
                        continue

            except Exception, e:
                self.elogger.exception("[GCMConnClient EXCEPTION]: Start() ::%s", e)

    def get_connection_client(self):
        return self.client

    def register_handlers(self):
        """
        Handles messages from CCS/Device
        """
        self.client.RegisterHandler('message', self.receive_upstream_message)

    def send_message(self, message):
        """
        Send message to the target mobile device
        It maintains a queue of the sent messages and removes them
        when it receives ACK message from the server
        """
        try:
            # Send only if unACKed messages are less than the quota
            if self.unacked_messages_counter < self.unacked_messages_quota:

                # Send message
                template = ("<message><gcm xmlns='google:mobile:data'>{1}</gcm></message>")
                self.client.send(xmpp.protocol.Message(
                    node=template.format(self.client.Bind.bound[0], message)))

                # Add in the sent queue only if it is a data message
                message = json.loads(message)
                if 'message_type' not in message:
                    msg_id = message['message_id']
                    reg_id = message['to']
                    self.sent_queue[msg_id] = {}
                    self.sent_queue[msg_id]["reg_id"] = reg_id
                    self.sent_queue[msg_id]["message"] = message
                    len_queue = len(self.sent_queue)
                    self.unacked_messages_counter = len_queue
            else:
                '''
                TODO:
                Handle the exponential backoff based on the ACK/NACK messages received
                or not received. Fix the 'self.unacked_messages_quota' variable usage. Maybe make
                a class, list etc. or something.
                '''
                # Introduce a delay using exponential backoff
                self.logger.warn("NEED TO STOP SENDING MESSAGES")
                self.logger.error('Waiting %s seconds before trying again' % self.backoff_msg)
                time.sleep(self.backoff_msg)
                self.backoff_msg = min(self.backoff_msg * 2, 320)

                self.send_message(self, message)
        except Exception, e:
            self.logger.error("[GCMCLIENT EXCEPTION] SendMessage:%s", e)

    # Doesn't make sense -- alter
    def resend_queued_messages(self):
        """
        Send queued ACK/NACK messages to the device
        """

        while (self.unacked_messages_counter > 0 and
               self.unacked_messages_counter < self.unacked_messages_quota):
            self.logger.debug("Resend some unACKed messages...")
            self.send_message(self.sent_queue.pop()["message"])

    def receive_upstream_message(self, session, message):
        """
        Handles upstream message from the mobile device or
        control messages from the CCS
        """

        try:
            self.logger.debug("Received Upstream Message")
            gcm = message.getTags('gcm')
            if gcm:
                gcm_json = gcm[0].getData()
                msg = json.loads(gcm_json)

                # Indicates it is an upstream data message and accept from the EnergyLens app
                if 'message_type' not in msg and msg['category'] in ['com.example.energylens',
                                                                     'com.iiitd.muc.energylens']:
                    self.handle_message(msg)

                # Indicates it is an ACK message
                elif msg['message_type'] == "ack":
                    self.handle_ack(msg)

                # Indicates it is an NACK message
                elif msg['message_type'] == "nack":
                    self.handle_nack(msg)

                # Indicates it is a control message
                elif msg['message_type'] == "control":
                    self.handle_control_message(msg)

            self.prev_req_time = time.time()

        except Exception, e:
            self.logger.error("[GCMCLIENT EXCEPTION]: UpMessageHandler ::%s", e)
            self.elogger.exception("[GCMCLIENT EXCEPTION]: UpMessageHandler ::%s", e)

    def handle_request_message(self, message):

        reg_id = message['from']
        data = message['data']
        api = data['api']

        if 'options' not in data:
            return False
        options = ast.literal_eval(data['options'])

        data_to_send = {}
        data_to_send['msg_type'] = "response"
        data_to_send['api'] = api
        data_to_send['options'] = {}

        # ---------- DEBUGGING CODE------------------
        self.logger.debug("Handling request message..")

        t_elap_start = (time.time() - self.start_time)
        if t_elap_start >= 3600:
            t_elap_start /= 3600
            t_elap_start = str(t_elap_start) + " hours"
        elif t_elap_start >= 60:
            t_elap_start /= 60
            t_elap_start = str(t_elap_start) + " minutes"
        self.logger.debug("Time elapsed from the start: %s", t_elap_start)

        if self.prev_req_time is not None:
            t_elap_prev = (time.time() - self.prev_req_time)
            if t_elap_prev >= 3600:
                t_elap_prev /= 3600
                t_elap_prev = str(t_elap_prev) + " hours"
            elif t_elap_prev >= 60:
                t_elap_prev /= 60
                t_elap_prev = str(t_elap_prev) + " minutes"
            self.logger.debug("Time elapsed from the last request: %s", t_elap_prev)
        else:
            self.logger.debug("First request")
        # ---------- DEBUGGING CODE------------------

        # Get User Details
        user = mod_func.determine_user(reg_id)
        if not user:
            return False
        apt_no = user.apt_no

        self.logger.debug("User: %s", user.name)

        if api == PERSONAL_ENERGY_API or api == ENERGY_WASTAGE_REPORT_API:
            # API: personal_energy
            start_time = options['start_time']
            end_time = options['end_time']

            # Get energy report
            options = get_energy_report(user, api, start_time, end_time)
            data_to_send['options'] = options

            self.logger.debug("Sending data for:  %s", api)

        elif api == DISAGG_ENERGY_API:
            # API: disaggregated_energy
            start_time = options['start_time']
            end_time = options['end_time']
            activity_name = options['activity_name']

            activities = disaggregated_energy(user, activity_name, start_time, end_time)
            # appliances = mod_func.retrieve_metadata(apt_no)

            data_to_send['options']['activities'] = activities
            # data_to_send['options']['appliances'] = appliances

            self.logger.debug("Sending diaggregated energy data..")

        # To be used only for testing purposes
        elif api == GROUND_TRUTH_NOTIF_API:
            # API: ground_truth api
            activities = get_inferred_activities(user)
            appliances = mod_func.retrieve_metadata(apt_no)

            data_to_send['options']['activities'] = activities
            data_to_send['options']['appliances'] = appliances

            self.logger.debug("Sending ground truth report..")

        elif api == REASSIGN_INFERENCE_API:
            self.logger.debug("Correcting inferences..")

            # Reassign the specified activity and update the db
            status = correct_inference(user, options)
            data_to_send['options'] = {'status': status}

            # self.logger.debug ("Data to send:\n", json.dumps(data_to_send, indent=4))
            self.logger.debug("Sending status for correction of inferences..")

        # May not use the following APIs
        elif api == ENERGY_COMPARISON_API:
            self.logger.debug("Sending comparison energy data..")

        # Send a response back based on the api request
        if 'from' in message:
            message = create_message(message['from'], data_to_send)
            self.send_message(message)
        return True

    def handle_response_message(self, message):
        pass

    def handle_message(self, message):
        """
        Handles the upstream message
        """

        self.pong += 1

        # Acknowledge the incoming message immediately.
        self.logger.debug("Sending ACK back to user..")
        ack = create_control_message(message['from'], 'ack', message['message_id'])
        self.send_message(ack)

        # Determine message type - request or response
        data = message['data']
        if 'msg_type' in data:
            self.logger.debug("Processing request/response for api: %s", data['api'])
            msg_type = data['msg_type']
            # Request messages:
            if msg_type == "request":
                sent_status = self.handle_request_message(message)
                self.logger.debug("Message sent status:%s\n", sent_status)
            elif msg_type == "response":
                self.handle_response_message(message)
        else:
            # Temp code: Echo back a response
            # Queue a response back to the server.
            if 'from' in message:
                # Send a dummy echo response back to the app that sent the upstream message.
                self.logger.debug("Sending pong message back..")
                message = create_message(message['from'], {'pong': self.pong, 'ping': 100})
                self.send_message(message)

    def handle_ack(self, message):
        """
        Handles received ACK messages and resends some of the unACKed messages
        such that it does not cross the quota of 100 unacked messages
        """
        # Delete the ACKed message from the queue
        msg_id = message['message_id']
        reg_id = message['from']
        self.logger.debug("Received ACK")
        self.logger.debug("MessageID:%s\n", msg_id)
        # self.logger.debug ("1 : Sent Queue:\n", json.dumps(self.sent_queue, indent=4))
        if msg_id in self.sent_queue and self.sent_queue[msg_id]["reg_id"] == reg_id:

            # Remove message from the unACKed message queue
            del self.sent_queue[msg_id]
            len_queue = len(self.sent_queue)
            self.unacked_messages_counter = len_queue

            """
            # Check if there are any messages to resend
            if len_queue > 0:
                # Resend some messages in the queue
                self.resend_queued_messages()
            self.logger.debug ("3 : Sent Queue:\n", json.dumps(self.sent_queue, indent=4))
            """

    def handle_nack(self, message):
        """
        Handles NACK messages and handles different types of errors
        TODO: Handle all the error JSON types e.g. REGISTRATION_INVALID, INVALID_JSON etc.
        """
        error = message['error']

        # Handle different error codes
        if error == "BAD_ACK":
            self.logger.error("BAD_ACK")

        elif error == "BAD_REGISTRATION":
            self.logger.error("BAD_REGISTRATION request received")
            # Mark the registration as "not active" in the database
            if mod_func.mark_not_active(message["from"]):
                self.logger.debug("Successfully marked not active")
            else:
                self.logger.debug("Successfully marked active")

        elif error == "CONNECTION_DRAINING":
            self.logger.error("CONNECTION_DRAINING")

        elif error == "DEVICE_UNREGISTERED":
            self.logger.error("DEVICE_UNREGISTERED")
            # Mark the registration as "not active" in the database
            if mod_func.mark_not_active(message["from"]):
                self.logger.debug("Successfully marked not active")
            else:
                self.logger.debug("Successfully marked active")

        elif error == "INTERNAL_SERVER_ERROR":
            self.logger.error("INTERNAL_SERVER_ERROR")

        elif error == "INVALID_JSON":
            self.logger.error("INVALID_JSON")

        elif error == "DEVICE_MESSAGE_RATE_EXCEEDED":
            self.logger.error("DEVICE_MESSAGE_RATE_EXCEEDED")

        elif error == "SERVICE_UNAVAILABLE":
            # Start exponential backoff with an intial delay of 1 second
            self.logger.error("SERVICE_UNAVAILABLE")
            self.logger.error('Waiting %s seconds before trying again' % self.backoff)
            time.sleep(self.backoff)
            self.backoff = min(self.backoff * 2, 320)

    def handle_control_message(self, message):
        # Connection about to close from the CCS
        if message['control_type'] == 'CONNECTION_DRAINING':
            # Open a new connection keeping the old connection open
            if not self.connect_to_gcm_server():
                self.logger.debug("Authentication failed! Try again!")
                sys.exit(1)
