import os
import ast
import base64
from datetime import datetime
import pytz

import google.cloud.logging as logging
from fastapi.responses import JSONResponse
from fastapi import status
from src.request_body import SubRequest
import src.notify.notify as notify
import src.action.action as action
import src.config as config

def action_handler(request: SubRequest) -> JSONResponse:
    message = request.message
    if "data" not in message:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "no data in message received"},
        )
    content = base64.b64decode(message["data"]).decode("utf-8")
    content = ast.literal_eval(content)
    if action.execute(content)==False:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "action handler error when action.execute()"},
        )
    
    return JSONResponse(
        status_code = status.HTTP_200_OK,
        content = {"message": "success"}
    )
    
def notify_handler(request: SubRequest) -> JSONResponse:
    message = request.message
    if "data" not in message:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "no data in message received"},
        )
    content = base64.b64decode(message["data"]).decode("utf-8")
    content = ast.literal_eval(content)

    action = content.get('action', None)
    if not action:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "parameter error: action missing"},
        )
    if ('add' and 'remove') not in action:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "data content with error"},
        )
    result = notify.execute(content)
    if result==False:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "notify handler error when notify.execute()"},
        )
    
    return JSONResponse(
        status_code = status.HTTP_200_OK,
        content = {"message": "success"}
    )

def userlog_handler(request: SubRequest) -> JSONResponse:
    message = request.message
    if "data" not in message:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "no data in message received"},
        )
    content = base64.b64decode(message["data"]).decode("utf-8")
    print('userlog content: ', content)
    content = ast.literal_eval(content)

    now = datetime.now(pytz.timezone(config.TIME_ZONE)).strftime("%Y.%m.%d %H:%M:%S")
    action = content.get('action', None)
    if not action:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "parameter error: action missing"},
        )

    memberId = content.get('memberId', 0)
    if memberId == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "parameter error: memberId missing"},
        )

    objId = (
    content.get('targetId', '') or \
    content.get('commentId', '') or \
    content.get('storyId', '') or \
    content.get('collectionId', '')
    )
    objective = content.get('objective', '')
    uuid = content.get('UUID', '')
    clientOS = content.get('os', '')
    version = content.get('version', '')
    device = content.get('device', '')

    ### writing log
    project_id = os.environ['project_id']
    log_name = os.environ['log_name']
    logger_name = f'projects/{project_id}/logs/{log_name}'
    resource = logging.Resource(type='global', labels={'project_id': project_id})
    clientInfo = {
    'client-info':
        {
        'current-runtime-start': now,
        'datetime': now,
        'exit-time': now,
        'action': action,
        'memberId': memberId,
        'objId': objId,
        'objective': objective
            },
    'client-os': {
        'UUID': uuid,
        'name': clientOS,
        'version': version,
        'device name': device,
            }
    }
    logging_client = logging.Client()
    logger = logging_client.logger(logger_name)
    logger.log_struct(info = clientInfo, severity = "INFO", resource = resource, log_name = logger_name)
    return JSONResponse(
        status_code = status.HTTP_200_OK,
        content = {"message": "success"}
    )