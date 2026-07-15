# External
from typing import Optional, List
from rich.prompt import Prompt
from rich.console import Console

#Internal
from pathflow.command_line import CommandLine
from pathflow.operations import CreateCommand, CopyCommand, MoveCommand, RenameCommand, DeleteCommand


def permission_func(prompt : str):
    response = Prompt.ask(prompt=prompt, choices=["yes", "no"], case_sensitive=False, default="no")
    if response == "yes":
        return True
    else:
        return False        

def pathflow(args : Optional[List[str]] = None):
    console = Console()
    arg = CommandLine().get_parser(args=args)   
    match arg.operation:
        case "create":
            command = CreateCommand(args=arg)
            result = command.execute_command()
            if arg.dry_run or arg.show_status:
                console.print(result)
        case "copy":
            command = CopyCommand(args=arg)
            result = command.execute_command()
            if arg.dry_run or arg.show_status:
                console.print(result)
        case "move":
            command = MoveCommand(args=arg)
            result = command.execute_command()
            if arg.dry_run or arg.show_status:
                console.print(result)
        case "rename":
            command = RenameCommand(args=arg)
            result = command.execute_command()
            if arg.dry_run or arg.show_status:
                console.print(result)
        case "delete":
            command = DeleteCommand(args=arg)
            result = command.execute_command(permission_func=permission_func)
            if arg.dry_run or arg.show_status:
                console.print(result)
        case _:
            console.print("[red] Invalid Operator")



