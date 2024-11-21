import datetime
import uuid
import src.config as config

# Ex: iso_time = "2023-10-14T09:15:06.863Z"
def get_timestamp(iso_time):
    dt = datetime.datetime.strptime(iso_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    timestamp = dt.timestamp()
    return int(timestamp)

def gen_uuid(length: int=config.NOTIFY_UUID_LENGTH):
    return str(uuid.uuid4())[:length]

def get_current_timestamp():
    return int(datetime.datetime.now().timestamp())