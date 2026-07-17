# External
import argparse
from pathlib import Path
import shutil

# Internal
from workflow.exceptions import CollisionError, InvalidItemType, SameFileError, SourceNotFoundError
from workflow.operations.base import BaseCommand
from workflow.operations.response import CommandResult, Status
from workflow.safety import FileSafety


class CopyCommand(BaseCommand):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__(args)
        # paths
        self.source_path : Path = self._validate_source_path(args.source_path)
        self.destination_path : Path = self._validate_destination_path(args.destination_path)
        
        # states
        self.is_file = FileSafety.check_if_file(self.source_path)

        self.validate_workspace_scope(workspace=self.workspace, path=self.source_path)
        self.validate_workspace_scope(workspace=self.workspace, path=self.destination_path)

        if not self.force:
            self._safe_check()
        
        self._mandatory_check()

    def _validate_source_path(self, path : str) -> Path:
        """Same validation but added check for if path exists"""
        source_path = self._validate_path(path=path)
        if not FileSafety.does_exists(path=source_path):
            raise SourceNotFoundError(f"Source '{source_path}' does not exist. Choose an existing file or folder.")
        return source_path

    def _validate_destination_path(self, path : str) -> Path:
        """Same as above but also checks if the destination is a folder"""
        destination_path = self._validate_path(path=path)
        if not FileSafety.does_exists(path=destination_path):
            raise SourceNotFoundError(f"Destination '{destination_path}' does not exist. Choose an existing folder.")
        if FileSafety.check_if_file(path=destination_path):
            raise InvalidItemType(f"Destination '{destination_path}' is a file. Copy and move destinations must be folders.")
        return destination_path

    def _safe_check(self):
        """Again optional safety check. to prevent overwrites"""
        if any([self.source_path.name == item.name for item in self.destination_path.iterdir()]):
            target = self.destination_path / self.source_path.name
            raise CollisionError(f"Cannot copy or move '{self.source_path}' to '{self.destination_path}': target '{target}' already exists. Use --force to overwrite it.")

    def _mandatory_check(self):
        """Check that is very import to prevent cascaded copy loop (i made that term up)"""
        if FileSafety.same_path(path1=self.source_path, path2=self.destination_path):
            raise SameFileError(f"Source '{self.source_path}' and destination '{self.destination_path}' resolve to the same path. Choose a different destination folder.")

    def execute_command(self) -> CommandResult:
        """executes command while taking tags into consideration"""
        if self.dry_run:
            item_type = "file" if self.is_file else "folder"
            return CommandResult(status=Status.DRY_RUN, message=f"Would Copy {item_type} {self.source_path.name} to {self.destination_path}")
        try:
            if self.is_file:
                shutil.copy2(src=self.source_path, dst=self.destination_path / self.source_path.name)
            else:
                shutil.copytree(src=self.source_path, dst=self.destination_path / self.source_path.name, dirs_exist_ok=self.force)
        except Exception as e:
            target = self.destination_path / self.source_path.name
            return CommandResult(status=Status.FAILED, message=f"Failed to copy '{self.source_path}' to '{target}'.", error=str(e))
        return CommandResult(status=Status.SUCCESSFUL, message="Successfully Executed")

    

