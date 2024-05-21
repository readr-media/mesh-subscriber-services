from pydantic import BaseModel

class SubRequest(BaseModel):
    message: dict