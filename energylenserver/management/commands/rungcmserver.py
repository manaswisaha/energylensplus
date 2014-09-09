"""
Main XMPP CCS Client file

Usage: start the XMPP client on a different terminal along with
Django server running simultaneously

"""
import sys
from multiprocessing.managers import BaseManager

# Django imports
from django.core.management.base import BaseCommand


class ClientManager(BaseManager):
    pass


class Command(BaseCommand):
    help = "Maintains a persistent connection with Google's Server via XMPP"

    def handle(self, *args, **options):
        # Establishing connection with the running gcmserver
        print "Waiting for requests from the Google Server..."
        try:
            ClientManager.register('get_client')
            ClientManager.register('get_msg_client')
            manager = ClientManager(address=('localhost', 50000), authkey='abracadabra')
            manager.connect()
            client = manager.get_client()
            msg_client = manager.get_msg_client()

            while True:
                client.Process(1)
                # Restore connection if connection broken
                if not client.isConnected():
                    if not msg_client.connect_to_gcm_server():
                        self.stdout.write("Authentication failed! Try again!")
                        sys.exit(1)
        except KeyboardInterrupt:
            self.stdout.write("\n\nInterrupted by user, shutting down..")
            sys.exit(0)
        except Exception, e:
            self.stdout.write("[RunGCMServerException] %s" % str(e))
            sys.exit(1)
