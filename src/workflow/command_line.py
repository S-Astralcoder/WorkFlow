# External
from typing import Optional, List 
import argparse


class CommandLine:
    def __init__(self) -> None:
        self.arg = argparse.ArgumentParser(description="Create, copy, move, rename, and delete files or folders within a workspace.")
        
        self.add_global_tags()

        self.operations = self.arg.add_subparsers(dest="operation", required=True)

        # create
        self.add_create_command_line()

        # copy
        self.add_copy_command_line()
        
        # move
        self.add_move_command_line()

        # rename
        self.add_rename_command_line()

        # delete
        self.add_delete_command_line()

        # workflow
        self.add_workflow_command_line()

    def add_global_tags(self):
        self.arg.add_argument("-a", "--allow", action="store_true", help="skip the confirmation prompt for operations that require approval")
        self.arg.add_argument("-f", "--force", action="store_true", help="allow supported overwrite or extension-change behavior; permanently delete instead of using the recycle bin (not supported for copy or move)")
        self.arg.add_argument("-d", "--dry-run", action="store_true", help="preview the operation without changing the file system")
        self.arg.add_argument("-s", "--show-status", action="store_true", help="display a brief result after execution")
        self.arg.add_argument("-ws", "--workspace", action="store", default=".")

    def add_create_command_line(self):
        create_parser = self.operations.add_parser("create")
        create_parser.add_argument("type", choices=("file", "folder"), metavar="TYPE", help="type of item to create: file or folder")
        create_parser.add_argument("-r", "--recursive", action="store_true", help="create missing parent folders")
        create_parser.add_argument("path",metavar="PATH" ,help="path of the file or folder to create")

    def add_copy_command_line(self):
        copy_parser = self.operations.add_parser("copy")
        copy_parser.add_argument("source_path", help="path of the file or folder to copy")
        copy_parser.add_argument("destination_path", help="existing folder into which the source will be copied")

    def add_move_command_line(self):
        move_parser = self.operations.add_parser("move")
        move_parser.add_argument("source_path", help="path of the file or folder to move")
        move_parser.add_argument("destination_path", help="existing folder into which the source will be moved")

    def add_rename_command_line(self):
        rename_parser = self.operations.add_parser("rename")
        rename_parser.add_argument("path", help="path of the file or folder to rename")
        rename_parser.add_argument("new_name", help="new name only, without a parent path")

    def add_delete_command_line(self):
        delete_parser = self.operations.add_parser("delete")
        delete_parser.add_argument("path", help="path of the file or folder to delete")

    def add_workflow_command_line(self):
        workflow_parser = self.operations.add_parser("run")
        workflow_parser.add_argument("workflow_path", help="Path to workflow script")

    def get_parser(self, args : Optional[List[str]] = None):
        return self.arg.parse_args(args=args)
