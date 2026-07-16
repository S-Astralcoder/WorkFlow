#External
import argparse
from pathlib import Path


#Internal
from .base import BaseCommand
from pathflow.operations.response import CommandResult, Status
from pathflow.exceptions import FileAlreadyExists, ParentNotFount
from pathflow.safety import FileSafety


class CreateCommand(BaseCommand):
    """Validates and executes create file/folder operation"""
    def __init__(self, args : argparse.Namespace) -> None:
        super().__init__(args=args)
        # states
        self.recursive : bool = args.recursive
        self.is_file : bool = args.type == "file"

        # path
        self.path : Path = self._resolve_path(args.path)

        self.validate_workspace_scope(workspace=self.workspace, path=self.path) 

        if not self.recursive:
            self._check_parent_exists()

        if not self.force:
            self._safe_checks()

    def _safe_checks(self):
        """A optional safety check to prevent accidental overwrites without permission"""
        if FileSafety.does_exists(path=self.path):
            raise FileAlreadyExists("An item already exists at the target path. Use --force to allow the existing item to be overwritten.")

    def _check_parent_exists(self):
        """checks it parent for the given path exists"""
        if not self.path.parent.exists():
            raise ParentNotFount("The target's parent folder does not exist. Use --recursive to create the missing parent folders.")

    def execute_command(self) -> CommandResult:
        """just executes what else?"""
        if self.dry_run:
            item_type = "file" if self.is_file else "folder"
            return CommandResult(status=Status.DRY_RUN, message=f"Would Create {item_type} : {self.path}")
        try:
            if self.is_file:
                if self.recursive:
                    self.path.parent.mkdir(parents=self.recursive, exist_ok=self.force)
                self.path.touch(exist_ok=self.force)
            else:
                self.path.mkdir(parents=self.recursive, exist_ok=self.force)
        except (OSError, PermissionError) as e:
            print(e)
            return CommandResult(status=Status.FAILED, message="Unexpected Error Occurred During Execution", error=str(e))
        return CommandResult(status=Status.SUCCESSFUL, message="Executed Successfully")


        
