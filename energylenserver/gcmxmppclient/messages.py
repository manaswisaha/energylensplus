import json
import random
import string
"""
Message Handling Functions
"""


def random_id():
    """
    Used for generating message ids
    Returns: a random alphanumerical id
    """

    rid = ''
    for x in range(8):
        rid += random.choice(string.ascii_letters + string.digits)
    return rid


def create_message(reg_id, data):
    """
    Creates a JSON message body for an XMPP message
    """
    message = json.dumps({'to': reg_id,
                          'message_id': random_id(),
                          'data': data,
                          'time_to_live': 3600,
                          'delay_while_idle': False})
    # print "Message created::\n", json.dumps(message, indent=4)
    return message


def create_control_message(reg_id, msg_type, msg_id):
    """
    Creates a JSON message body for an ack/nack/control message
    """
    message = json.dumps({'to': reg_id,
                          'message_type': msg_type,
                          'message_id': msg_id})
    # print "Control Message created::", message
    return message
