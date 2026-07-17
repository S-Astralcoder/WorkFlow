# External
import argparse
import os
from pathlib import Path

# Internal 
from workflow.safety import FileSafety
from workflow.exceptions import InvalidFilePath, LimitationError, OutOfScope, WorkspacePathInvalid, WorkspaceProtection


class BaseCommand:
    """A standard class to be avoid repeated code"""
    def __init__(self, args : argparse.Namespace) -> None:
        # global tags
        self.allow : bool = args.allow
        self.force : bool = args.force
        self.dry_run : bool = args.dry_run
        self.workspace : Path = self._validate_workspace_path(path=args.workspace)

        self.is_file : bool

    def _resolve_path(self, path: str) -> Path:
        """Validate the path string and return its absolute representation."""
        if not FileSafety.valid_path_string(path=path):
            raise InvalidFilePath(f"Invalid path '{path}': the value is not a valid file or folder path.")

        absolute_path = Path(os.path.abspath(path))
        if any(os.path.islink(candidate) for candidate in (absolute_path, *absolute_path.parents)):
            raise LimitationError(
                f"Cannot operate on '{absolute_path}': symbolic links are not supported in this version."
            )
        return absolute_path.resolve()

    def _validate_workspace_path(self, path : str):
        workspace_path = self._resolve_path(path)
        if not FileSafety.does_exists(path=workspace_path):
            raise WorkspacePathInvalid(f"Workspace '{workspace_path}' does not exist. Choose an existing folder with --workspace.")
        if FileSafety.check_if_file(path=workspace_path):
            raise WorkspacePathInvalid(f"Workspace '{workspace_path}' should be a folder. Choose an folder with --workspace.")
        return workspace_path

    def _validate_path(self, path : str):
        """Validate that a path is valid and already exists."""
        check_path = self._resolve_path(path)
        if not FileSafety.does_exists(path=check_path):
            raise WorkspacePathInvalid(f"The given path '{check_path}' does not exist. Choose an existing path.")
        return check_path

    def validate_workspace_scope(self, workspace : Path, path : Path, inside : bool = True):
        """checks if the action path is outside the workspace. to prevent operations outside of workspace"""
        if not FileSafety.is_relative_to(path1=workspace, path2=path):
            raise OutOfScope(f"Path '{path}' is outside workspace '{workspace}'. Choose a path inside that workspace or change --workspace.")
        if inside:
            if FileSafety.same_path(path1=workspace, path2=path):
                raise WorkspaceProtection(f"Path '{path}' is the workspace root. This operation must target an item inside '{workspace}'.")
        
