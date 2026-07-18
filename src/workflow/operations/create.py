#External
import argparse
from pathlib import Path


#Internal
from .base import BaseCommand
from workflow.operations.response import CommandResult, Status
from workflow.exceptions import FileAlreadyExists, ParentNotFount
from workflow.safety import FileSafety


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
            raise FileAlreadyExists(f"Cannot create '{self.path}': an item already exists at that path. Use --force to keep or reuse it.")

    def _check_parent_exists(self):
        """checks it parent for the given path exists"""
        if not self.path.parent.exists():
            raise ParentNotFount(f"Cannot create '{self.path}': parent folder '{self.path.parent}' does not exist. Use --recursive to create missing parents.")

    def execute_command(self) -> CommandResult:
        """just executes what else?"""
        if self.dry_run:
            item_type = "file" if self.is_file else "folder"
            return CommandResult(
                status=Status.DRY_RUN,
                message=f"Would create {item_type} '{self.path}'.",
            )
        try:
            if self.is_file:
                if self.recursive:
                    self.path.parent.mkdir(parents=self.recursive, exist_ok=True)
                self.path.touch(exist_ok=self.force)
            else:
                self.path.mkdir(parents=self.recursive, exist_ok=self.force)
        except (OSError, PermissionError) as e:
            return CommandResult(status=Status.FAILED, message=f"Failed to create '{self.path}'.", error=str(e))
        item_type = "file" if self.is_file else "folder"
        return CommandResult(
            status=Status.SUCCESSFUL,
            message=f"Created {item_type} '{self.path}'.",
        )


        
