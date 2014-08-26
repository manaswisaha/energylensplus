#!/usr/bin/python
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
import sys
import ast
import time
import json
import xmpp

sys.path.insert(1, '/home/manaswi/EnergyLensPlusCode/energylensplus')
# print "SYSPATH", sys.path

import os
os.environ['DJANGO_SETTINGS_MODULE'] = "energylensplus.settings"

# import django
# django.setup()

from api.reporting import *
from api.reassign import *
from models.functions import retrieve_metadata

from gcmxmppclient.messages import create_message
from gcmxmppclient.messages import create_control_message

from gcmxmppclient.settings import GCM_APIKEY
from gcmxmppclient.settings import GCM_SENDERID

from constants import *

# export DJANGO_SETTINGS_MODULE="energylensplus.settings"


# For testing
# SERVER = 'gcm-staging.googleapis.com'
# PORT = 5236

# For production
SERVER = 'gcm.googleapis.com'
PORT = 5235
USERNAME = GCM_SENDERID
PASSWORD = GCM_APIKEY


"""
GCM Cloud Connection Server (XMPP)
"""
unacked_messages_quota = 100
unacked_messages_counter = 0

"""
Maintain a queue of all the unACKed sent messages
Format of the queue:
sent_queue = {
    "<msg_id>" : { "reg_id": "<reg_id>",
                   "message": "<message>"},...
}
"""
sent_queue = {}
# ccs_client = None
pong = 0


