"""
Main XMPP CCS Client file

Usage: start the XMPP client on a different terminal along with
Django server running simultaneously

"""
import sys
import threading
from multiprocessing.managers import BaseManager

# Django imports
from django.core.management.base import BaseCommand

from energylenserver.gcmxmppclient.msgclient import MessageClient
import logging

# Enable Logging
logger = logging.getLogger('energylensplus_gcm')


class ClientManager(BaseManager):
    pass


class Command(BaseCommand):
    help = "Opens a connection with Google's Server via XMPP"

    def handle(self, *args, **options):
        # Creates a message client that is connected to the Google server
        try:
            msg_client_obj = MessageClient()
            msg_client_obj.register_handlers()
            client = msg_client_obj.get_connection_client()

            ClientManager.register('get_client', callable=lambda: client)
            ClientManager.register('get_client_obj', callable=lambda: msg_client_obj)
            manager = ClientManager(address=('', 150000), authkey='abracadabra')
            server = manager.get_server()
            logger.debug("Got server")
            t = threading.Thread(target=lambda: server.serve_forever())
            t.start()
            logger.debug("Command Server started")
            msg_client_obj.start()

        except KeyboardInterrupt:
            logger.error("\n\nInterrupted by user, shutting down..")
            sys.exit(0)
        except Exception, e:
            logger.exception("[GCMServerException] %s" % str(e))
        finally:
            logger.debug("GCM Client Connection Closed")
            sys.exit(0)
