#External
import argparse
from pathlib import Path


#Internal
from .base import BaseCommand
from pathflow.operations.response import CommandResult, Status
from pathflow.exceptions import FileAlreadyExists, ParentNotFount
from pathflow.safety import FileSafety


class CreateCommand(BaseCommand):
    def __init__(self, args : argparse.Namespace) -> None:
        super().__init__(args=args)
        # states
        self.recursive : bool = args.recursive
        self.is_file : bool = args.type == "file"

        # path
        self.path : Path = self._validate_path(args.path)

        self.validate_workspace_scope(workspace=self.workspace, path=self.path)

        if not self.recursive:
            self._check_parent_exists()

        if not self.force:
            self._safe_checks()

    def _safe_checks(self):
        if FileSafety.does_exists(path=self.path):
            raise FileAlreadyExists("The given path points to a existing directory, use --force to allow overwrites")

    def _check_parent_exists(self):
        if not self.path.parent.exists():
            raise ParentNotFount("The given path's parent doesn't exist, use --recursive to create parent")

    def execute_command(self) -> CommandResult:
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


        
