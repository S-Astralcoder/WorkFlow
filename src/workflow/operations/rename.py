# External
import argparse
from pathlib import Path

# Internal
from workflow.exceptions import InvalidFileName, InvalidFileType, SourceNotFoundError
from workflow.operations.base import BaseCommand
from workflow.operations.response import CommandResult, Status
from workflow.safety import FileSafety


class RenameCommand(BaseCommand):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__(args)
        #path
        self.path : Path = self._validate_rename_path(path=args.path)
        self.new_name : Path = self._validate_name(new_name=args.new_name)

        # tag
        self.is_file = FileSafety.check_if_file(self.path)

        self.validate_workspace_scope(workspace=self.workspace, path=self.path)
        self.validate_workspace_scope(workspace=self.workspace, path=self.new_name)

        if not self.force:
            self._safe_check()
        
    def _validate_rename_path(self, path : str) -> Path:
        """Same validation but added check for if path exists"""
        source_path = self._validate_path(path=path)
        if not FileSafety.does_exists(path=source_path):
            raise SourceNotFoundError("Rename target does not exist. Enter the path of an existing file or folder.")
        return source_path

    def _validate_name(self, new_name : str) -> Path:
        if not FileSafety.check_if_valid_name(name=new_name):
            raise InvalidFileName("Invalid new name: provide a valid file or folder name without a path.")
        return self.path.parent / Path(new_name).name

    def _safe_check(self):
        if self.is_file and self.path.suffix != Path(self.new_name).suffix:
            raise InvalidFileType("The new filename uses a different extension. Keep the original extension or use --force to allow the change.")

    def execute_command(self):
        if self.dry_run:
            return CommandResult(status=Status.DRY_RUN, message=f"Would Rename {self.path.name} to {self.new_name.name}")
        try:
            self.path.rename(self.new_name)
        except (OSError, PermissionError) as e:
            return CommandResult(status=Status.FAILED, message="Unexpected Error Occurred During Execution", error=str(e))
        return CommandResult(status=Status.SUCCESSFUL, message="Executed Successfully")
        


