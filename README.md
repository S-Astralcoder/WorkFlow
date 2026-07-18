# Workflow

Workflow is a Python CLI for creating, copying, moving, renaming, and deleting files and folders inside a protected workspace. It can run one command at a time or simulate and execute a sequence of operations from a TOML workflow script.

> [!WARNING]
> This MVP is developed and tested for Windows. Linux, macOS, and other operating systems may behave differently or be incompatible, especially around filename rules, case sensitivity, path handling, the Recycle Bin, and symbolic links.

## Quick setup

Requirements:

- Windows
- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)

From PowerShell:

```powershell
git clone <repository-url>
cd workflow
uv sync --locked
uv run workflow --help
```

Run commands from the project environment with `uv run workflow`. Global options must appear before the operation name:

```powershell
uv run workflow --workspace . --show-status create file .\notes.txt
```

## Workspace safety

Every operation is restricted to a workspace. The default workspace is the current directory.

```powershell
uv run workflow --workspace . create folder .\demo
```

Paths outside the workspace are rejected. Destructive operations cannot target the workspace root itself. Symbolic links are also rejected in this MVP.

## The five commands

### Create

Create a file or folder:

```powershell
uv run workflow --workspace . --show-status create file .\notes.txt
uv run workflow --workspace . --show-status create folder .\src
```

Use `--recursive` after `create` to create missing parent folders:

```powershell
uv run workflow --workspace . --show-status create --recursive file .\src\app\main.py
```

With `--force`, create may reuse an existing target only when its type matches the requested type.

### Copy

Copy a file or folder into an existing destination folder:

```powershell
uv run workflow --workspace . --show-status copy .\notes.txt .\backup
uv run workflow --workspace . --show-status copy .\src .\backup
```

The copied item keeps its source name. Copying into the source itself or one of its descendants is rejected. Overwriting an existing target is disabled, including when `--force` is supplied.

### Move

Move a file or folder into an existing destination folder:

```powershell
uv run workflow --workspace . --show-status move .\notes.txt .\archive
uv run workflow --workspace . --show-status move .\src .\archive
```

Moving into the source itself or one of its descendants is rejected. Overwriting an existing target is disabled, including when `--force` is supplied.

### Rename

Rename an existing file or folder. `NEW_NAME` must contain only the new name, not a parent path:

```powershell
uv run workflow --workspace . --show-status rename .\notes.txt ideas.txt
```

Without `--force`, a file must keep the same extension and the target name must be available. With `--force`, an extension may change. If the requested target exists, Workflow chooses the next numbered name, such as `ideas2.txt`.

### Delete

Delete an existing file or folder:

```powershell
uv run workflow --workspace . --show-status delete .\notes.txt
```

By default, delete requests permission and moves the item to the Windows Recycle Bin. `--allow` skips the per-operation prompt. Combining `--allow` and `--force` permanently deletes the item:

```powershell
uv run workflow --workspace . --allow --force --show-status delete .\old-build
```

Permanent deletion cannot be undone through the Recycle Bin.

## Command-line options

Global options must be placed before `create`, `copy`, `move`, `rename`, `delete`, or `run`.

| Option | Meaning for a basic command | Meaning for `run` |
| --- | --- | --- |
| `-ws`, `--workspace PATH` | Restrict the operation to this folder. | Override the workspace declared by the script. Use `*` to select the current directory explicitly. |
| `-a`, `--allow` | Skip confirmation where permission is required, currently delete. | Pre-authorize destructive workflow actions after the workflow-level execution confirmation. |
| `-f`, `--force` | Reuse supported create targets, permit rename extension changes/numbering, or permanently delete. Copy/move overwrite remains disabled. | Enable the same supported behavior for every action. Be careful: workflow deletes become permanent. |
| `-d`, `--dry-run` | Preview one operation without changing the filesystem. | Simulate the complete workflow, show the final virtual state, and stop without executing commands. |
| `-s`, `--show-status` | Show readable success, failure, skipped, or dry-run feedback. Failures are always shown. | Show status feedback for each command during physical execution. The simulated tree is always shown. |

Create also supports `-r` / `--recursive`. This is an operation option and appears after `create`.

