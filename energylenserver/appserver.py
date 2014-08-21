#!/usr/bin/python

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
import random as rnd
import numpy as np
from numpy import random

from gcmxmppclient.messages import create_message
from gcmxmppclient.messages import create_control_message

from gcmxmppclient.settings import GCM_APIKEY
from gcmxmppclient.settings import GCM_SENDERID

from constants import *

# PERSONAL_ENERGY_API = "energy/personal/"
# DISAGG_ENERGY_API = "energy/disaggregated/"
# REAL_TIME_POWER_API = "power/real-time/"
# ENERGY_COMPARISON_API = "energy/comparison/"
# ENERGY_WASTAGE_API = "energy/wastage/"
# ENERGY_REPORT_API = "energy/report/"


# For testing
# SERVER = 'gcm-staging.googleapis.com'
# PORT = 5236
# For production
SERVER = 'gcm.googleapis.com'
PORT = 5235
USERNAME = GCM_SENDERID
PASSWORD = GCM_APIKEY

# Vedant's phone
reg_id = 'APA91bHviIi_udpOIMEm_cu2DtQE0lj4RtSYBVXc5t4UfHnbErnhkrus_W5JPI4GDpO91m6YPYznWAQGulBLFOryboLfT74hY9fUmAT3rPYs5Q5yuAtnaMoSo9znfzd9dF3uSAxOhkM2MGcvw5CpeWXHnonO370LOg'
# MotoG
reg_id = 'APA91bF6i8F0Yo6afUcZXqIyEsaj1FEy98G2vZApj071sxVoTx6sYxGOElu8Z_uqCPamU7r7imSpeMhvyGbaXAg98k1scubjwaWIX7Tg277TEETGKMmLcxjll8Bf0E9T4sb1g_AzoILLqe7rR721Y5Kt3WzjyuSUgw'

# Helper functions


def constrained_sum_sample_pos(n, total):
    """Return a randomly chosen list of n positive integers summing to total.
    Each such list is equally likely to occur."""

    dividers = sorted(rnd.sample(xrange(1, total), n - 1))
    return [a - b for a, b in zip(dividers + [total], [0] + dividers)]


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
            print "[GCMCLIENT EXCEPTION]:", e

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
        data = message['data']
        api = data['api']

        if 'options' not in data:
            return False
        options = ast.literal_eval(data['options'])

        data_to_send = {}
        data_to_send['msg_type'] = "response"
        data_to_send['api'] = api
        data_to_send['options'] = {}

        if api == PERSONAL_ENERGY_API:
            # API: personal_energy
            end_time = options['end_time']
            no_of_hours = 12
            if "last" in end_time:
                end_time_str = end_time.split(" ")
                if end_time_str[2] == "hours":
                    no_of_hours = int(end_time_str[1])
                    print "Number of hours:", no_of_hours

            # Replace the following with the call to the appropriate API
            # temp code
            # usage_list = [1000, 1030, 1100, 4500, 2300, 5500, 3200, 2100, 5500, 6000, 3000, 7800]
            usage_list = random.randint(1000, size=no_of_hours)
            print "Energy Usage", usage_list

            total_usage = sum(usage_list)
            perc_list = constrained_sum_sample_pos(4, 100)
            perc_list.sort()

            data_to_send['options']['total_consumption'] = total_usage
            data_to_send['options']['hourly_consumption'] = usage_list.tolist()

            data_to_send['options']['activities'] = []
            data_to_send['options']['activities'].append(
                {'name': "TV", "usage": total_usage * perc_list[1] / 100.})
            data_to_send['options']['activities'].append(
                {'name': "AC", "usage": total_usage * perc_list[2] / 100.})
            data_to_send['options']['activities'].append(
                {'name': "Microwave", "usage": total_usage * perc_list[3] / 100.})
            data_to_send['options']['activities'].append(
                {'name': "Unknown", "usage": total_usage * perc_list[0] / 100.})

            print "Data to send:\n", json.dumps(data_to_send)
            print "\nSending personal energy data.."

        elif api == DISAGG_ENERGY_API:
            # API: disaggregated_energy
            end_time = options['end_time']
            activity_name = options['activity_name']
            no_of_hours = 12
            if "last" in end_time:
                end_time_str = end_time.split(" ")
                if end_time_str[2] == "hours":
                    no_of_hours = int(end_time_str[1])
                    print "Number of hours:", no_of_hours
            # Replace the following with the call to the appropriate API
            # temp code

            activities = []
            activities.append(
                {'id': 1, 'name': activity_name, 'location': 'Dining Room', "usage": 320,
                 "start_time": 1408093265, "end_time": 1408095726})
            activities.append(
                {'id': 2, 'name': activity_name, 'location': 'Dining Room', "usage": 320,
                 "start_time": 1408096865, "end_time": 1408111265})
            activities.append(
                {'id': 3, 'name': activity_name, 'location': 'Bedroom', "usage": 80,
                 "start_time": 1408165265, "end_time": 1408168865})
            activities.append(
                {'id': 4, 'name': activity_name, 'location': 'Bedroom', "usage": 120,
                 "start_time": 1408179665, "end_time": 1408185065})

            data_to_send['options']['activities'] = activities

            print "Data to send:\n", json.dumps(data_to_send)
            print "\nSending diaggregated energy data.."

        elif api == REAL_TIME_POWER_API:
            print "\nSending real-time power data.."

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
        print "1 : Sent Queue:\n", json.dumps(sent_queue, indent=4)
        if msg_id in sent_queue and sent_queue[msg_id]["reg_id"] == reg_id:

            # Remove message from the unACKed message queue
            del sent_queue[msg_id]
            len_queue = len(sent_queue)
            unacked_messages_counter = len_queue

            print "2 : Sent Queue:\n", json.dumps(sent_queue, indent=4)

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
