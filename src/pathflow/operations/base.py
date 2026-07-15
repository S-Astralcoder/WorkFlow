# External
import argparse
from pathlib import Path

# Internal 
from pathflow.safety import FileSafety
from pathflow.exceptions import InvalidFilePath, OutOfScope, WorkspaceProtection


class BaseCommand:
    def __init__(self, args : argparse.Namespace) -> None:
        # global
        self.allow : bool = args.allow
        self.force : bool = args.force
        self.dry_run : bool = args.dry_run
        self.workspace : Path = self._validate_path(path=args.workspace)

        self.is_file : bool

    def _validate_path(self, path : str):
        if not FileSafety.valid_path_string(path=path):
            raise InvalidFilePath("The given path is invalid, enter a valid path")
        return Path(path).resolve()

    def validate_workspace_scope(self, workspace : Path, path : Path, inside : bool = True):
        if not FileSafety.is_relative_to(path1=workspace, path2=path):
            raise OutOfScope("The action path is outside of workspace scope")
        if inside:
            if FileSafety.same_path(path1=workspace, path2=path):
                raise WorkspaceProtection("Operation on workspace is not allowed")
        
    