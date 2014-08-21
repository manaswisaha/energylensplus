import xmpp
from messages import create_message
from appserver import MessageClient, get_ccs_instance

# global ccs_client
# msg_client = CCSClient()
reg_id = 'APA91bF6i8F0Yo6afUcZXqIyEsaj1FEy98G2vZApj071sxVoTx6sYxGOElu8Z_uqCPamU7r7imSpeMhvyGbaXAg98k1scubjwaWIX7Tg277TEETGKMmLcxjll8Bf0E9T4sb1g_AzoILLqe7rR721Y5Kt3WzjyuSUgw'

# msg_client.send_message(create_message(reg_id, {'test': 'msg'}))

print "Hello\n"
c_client = get_ccs_instance()
print "CCLient", c_client
# print "State:", c_client.isConnected()
print "Sending message"
print "Type:", type(c_client)


message = create_message(reg_id, {'test1': 'msg1'})

template = ("<message><gcm xmlns='google:mobile:data'>{1}</gcm></message>")
c_client.send(xmpp.protocol.Message(
    node=template.format(c_client.Bind.bound[0], message)))
# c_client.send_message(create_message(reg_id, {'test1': 'msg1'}))
