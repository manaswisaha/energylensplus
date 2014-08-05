
# Constants for sending response messages
ERROR_INVALID_REQUEST = {'type': 'ERROR', 'code': 0, 'message': 'Invalid request made'}

UPLOAD_SUCCESS = {'type': 'SUCCESS', 'code': 1, 'message': 'Data was successfully uploaded'}
UPLOAD_UNSUCCESSFUL = {'type': 'ERROR', 'code': 2, 'message': 'Data was not uploaded'}

REGISTRATION_SUCCESS = {'type': 'SUCCESS', 'code': 3, 'message': 'User was successfully registered'}
REGISTRATION_UNSUCCESSFUL = {'type': 'ERROR', 'code': 4, 'message': 'User was not registered'}
