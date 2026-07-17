# External
from typing import Optional, List
from rich.prompt import Prompt
from rich.console import Console

#Internal
from workflow.command_line import CommandLine
from workflow.operations import CreateCommand, CopyCommand, MoveCommand, RenameCommand, DeleteCommand
from workflow.operations.response import Status
from workflow.sequence_workflow import WorkFlowConstructor



def permission_func(prompt : str):
    response = Prompt.ask(prompt=prompt, choices=["yes", "no"], case_sensitive=False, default="no")
    if response == "yes":
        return True
    else:
        return False        

def workflow(args : Optional[List[str]] = None) -> int:
    console = Console()
    arg = CommandLine().get_parser(args=args)   
    match arg.operation:
        case "create":
            command = CreateCommand(args=arg)
            result = command.execute_command()
            if arg.dry_run or arg.show_status or result.status is Status.FAILED:
                console.print(result)
            if result.status is Status.FAILED:
                return 1
        case "copy":
            command = CopyCommand(args=arg)
            result = command.execute_command()
            if arg.dry_run or arg.show_status or result.status is Status.FAILED:
                console.print(result)
            if result.status is Status.FAILED:
                return 1
        case "move":
            command = MoveCommand(args=arg)
            result = command.execute_command()
            if arg.dry_run or arg.show_status or result.status is Status.FAILED:
                console.print(result)
            if result.status is Status.FAILED:
                return 1
        case "rename":
            command = RenameCommand(args=arg)
            result = command.execute_command()
            if arg.dry_run or arg.show_status or result.status is Status.FAILED:
                console.print(result)
            if result.status is Status.FAILED:
                return 1
        case "delete":
            command = DeleteCommand(args=arg)
            result = command.execute_command(permission_func=permission_func)
            if arg.dry_run or arg.show_status or result.status is Status.FAILED:
                console.print(result)
            if result.status is Status.FAILED:
                return 1
        case "run":
            workflow_data = WorkFlowConstructor(args=arg).get_workspace_sequence_data()
            console.print(workflow_data)
        case _:
            console.print("[red] Invalid Operator")
            return 1

    return 0



