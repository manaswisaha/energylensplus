#!/usr/bin/python
"""
Runs the GCM App server
"""

from setup_django_envt import *

from gcmxmppclient.msgclient import MessageClient

# export DJANGO_SETTINGS_MODULE="energylensplus.settings"


if __name__ == '__main__':

    msg_client = MessageClient()  # Creates a message client that is connected to the Google server
    msg_client.register_handlers()
    client = msg_client.get_connection_client()

    try:
        while True:
            client.Process(1)
            # Restore connection if connection broken
            if not client.isConnected():
                if not msg_client.connect_to_gcm_server():
                    print "Authentication failed! Try again!"
                    sys.exit(1)
    except KeyboardInterrupt:
        print "\n\nInterrupted by user, shutting down.."
        sys.exit(0)
