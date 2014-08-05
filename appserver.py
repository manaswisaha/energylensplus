#!/usr/bin/python

"""
Main XMPP CCS Client file

Usage: start the XMPP client on a different terminal along with
Django server running simultaneously

"""
import sys
import json
import xmpp

from gcmxmppserver.messages import create_message
from gcmxmppserver.messages import create_control_message

from energylenserver.settings import GCM_APIKEY
from energylenserver.settings import GCM_SENDERID


# For testing
# SERVER = 'gcm-staging.googleapis.com'
# PORT = 5236
# For production
SERVER = 'gcm.googleapis.com'
PORT = 5235
USERNAME = GCM_SENDERID
PASSWORD = GCM_APIKEY
reg_id = 'APA91bF6i8F0Yo6afUcZXqIyEsaj1FEy98G2vZApj071sxVoTx6sYxGOElu8Z_uqCPamU7r7imSpeMhvyGbaXAg98k1scubjwaWIX7Tg277TEETGKMmLcxjll8Bf0E9T4sb1g_AzoILLqe7rR721Y5Kt3WzjyuSUgw'
reg_id = 'APA91bHviIi_udpOIMEm_cu2DtQE0lj4RtSYBVXc5t4UfHnbErnhkrus_W5JPI4GDpO91m6YPYznWAQGulBLFOryboLfT74hY9fUmAT3rPYs5Q5yuAtnaMoSo9znfzd9dF3uSAxOhkM2MGcvw5CpeWXHnonO370LOg'


"""
GCM Cloud Connection Server (XMPP)
"""
unacked_messages_quota = 100
unacked_messages_counter = 0

'''
format of the queue:
sent_queue = {
    '<msg_id>' : '<reg_id>',
    '<msg_id>' : '<reg_id>',...
}
'''
sent_queue = {}
sent_message_queue = {}

# ccs_client = None


class CCSClient:

    def register_handlers(self):
        ccs_client.RegisterHandler('message', self.receive_upstream_message)

    def send_message(self, message):
        """
        Send message to the target mobile device
        It maintains a queue of the sent messages and removes them
        when it receives ACK message from the server
        """
        global unacked_messages_counter

        # Send only if unACKed messages are less than the quota
        if unacked_messages_counter < unacked_messages_quota:
            # Send message
            template = ("<message><gcm xmlns='google:mobile:data'>{1}</gcm></message>")
            ccs_client.send(xmpp.protocol.Message(
                node=template.format(ccs_client.Bind.bound[0], message)))

            # Add in the sent queue
            msg_id = message['message_id']
            reg_id = message['to']
            sent_queue[msg_id] = reg_id
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
            pass

    def resend_queued_messages(self):
        """
        Send queued ACK/NACK messages to the device
        """
        global unacked_messages_quota
        global unacked_messages_counter

        while unacked_messages_counter > 0 and unacked_messages_counter < unacked_messages_quota:
            print "Resend some unACKed messages..."
            self.send_message(send_queue.pop(0))

    def handle_message(self, message):
        """
        Handles the upstream message
        """

        # Acknowledge the incoming message immediately.
        print "Sending ACK back to user:"
        ack = create_control_message(message['from'], 'ack', message['message_id'])
        self.send_message(ack)

        '''
        TODO:
        Create methods that receive different request types and
        handle them in this script

        e.g. if the request is for personal energy usage, then
        call the appropriate method from here. Basically, this file would be
        another views.py
        '''
        # Determine message type - request or response
        data = message['data']
        print data
        if 'msg_type' in data:
            msg_type = data['msg_type']
            # Request messages:
            if msg_type == "request":
                pass
            elif msg_type == "response":
                pass

        # Temp code: Echo back a response
        # Queue a response back to the server.
        if 'from' in message:
            # Send a dummy echo response back to the app that sent the upstream message.
            print "Sending pong message back.."
            message = create_message(message['from'], {'pong': 1})
            self.send_message(message)

    def handle_ack(self, message):
        """
        Handles ACK messages and resends some of the unACKed messages
        """
        global unacked_messages_counter
        # Delete the ACKed message from the queue
        msg_id = message['message_id']
        reg_id = message['from']
        if msg_id in sent_queue and sent_queue[msg_id] == reg_id:

            # Remove message from the unACKed message queue
            del sent_queue[msg_id]
            len_queue = len(sent_queue)
            unacked_messages_counter = len_queue

            # Check if there are any messages to resend
            if len_queue > 0:
                # Resend some messages in the queue
                self.resend_queued_messages()

    def handle_nack(self, message):
        """
        Handles NACK messages and handles the different types of errors
        TODO: Handle all the error JSON types e.g. REGISTRATION_INVALID, INVLAID_JSON etc.
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
            # TODO: Open another connection
            pass

    def receive_upstream_message(self, session, message):
        """
        Handles upstream message from the mobile device or
        control messages from the CCS
        """

        print "Received Upstream Message.."
        global unacked_messages_quota
        global unacked_messages_counter
        gcm = message.getTags('gcm')
        if gcm:
            gcm_json = gcm[0].getData()
            msg = json.loads(gcm_json)

            # Accept messages only from the EnergyLens app
            if msg['category'] == 'com.example.energylens':
                # Indicates it is an upstream message
                if 'message_type' not in msg:
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


def check_connection():
        pass


def connect_to_gcm_server():
    """
    Create a permanent connection to Google CCS Server
    """
    ccs_client.connect(server=(SERVER, PORT), secure=1, use_srv=False)
    auth = ccs_client.auth(USERNAME, PASSWORD)
    # Authentication failed!
    if not auth:
        return False
    return True


if __name__ == '__main__':
    global ccs_client

    ccs_client = xmpp.Client(SERVER, debug=['socket'])
    if not connect_to_gcm_server():
        print "Authentication failed! Try again!"
        sys.exit(1)

    msg_client = CCSClient()
    msg_client.register_handlers()
    sent = False

    while True:
        ccs_client.Process(1)
        # if not sent:
        #     msg_client.send_message(create_message(reg_id, {'test': 'msg'}))
        # Increase the counter for unacked messages
        #     sent = True
