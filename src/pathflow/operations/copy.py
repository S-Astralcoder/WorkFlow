# External
import argparse
from pathlib import Path

# Internal
from pathflow.exceptions import CollisionError, InvalidItemType, SourceNotFoundError
from pathflow.operations.base import BaseCommand
from pathflow.safety import FileSafety


class CopyCommand(BaseCommand):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__(args)
        # paths
        self.source_path : Path = self._validate_source_path(args.source_path)
        self.destination_path : Path = self._validate_destination_path(args.destination_path)
        
        # states
        self.is_file = FileSafety.check_if_file(self.source_path)

        if not self.force:
            self._safe_check()

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
        