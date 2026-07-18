# External 
from enum import Enum, auto

from pydantic import BaseModel
from rich.console import Group
from rich.text import Text

class Status(Enum):
    SUCCESSFUL = auto()
    FAILED = auto()
    DRY_RUN = auto()
    SKIPPED = auto()



class CommandResult(BaseModel):
    status : Status 
    message : str
    error : str | None = None 

    def __rich__(self) -> Group:
        label, style = {
            Status.SUCCESSFUL: ("SUCCESS", "bold green"),
            Status.FAILED: ("FAILED", "bold red"),
            Status.DRY_RUN: ("DRY RUN", "bold yellow"),
            Status.SKIPPED: ("SKIPPED", "bold yellow"),
        }[self.status]

        summary = Text()
        summary.append(f"{label}: ", style=style)
        summary.append(self.message)

        if self.error is None:
            return Group(summary)

        reason = Text()
        reason.append("Reason: ", style="bold red")
        reason.append(self.error)
        return Group(summary, reason)


