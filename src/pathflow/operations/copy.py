# External
import argparse
from pathlib import Path
import shutil

# Internal
from pathflow.exceptions import CollisionError, InvalidItemType, SameFileError, SourceNotFoundError
from pathflow.operations.base import BaseCommand
from pathflow.operations.response import CommandResult, Status
from pathflow.safety import FileSafety


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
        source_path = self._validate_path(path=path)
        if not FileSafety.does_exists(path=source_path):
            raise SourceNotFoundError("The given source path doesn't exist")
        return source_path

    def _validate_destination_path(self, path : str) -> Path:
        destination_path = self._validate_path(path=path)
        if not FileSafety.does_exists(path=destination_path):
            raise SourceNotFoundError("The given source path doesn't exist")
        if FileSafety.check_if_file(path=destination_path):
            raise InvalidItemType("The given destination should be a folder")
        return destination_path

    def _safe_check(self):
        if any([self.source_path.name == item.name for item in self.destination_path.iterdir()]):
            raise CollisionError(f"{self.source_path.name} Already exists in {self.destination_path}, use --force to continue")

    def _mandatory_check(self):
        if FileSafety.same_path(path1=self.source_path, path2=self.destination_path):
            raise SameFileError("given path and destination are same. enter a different destination")

    def execute_command(self) -> CommandResult:
        if self.dry_run:
            item_type = "file" if self.is_file else "folder"
            return CommandResult(status=Status.DRY_RUN, message=f"Would Copy {item_type} {self.source_path.name} to {self.destination_path}")
        
        try:
            if self.is_file:
                shutil.copy2(src=self.source_path, dst=self.destination_path / self.source_path.name)
            else:
                shutil.copytree(src=self.source_path, dst=self.destination_path / self.source_path.name, dirs_exist_ok=self.force)
        except Exception as e:
            return CommandResult(status=Status.FAILED, message="Unexpected Error Occurred During Execution", error=str(e))
        return CommandResult(status=Status.SUCCESSFUL, message="Successfully Executed")

    