## Workflow scripts

A workflow is a TOML file with one `[workflow]` table and one or more `[[actions]]` tables. Actions are processed in order against a virtual representation of the workspace.

Before touching the filesystem, Workflow:

1. Loads the current workspace tree.
2. Validates every action is inside the workspace.
3. Simulates create, copy, move, rename, and delete in order.
4. Displays the simulated final tree.
5. Reports every predictable failure using its action ID.
6. Executes only after simulation succeeds and the user confirms.

If `dry_run = true` or `--dry-run` is supplied, simulation is the final result and no physical commands run.

### Workflow settings

```toml
[workflow]
name = "basic project setup"
workspace = "./examples/workspace"
force = false
dry_run = true
allow = false
show = true
```

| Field | Purpose |
| --- | --- |
| `name` | Optional descriptive workflow name. |
| `workspace` | Existing folder that contains every action path. Required unless overridden from the CLI. |
| `force` | Enables supported force behavior globally. Copy and move overwrite remains disabled. |
| `dry_run` | Stops after successful simulation when true. |
| `allow` | Pre-authorizes destructive actions during physical execution. |
| `show` | Displays individual command results during physical execution. |

CLI flags can enable the corresponding workflow settings for a run.

### Action formats

Create:

```toml
[[actions]]
operation = "create"
type = "file" # "file" or "folder"
path = "./project/src/main.py"
recursive = true # optional, defaults to false
```

Copy:

```toml
[[actions]]
operation = "copy"
source_path = "./project/src/main.py"
destination_path = "./project/backup"
```

Move:

```toml
[[actions]]
operation = "move"
source_path = "./project/backup/main.py"
destination_path = "./project/archive"
```

Rename:

```toml
[[actions]]
operation = "rename"
path = "./project/archive/main.py"
new_name = "example.py"
```

Delete:

```toml
[[actions]]
operation = "delete"
path = "./project/backup"
```

Paths may refer to files and folders created by earlier actions because simulation updates the virtual tree after every valid action.

### Run a workflow

The included basic example is safe by default because it has `dry_run = true`:

```powershell
uv run workflow run .\examples\workflows\basic_project_setup.toml
```

Other included scripts:

| Script | Expected result |
| --- | --- |
| `virtual_state_stress_test.toml` | Successful dry-run covering dependent virtual operations. |
| `failing_collision.toml` | Simulation failure with a create collision at action 3. |
| `failing_missing_source.toml` | Simulation failure because the copy source is missing. |
| `invalid_missing_field.toml` | Script validation failure for a missing required field. |
| `invalid_operation.toml` | Script validation failure for an unsupported operation. |
| `invalid_toml_syntax.toml` | TOML parser failure with a concise error and no traceback. |

To execute a valid example physically, copy it, review every action, set `dry_run = false`, and run it again. Workflow will still simulate and display the final state before requesting execution permission.

## Current limitations

- Windows is the only tested and supported operating system for this MVP. Linux, macOS, and other systems may differ in filename validation, path semantics, case sensitivity, and trash behavior.
- Symbolic links are rejected. This affects copy, move, rename, delete, and paths created below a symbolic-link parent.
- Copy and move cannot overwrite or merge with an existing target. `--force` does not bypass this restriction.
- Case-only renames are not supported by workflow simulation because virtual names are normalized for Windows-style matching.
- Workflow execution is not transactional. If a physical action fails after earlier actions succeeded, completed actions are not rolled back.
- The filesystem may change between simulation and execution, so a workflow that simulated successfully can still fail while running.
- Very large or deeply nested workspaces may use significant memory or reach Python recursion limits during virtual copying or tree rendering.

## Next version

Hopefully the limitations of this version can be reduced and the design can become more concrete after building this project and learning more about how operating systems handle file and folder operations. Future versions may also add commands that do not normally exist as one filesystem operation, such as merging folders or extracting files from a source and all of its children into one folder.

> **Developer's note:** Don't curse me if you read the code. There are a lot of lazy patches—but hey, it works.

Feel free to clone this project and fix it, find bugs, add compatibility with other operating systems, or improve the current limitations in copy and move.
