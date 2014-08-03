#!/usr/bin/python
import sys
import json
import xmpp
import random
import string
from energylensplus import settings

SERVER = 'gcm.googleapis.com'
PORT = 5235
USERNAME = settings.GCM_SENDERID
PASSWORD = settings.GCM_APIKEY

# TODO: To retrieve from the DB
REGISTRATION_ID = "Registration Id of the target device"

unacked_messages_quota = 100
send_queue = []


def random_id():
    """
    Used for generating message ids
    Returns: a random alphanumerical id
    """

    rid = ''
    for x in range(8):
        rid += random.choice(string.ascii_letters + string.digits)
    return rid


def message_callback(session, message):
    """
    Handles upstream message from the mobile device
    """

    global unacked_messages_quota
    gcm = message.getTags('gcm')
    if gcm:
        gcm_json = gcm[0].getData()
        msg = json.loads(gcm_json)
        if not msg.has_key('message_type'):
            # Acknowledge the incoming message immediately.
            send({'to': msg['from'],
                  'message_type': 'ack',
                  'message_id': msg['message_id']})
            # Queue a response back to the server.
            if msg.has_key('from'):
                # Send a dummy echo response back to the app that sent the upstream message.
                send_queue.append({'to': msg['from'],
                                   'message_id': random_id(),
                                   'data': {'pong': 1}})
        elif msg['message_type'] == 'ack' or msg['message_type'] == 'nack':
            unacked_messages_quota += 1


def send(json_dict):
    """
    Send message to the target mobile device
    """
    template = ("<message><gcm xmlns='google:mobile:data'>{1}</gcm></message>")
    ccs_client.send(xmpp.protocol.Message(
        node=template.format(ccs_client.Bind.bound[0], json.dumps(json_dict))))


def flush_queued_messages():
    """
    Send queued ACK/NACK messages to the device
    """
    global unacked_messages_quota
    while len(send_queue) and unacked_messages_quota > 0:
        send(send_queue.pop(0))
        unacked_messages_quota -= 1

# Main process

# Create a permanent connection to Google CCS Server
ccs_client = xmpp.Client('gcm.googleapis.com', debug=['socket'])
ccs_client.connect(server=(SERVER, PORT), secure=1, use_srv=False)
auth = ccs_client.auth(USERNAME, PASSWORD)
if not auth:
    print 'Authentication failed!'
    sys.exit(1)

ccs_client.RegisterHandler('message', message_callback)

# Add message in the send queue
send_queue.append({'to': REGISTRATION_ID,
                   'message_id': 'reg_id',
                   'data': {'message_destination': 'RegId',
                            'message_id': random_id()}})

while True:
    ccs_client.Process(1)
    flush_queued_messages()
