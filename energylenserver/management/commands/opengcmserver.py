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

    def run_server_forever(self, server, client, msg_client):
        '''
        Run the server forever
        '''
        # current_process()._manager_server = self
        try:
            try:
                while 1:
                    try:
                        c = server.listener.accept()
                    except (OSError, IOError):
                        continue
                    t = threading.Thread(target=server.handle_request, args=(c,))
                    t.daemon = True
                    t.start()
                    client.Process(1)
                    # Restore connection if connection broken
                    if not client.isConnected():
                        if not msg_client.connect_to_gcm_server():
                            logger.error("Authentication failed! Try again!")
                            sys.exit(1)
            except (KeyboardInterrupt, SystemExit):
                pass
        finally:
            server.stop = 999
            server.listener.close()


class Command(BaseCommand):
    help = "Opens a connection with Google's Server via XMPP"

    def handle(self, *args, **options):
        # Creates a message client that is connected to the Google server
        msg_client = MessageClient()
        msg_client.register_handlers()
        client = msg_client.get_connection_client()

        try:

            ClientManager.register('get_client', callable=lambda: client)
            ClientManager.register('get_msg_client', callable=lambda: msg_client)
            manager = ClientManager(address=('', 50000), authkey='abracadabra')
            server = manager.get_server()
            server.serve_forever()

            """
            try:
                # manager.run_server_forever(server, client, msg_client)
                self.stdout.write("--------------------------------------------")
                import time
                while True:
                    t1 = time.time()
                    self.stdout.write("Start time for while loop:: %s" % time.ctime(t1))
                    c = server.listener.accept()
                    t2 = time.time()
                    self.stdout.write("Time taken for listener.accept():: %d" % int(t2 - t1))
                    t = threading.Thread(target=server.handle_request, args=(c,))
                    t.daemon = True
                    t.start()
                    t2 = time.time()
                    self.stdout.write("Time taken from listener to t.start():: %d" % int(t2 - t1))

                    self.stdout.write("CCS Connection:: %s" % client.isConnected())
                    client.Process(1)
                    # Restore connection if connection broken
                    if not client.isConnected():
                        if not msg_client.connect_to_gcm_server():
                            self.stdout.write("Authentication failed! Try again!")
                            sys.exit(1)
                    t3 = time.time()
                    self.stdout.write("After Client Process():: %d" % int(t3 - t2))
                    self.stdout.write("End time for while loop:: %s" % time.ctime(t3))
                    self.stdout.write("Time taken for the while loop:: %d" % int(t3 - t1))
                    self.stdout.write("--------------------------------------------")
                except Exception, e:
                    self.stdout.write("[RunGCMServerException] %s" % str(e))
            """
        except KeyboardInterrupt:
            logger.error("\n\nInterrupted by user, shutting down..")
            sys.exit(0)
        except Exception, e:
            logger.error("[OpenGCMServerException] %s" % str(e))
