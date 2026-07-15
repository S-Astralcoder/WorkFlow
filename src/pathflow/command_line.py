# External
from typing import Optional, List 
import argparse


class CommandLine:
    def __init__(self) -> None:
        self.arg = argparse.ArgumentParser(description="manage workspace")
        
        self.add_global_tags()

        self.operations = self.arg.add_subparsers(dest="operation", required=True)

        # create
        self.add_create_command_line()


    def add_global_tags(self):
        self.arg.add_argument("-a", "--allow", action="store_true", help="Bypass permissions")
        self.arg.add_argument("-f", "--force", action="store_true", help="Bypass safe execution [at your own risk]")
        self.arg.add_argument("-d", "--dry-run", action="store_true", help="run a simulated execution")
        self.arg.add_argument("-ws", "--workspace", action="store", default=".")

    def add_create_command_line(self):
        create_parser = self.operations.add_parser("create")
        create_parser.add_argument("type", choices=("file", "folder"), metavar="TYPE", help="Choose file or folder to create")
        create_parser.add_argument("-r", "--recursive", action="store_true", help="create parent directory if not exists")
        create_parser.add_argument("path",metavar="PATH" ,help="path to be created")

    
    def get_parser(self, args : Optional[List[str]] = None):
        return self.arg.parse_args(args=args)