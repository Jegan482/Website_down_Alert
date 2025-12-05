from pydantic import BaseModel

class Website(BaseModel):
    name: str
    url: str
    owner_email: str
