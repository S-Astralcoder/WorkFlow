# External
import argparse
import time
from typing import Optional, List
from rich.prompt import Prompt
from rich.console import Console

#Internal
from workflow.command_line import CommandLine
from workflow.operations import CreateCommand, CopyCommand, MoveCommand, RenameCommand, DeleteCommand
from workflow.operations.response import Status
from workflow.sequence_workflow import SequenceOperations, WorkFlowConstructor
from workflow.sequence_workflow.virtual_tree import to_rich_tree
from workflow.sequence_workflow.workflow import ExecuteWorkflow



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
            return workflow_executor(arg=arg, console=console)
        case _:
            console.print("[red] Invalid Operator")
            return 1

    return 0


def workflow_executor(arg : argparse.Namespace, console : Console) -> int:
    workflow_data = WorkFlowConstructor(args=arg).get_workspace_sequence_data()
    sequence_orchestrator = SequenceOperations(workflow_data=workflow_data)
    with console.status(status="[green]Simulating Workflow operation.."):
        sequence_orchestrator.load_workspace_virtual_tree()
        sequence_orchestrator.validate_sequence_operation()
        time.sleep(2)
    if sequence_orchestrator.error_cache:
        console.print("[red]Simulation Finished with error..")
        for keys, values in sequence_orchestrator.error_cache.items():
            console.print(f"Action id {keys} : {values}")
        return 1
    else:
        console.print("[green]Simulation Passed successfully, Displaying simulation end results")
        console.print(to_rich_tree(sequence_orchestrator.virtual_tree.root_node))
        if not permission_func(prompt="[yellow]Would you like to execute this workflow"):
            console.print("[yellow]Permission Not granted. Exiting..")
            return 0
        if not sequence_orchestrator.allow:
            if not permission_func(prompt="[yellow]To continue. Please grant destructive actions permission, after reviewing the simulated end result"):
                console.print("[yellow]Permission Not granted. Exiting..")
                return 0
            arg.allow = True
        
        with console.status("Executing Workflow operations.."):
            workflow_execute = ExecuteWorkflow(workflow_data=workflow_data, args=arg)
            workflow_execute.execute_commands()             

    return 1