class MessageClient:

    def __init__(self):
        self.client = ccs_client

    def register_handlers(self):
        # Handles messages from CCS/Device
        self.client.RegisterHandler('message', self.receive_upstream_message)
        # TODO: add handler for EnergyLens App Server
        # self.client.RegisterHandler('message', self.receive_server_message)

    def send_message(self, message):
        """
        Send message to the target mobile device
        It maintains a queue of the sent messages and removes them
        when it receives ACK message from the server
        """
        global unacked_messages_counter

        try:
            # Send only if unACKed messages are less than the quota
            if unacked_messages_counter < unacked_messages_quota:
                # Send message
                template = ("<message><gcm xmlns='google:mobile:data'>{1}</gcm></message>")
                self.client.send(xmpp.protocol.Message(
                    node=template.format(self.client.Bind.bound[0], message)))

                # Add in the sent queue only if it is a data message
                message = json.loads(message)
                if 'message_type' not in message:
                    msg_id = message['message_id']
                    reg_id = message['to']
                    sent_queue[msg_id] = {}
                    sent_queue[msg_id]["reg_id"] = reg_id
                    sent_queue[msg_id]["message"] = message
                    len_queue = len(sent_queue)
                    unacked_messages_counter = len_queue
            else:
                '''
                TODO:
                Handle the exponential backoff based on the ACK/NACK messages received
                or not received. Fix the 'unacked_messages_quota' variable usage. Maybe make
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
        global unacked_messages_quota
        global unacked_messages_counter

        while unacked_messages_counter > 0 and unacked_messages_counter < unacked_messages_quota:
            print "Resend some unACKed messages..."
            self.send_message(sent_queue.pop()["message"])

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

        # Get User Details
        user = determine_user(reg_id)
        if not user:
            return False
        apt_no = user.apt_no

        if api == PERSONAL_ENERGY_API or api == ENERGY_WASTAGE_API:
            # API: personal_energy
            start_time = options['start_time']
            end_time = options['end_time']

            # Get energy report
            options = get_energy_report(reg_id, api, start_time, end_time)
            data_to_send['options'] = options

            print "\nSending data for", api

        elif api == DISAGG_ENERGY_API:
            # API: disaggregated_energy
            start_time = options['start_time']
            end_time = options['end_time']
            activity_name = options['activity_name']

            activities = disaggregated_energy(reg_id, activity_name, start_time, end_time)
            appliances = retrieve_metadata(apt_no)

            data_to_send['options']['activities'] = activities
            data_to_send['options']['appliances'] = appliances

            print "\nSending diaggregated energy data.."

        elif api == REASSIGN_INFERENCE_API:
            print "\nCorrecting inferences.."

            # Reassign the specified activity and update the db
            status = correct_inference(reg_id, options)
            data_to_send['options'] = {'status': status}

            # print "Data to send:\n", json.dumps(data_to_send, indent=4)
            print "\nSending diaggregated energy data.."

        # May not use the following APIs
        elif api == ENERGY_COMPARISON_API:
            print "\nSending comparison energy data.."

        elif api == ENERGY_WASTAGE_API:
            print "\nSending energy wastage data.."

        elif api == ENERGY_REPORT_API:
            print "\nSending energy report.."

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

        global pong
        pong += 1

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
                message = create_message(message['from'], {'pong': pong, 'ping': 100})
                self.send_message(message)

    def handle_ack(self, message):
        """
        Handles received ACK messages and resends some of the unACKed messages
        such that it does not cross the quota of 100 unacked messages
        """
        global unacked_messages_counter
        # Delete the ACKed message from the queue
        msg_id = message['message_id']
        reg_id = message['from']
        now_time = "[" + time.ctime(time.time()) + "]"
        print now_time, "Received ACK"
        print "MessageID:", msg_id
        # print "1 : Sent Queue:\n", json.dumps(sent_queue, indent=4)
        if msg_id in sent_queue and sent_queue[msg_id]["reg_id"] == reg_id:

            # Remove message from the unACKed message queue
            del sent_queue[msg_id]
            len_queue = len(sent_queue)
            unacked_messages_counter = len_queue

            """
            # Check if there are any messages to resend
            if len_queue > 0:
                # Resend some messages in the queue
                self.resend_queued_messages()
            print "3 : Sent Queue:\n", json.dumps(sent_queue, indent=4)
            """

    def handle_nack(self, message):
        """
        Handles NACK messages and handles different types of errors
        TODO: Handle all the error JSON types e.g. REGISTRATION_INVALID, INVALID_JSON etc.
        """
        error = message['error']

        # Handle different error codes
        if error is "BAD_ACK":
            print "BAD_ACK"

        elif error is "BAD_REGISTRATION":
            print "BAD_REGISTRATION"

        elif error is "CONNECTION_DRAINING":
            print "CONNECTION_DRAINING"

        elif error is "DEVICE_UNREGISTERED":
            print "DEVICE_UNREGISTERED"

        elif error is "INTERNAL_SERVER_ERROR":
            print "INTERNAL_SERVER_ERROR"

        elif error is "INVALID_JSON":
            print "INVALID_JSON"

        elif error is "QUOTA_EXCEEDED":
            print "QUOTA_EXCEEDED"

        elif error is "SERVICE_UNAVAILABLE":
            # Start exponential backoff with an intial delay of 1 second
            print "SERVICE_UNAVAILABLE"

    def handle_control_message(self, message):
        # Connection about to close from the CCS
        if message['control_type'] == "CONNECTION_DRAINING":
            # Open a new connection keeping the old connection open
            # TODO: Spawn a new python process of the appserver
            pass

    def receive_upstream_message(self, session, message):
        """
        Handles upstream message from the mobile device or
        control messages from the CCS
        """

        try:

            now_time = "[" + time.ctime(time.time()) + "]"
            print now_time, "Received Upstream Message"
            global unacked_messages_quota
            global unacked_messages_counter
            gcm = message.getTags('gcm')
            if gcm:
                gcm_json = gcm[0].getData()
                msg = json.loads(gcm_json)

                # Indicates it is an upstream data message and accept from the EnergyLens app
                if 'message_type' not in msg and msg['category'] == 'com.example.energylens':
                    self.handle_message(msg)

                # Indicates it is an ACK message
                elif msg['message_type'] == 'ack':
                    self.handle_ack(msg)

                # Indicates it is an NACK message
                elif msg['message_type'] == 'nack':
                    self.handle_nack(msg)

                # Indicates it is a control message
                elif msg['message_type'] == "control":
                    self.handle_control_message(msg)
        except Exception, e:
            print "[GCMCLIENT EXCEPTION]: UpMessageHandler ::", e


def connect_to_gcm_server():
    """
    Create a persistent XMPP connection to Google CCS Server
    """
    ccs_client.connect(server=(SERVER, PORT), secure=1, use_srv=False)
    auth = ccs_client.auth(USERNAME, PASSWORD)
    # Authentication failed!
    if not auth:
        return False
    return True

if __name__ == '__main__':

    ccs_client = xmpp.Client(SERVER, debug=['socket'])
    if not connect_to_gcm_server():
        print "Authentication failed! Try again!"
        sys.exit(1)

    msg_client = MessageClient()
    msg_client.register_handlers()
    sent = False

    while True:
        ccs_client.Process(1)
        # if not sent:
        #     msg_client.send_message(create_message(reg_id, {'test': 'msg2'}))
        # Increase the counter for unacked messages
        #     sent = True
