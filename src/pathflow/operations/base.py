# External
import argparse
from pathlib import Path

# Internal 
from pathflow.safety import FileSafety
from pathflow.exceptions import InvalidFilePath, OutOfScope, WorkspaceProtection


class BaseCommand:
    """A standard class to be avoid repeated code"""
    def __init__(self, args : argparse.Namespace) -> None:
        # global tags
        self.allow : bool = args.allow
        self.force : bool = args.force
        self.dry_run : bool = args.dry_run
        self.workspace : Path = self._validate_path(path=args.workspace)

        self.is_file : bool

    def _validate_path(self, path : str):
        """validates if the path is correct"""
        if not FileSafety.valid_path_string(path=path):
            raise InvalidFilePath("Invalid path: enter a valid file or folder path.")
        return Path(path).resolve()

    def validate_workspace_scope(self, workspace : Path, path : Path, inside : bool = True):
        """checks if the action path is outside the workspace. to prevent operations outside of workspace"""
        if not FileSafety.is_relative_to(path1=workspace, path2=path):
            raise OutOfScope("Path is outside the configured workspace. Choose a path inside the workspace or change --workspace.")
        if inside:
            if FileSafety.same_path(path1=workspace, path2=path):
                raise WorkspaceProtection("This operation cannot target the workspace root itself. Choose an item inside the workspace.")
        
