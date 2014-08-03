
# Constants for sending response messages
# UPLOAD_SUCCESS = 'SUCCESS[0]: Data was successfully uploaded'
# UPLOAD_UNSUCCESSFUL = 'ERROR[0]: Data was not uploaded'
# ERROR_INVALID_REQUEST = 'ERROR[1]: Invalid request made'
UPLOAD_SUCCESS = {'type': 'SUCCESS', 'code': 0, 'message': 'Data was successfully uploaded'}
UPLOAD_UNSUCCESSFUL = {'type': 'ERROR', 'code': 1, 'message': 'Data was not uploaded'}
ERROR_INVALID_REQUEST = {'type': 'ERROR', 'code': 2, 'message': 'Invalid request made'}
