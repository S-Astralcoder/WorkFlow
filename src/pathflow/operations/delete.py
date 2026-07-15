# External
import argparse
import os
from pathlib import Path
import shutil
from typing import Callable
import send2trash 

# Internal
from pathflow.exceptions import ItemNotFound
from pathflow.operations.base import BaseCommand
from pathflow.operations.response import CommandResult, Status
from pathflow.safety import FileSafety


class DeleteCommand(BaseCommand):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__(args)
        # path
        self.path : Path = self._validate_target_path(path=args.path)

        # tag
        self.is_file = FileSafety.check_if_file(self.path)

        self.validate_workspace_scope(workspace=self.workspace, path=self.path)

    def _validate_target_path(self, path : str) -> Path:
        source_path = self._validate_path(path=path)
        if not FileSafety.does_exists(path=source_path):
            raise ItemNotFound("The given path doesn't exist")
        return source_path

    def execute_command(self, permission_func : Callable[[str],bool]) -> CommandResult:
        """ permission_func : a function from cli to request permission from user to execute, only if allow is false"""
        if self.dry_run:
            return CommandResult(status=Status.DRY_RUN, message=f"Would Delete : {self.path}")
        try:
            if self.allow or permission_func("[red]Do you want to execute this command"):
                if self.force: # performs permanent delete without shifting to trash bin if true
                    if self.is_file:
                        os.remove(self.path)
                    else:
                        shutil.rmtree(self.path)
                    return CommandResult(status=Status.SUCCESSFUL, message="Delete Permanently")
                else: # moves to trash bin
                    send2trash.send2trash(self.path)
                    return CommandResult(status=Status.SUCCESSFUL, message="Moved to bin")
        except (OSError, PermissionError) as e:
            return CommandResult(status=Status.FAILED, message="Unexpected Error Occurred During Execution", error=str(e))
        return CommandResult(status=Status.SKIPPED, message="Execution Skipped")
        
    
