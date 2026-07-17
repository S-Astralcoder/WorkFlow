# External
from typing import Optional, List
from rich.prompt import Prompt
from rich.console import Console

#Internal
from workflow.command_line import CommandLine
from workflow.operations import CreateCommand, CopyCommand, MoveCommand, RenameCommand, DeleteCommand
from workflow.sequence_workflow import WorkFlowConstructor



def permission_func(prompt : str):
    response = Prompt.ask(prompt=prompt, choices=["yes", "no"], case_sensitive=False, default="no")
    if response == "yes":
        return True
    else:
        return False        

def workflow(args : Optional[List[str]] = None):
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
        case "run":
            workflow_data = WorkFlowConstructor(args=arg).get_workspace_sequence_data()
            console.print(workflow_data)
        case _:
            console.print("[red] Invalid Operator")



