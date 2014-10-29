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
from energylenserver.models.functions import retrieve_metadata, mark_not_active

from gcmxmppclient.messages import create_message, create_control_message
from gcmxmppclient.settings import *

from energylenserver.constants import *

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
            print "Authentication failed! Try again!"
            sys.exit(1)

    def connect_to_gcm_server(self):
        """
        Create a persistent XMPP connection to Google CCS Server
        """
        if self.client is None:
            print "Not connected"
            self.client = xmpp.Client(SERVER, debug=['socket'])
            self.client.connect(server=(SERVER, PORT), secure=1, use_srv=False)
            auth = self.client.auth(USERNAME, PASSWORD)
            if not auth:
                return False
        return True

    def get_connection_client(self):
        return self.client

    def set_connection_client(self, client):
        self.client = client

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
                print "NEED TO STOP SENDING MESSAGES"
                pass
        except Exception, e:
            print "[GCMCLIENT EXCEPTION] SendMessage:", e

    # Doesn't make sense -- alter
    def resend_queued_messages(self):
        """
        Send queued ACK/NACK messages to the device
        """

        while (self.unacked_messages_counter > 0 and
               self.unacked_messages_counter < self.unacked_messages_quota):
            print "Resend some unACKed messages..."
            self.send_message(self.sent_queue.pop()["message"])

    def receive_upstream_message(self, session, message):
        """
        Handles upstream message from the mobile device or
        control messages from the CCS
        """

        self.prev_req_time = time.time()
        try:
            now_time = "[" + time.ctime(time.time()) + "]"
            print now_time, "Received Upstream Message"
            gcm = message.getTags('gcm')
            if gcm:
                gcm_json = gcm[0].getData()
                msg = json.loads(gcm_json)

                # Indicates it is an upstream data message and accept from the EnergyLens app
                if 'message_type' not in msg and msg['category'] == 'com.example.energylens':
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
        except Exception, e:
            print "[GCMCLIENT EXCEPTION]: UpMessageHandler ::", e

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

        print "Handling request message.."
        print "Time elapsed from the start:", (time.time() - self.start_time)
        print "Time elapsed from the last request:", (time.time() - self.prev_req_time)

        # Get User Details
        user = determine_user(reg_id)
        if not user:
            return False
        apt_no = user.apt_no

        print "Determined user successfully!"

        if api == PERSONAL_ENERGY_API or api == ENERGY_WASTAGE_REPORT_API:
            # API: personal_energy
            start_time = options['start_time']
            end_time = options['end_time']

            # Get energy report
            options = get_energy_report(user.dev_id, api, start_time, end_time)
            data_to_send['options'] = options

            print "\nSending data for", api

        elif api == DISAGG_ENERGY_API:
            # API: disaggregated_energy
            start_time = options['start_time']
            end_time = options['end_time']
            activity_name = options['activity_name']

            activities = disaggregated_energy(user.dev_id, activity_name, start_time, end_time)
            # appliances = retrieve_metadata(apt_no)

            data_to_send['options']['activities'] = activities
            # data_to_send['options']['appliances'] = appliances

            print "\nSending diaggregated energy data.."

        # To be used only for testing purposes
        elif api == GROUND_TRUTH_NOTIF_API:
            # API: ground_truth api
            activities = get_inferred_activities(user.dev_id)
            appliances = retrieve_metadata(apt_no)

            data_to_send['options']['activities'] = activities
            data_to_send['options']['appliances'] = appliances

            print "\nSending ground truth report.."

        elif api == REASSIGN_INFERENCE_API:
            print "\nCorrecting inferences.."

            # Reassign the specified activity and update the db
            status = correct_inference(user, options)
            data_to_send['options'] = {'status': status}

            # print "Data to send:\n", json.dumps(data_to_send, indent=4)
            print "\nSending status for correction of inferences.."

        # May not use the following APIs
        elif api == ENERGY_COMPARISON_API:
            print "\nSending comparison energy data.."

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
        print "\nSending ACK back to user:"
        ack = create_control_message(message['from'], 'ack', message['message_id'])
        self.send_message(ack)

        # Determine message type - request or response
        data = message['data']
        if 'msg_type' in data:
            print "\nProcessing request/response from the user:\n", data
            msg_type = data['msg_type']
            # Request messages:
            if msg_type == "request":
                sent_status = self.handle_request_message(message)
                print "Message sent status:", sent_status
            elif msg_type == "response":
                self.handle_response_message(message)
        else:
            # Temp code: Echo back a response
            # Queue a response back to the server.
            if 'from' in message:
                # Send a dummy echo response back to the app that sent the upstream message.
                print "\nSending pong message back.."
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
        now_time = "[" + time.ctime(time.time()) + "]"
        print now_time, "Received ACK"
        print "MessageID:", msg_id
        # print "1 : Sent Queue:\n", json.dumps(self.sent_queue, indent=4)
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
            print "3 : Sent Queue:\n", json.dumps(self.sent_queue, indent=4)
            """

    def handle_nack(self, message):
        """
        Handles NACK messages and handles different types of errors
        TODO: Handle all the error JSON types e.g. REGISTRATION_INVALID, INVALID_JSON etc.
        """
        error = message['error']

        # Handle different error codes
        if error == "BAD_ACK":
            print "BAD_ACK"

        elif error == "BAD_REGISTRATION":
            print "BAD_REGISTRATION request received"
            # Mark the registration as "not active" in the database
            if mark_not_active(message["from"]):
                print "Successfully marked not active"
            else:
                print "Successfully marked active"

        elif error == "CONNECTION_DRAINING":
            print "CONNECTION_DRAINING"

        elif error == "DEVICE_UNREGISTERED":
            print "DEVICE_UNREGISTERED"

        elif error == "INTERNAL_SERVER_ERROR":
            print "INTERNAL_SERVER_ERROR"

        elif error == "INVALID_JSON":
            print "INVALID_JSON"

        elif error == "QUOTA_EXCEEDED":
            print "QUOTA_EXCEEDED"

        elif error == "SERVICE_UNAVAILABLE":
            # Start exponential backoff with an intial delay of 1 second
            print "SERVICE_UNAVAILABLE"

    def handle_control_message(self, message):
        # Connection about to close from the CCS
        if message['control_type'] == 'CONNECTION_DRAINING':
            # Open a new connection keeping the old connection open
            if not self.connect_to_gcm_server():
                print "Authentication failed! Try again!"
                sys.exit(1)
