# External
from typing import Optional, List



#Internal
from .command_line import CommandLine

def pathflow(args : Optional[List[str]] = None):
    arg = CommandLine().get_parser(args=args)   # pyright: ignore[reportUnusedVariable]