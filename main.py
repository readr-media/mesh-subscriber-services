from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import src.request_body as request_body
from src.handler import userlog_handler, notify_handler, action_handler

### App related variables
app = FastAPI()
origins = ["*"]
methods = ["*"]
headers = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = methods,
    allow_headers = headers
)

### API Design
@app.get('/')
async def health_checking():
  '''
  Health checking API. You can only use @cache decorator to get method.
  '''
  return dict(message="Health check for mesh-subscriber-services")

@app.post('/userlog-sub')
async def userlog(request: request_body.SubRequest):
  '''
  Userlog subscribe API. This is called by pubsub.
  '''
  response: JSONResponse = userlog_handler(request)
  return response

@app.post('notify-sub')
async def notify(request: request_body.SubRequest):
  response: JSONResponse = notify_handler(request)
  return response

@app.post('action-sub')
async def action(request: request_body.SubRequest):
  response: JSONResponse = action_handler(request)
  return response