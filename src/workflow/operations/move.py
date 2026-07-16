# External
import argparse
import shutil


# Internal
from workflow.exceptions import InvalidSelfMove
from workflow.operations.copy import CopyCommand
from workflow.operations.response import CommandResult, Status
from workflow.safety import FileSafety



class MoveCommand(CopyCommand):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__(args)

    def _mandatory_check(self):
        super()._mandatory_check()

        if FileSafety.is_relative_to(path1=self.source_path, path2=self.destination_path):
            raise InvalidSelfMove("A folder cannot be moved into one of its own descendants. Choose a destination outside the source folder.")

    def execute_command(self) -> CommandResult:
        if self.dry_run:
            item_type = "file" if self.is_file else "folder"
            return CommandResult(status=Status.DRY_RUN, message=f"Would Move {item_type} {self.source_path.name} to {self.destination_path}")
        try:
            shutil.move(self.source_path, self.destination_path)
        except (OSError, PermissionError) as e:
            return CommandResult(status=Status.FAILED, message="Unexpected Error Occurred During Execution", error=str(e))        
        return CommandResult(status=Status.SUCCESSFUL, message="Successfully Executed")

    
