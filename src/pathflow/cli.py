# External
from typing import Optional, List
from rich.prompt import Prompt

#Internal
from pathflow.command_line import CommandLine
from pathflow.operations.delete import DeleteCommand

def pathflow(args : Optional[List[str]] = None):
    arg = CommandLine().get_parser(args=args)   # pyright: ignore[reportUnusedVariable]
    print(DeleteCommand(args=arg).execute_command(permission_func=permission_func))


def permission_func(prompt : str):
    response = Prompt.ask(prompt=prompt, choices=["yes", "no"], case_sensitive=False, default="no")
    if response == "yes":
        return True
    else:
        return False        



