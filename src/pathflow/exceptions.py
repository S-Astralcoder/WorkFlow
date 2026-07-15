class InvalidFilePath(SystemExit):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class FileAlreadyExists(SystemExit):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class OutOfScope(SystemExit):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class WorkspaceProtection(SystemExit):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class ParentNotFount(SystemExit):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class ExecutionError(SystemError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class SourceNotFoundError(SystemExit):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class InvalidItemType(SystemExit):
    def __init__(self, *arg : object) -> None:
        super().__init__(*arg)

class CollisionError(SystemExit):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class SameFileError(SystemExit):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class InvalidSelfMove(SystemExit):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class ItemNotFound(SystemExit):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

