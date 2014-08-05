from messages import create_message
from appserver import *

# global ccs_client
msg_client = CCSClient()
reg_id = 'APA91bF6i8F0Yo6afUcZXqIyEsaj1FEy98G2vZApj071sxVoTx6sYxGOElu8Z_uqCPamU7r7imSpeMhvyGbaXAg98k1scubjwaWIX7Tg277TEETGKMmLcxjll8Bf0E9T4sb1g_AzoILLqe7rR721Y5Kt3WzjyuSUgw'

msg_client.send_message(create_message(reg_id, {'test': 'msg'}))
