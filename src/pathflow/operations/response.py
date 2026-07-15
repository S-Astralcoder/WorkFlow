# External 
from pydantic import BaseModel
from enum import Enum, auto

class Status(Enum):
    SUCCESSFUL = auto()
    FAILED = auto()
    DRY_RUN = auto()
    SKIPPED = auto()



class CommandResult(BaseModel):
    status : Status 
    message : str
    error : str | None = None 


