# External
import argparse
from pathlib import Path

# Internal
from workflow.exceptions import CollisionError, InvalidFileName, InvalidFileType, OperationOnSelf, SourceNotFoundError
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

        self._mandatory_check()

        if not self.force:
            self._safe_check()
        elif FileSafety.does_exists(self.new_name):
            self.new_name = self._get_unique_name(self.new_name)
        
    def _validate_rename_path(self, path : str) -> Path:
        """Same validation but added check for if path exists"""
        source_path = self._validate_path(path=path)
        if not FileSafety.does_exists(path=source_path):
            raise SourceNotFoundError(f"Cannot rename '{source_path}': the source does not exist.")
        return source_path

    def _validate_name(self, new_name : str) -> Path:
        if not FileSafety.check_if_valid_name(name=new_name):
            raise InvalidFileName(f"Cannot rename '{self.path}' to '{new_name}': provide a valid name without a parent path or invalid characters.")
        return self.path.parent / Path(new_name).name

    def _safe_check(self):
        if self.is_file and self.path.suffix != Path(self.new_name).suffix:
            raise InvalidFileType(f"Cannot rename file '{self.path}' to '{self.new_name}': extension '{self.path.suffix}' would change to '{self.new_name.suffix}'. Use --force to allow it.")
        if FileSafety.does_exists(self.new_name):
            raise CollisionError(f"Cannot rename '{self.path}' to '{self.new_name}': the target already exists. Use --force to choose an available numbered name.")

    def _get_unique_name(self, requested_path: Path) -> Path:
        stem = requested_path.stem if self.is_file else requested_path.name
        suffix = requested_path.suffix if self.is_file else ""
        number = 2

        while True:
            candidate = requested_path.parent / f"{stem}{number}{suffix}"
            if not FileSafety.does_exists(candidate):
                return candidate
            number += 1

    def _mandatory_check(self):
        if FileSafety.same_path(self.path, self.new_name):
            raise OperationOnSelf("The new name is same as the original name")

    def execute_command(self):
        if self.dry_run:
            return CommandResult(status=Status.DRY_RUN, message=f"Would Rename {self.path.name} to {self.new_name.name}")
        try:
            self.path.rename(self.new_name)
        except (OSError, PermissionError) as e:
            return CommandResult(status=Status.FAILED, message=f"Failed to rename '{self.path}' to '{self.new_name}'.", error=str(e))
        return CommandResult(
            status=Status.SUCCESSFUL,
            message=f"Renamed '{self.path}' to '{self.new_name}'.",
        )
        


