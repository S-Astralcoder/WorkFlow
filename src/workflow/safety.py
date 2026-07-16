#External
from pathlib import Path
from pathvalidate import is_valid_filepath, is_valid_filename
class FileSafety:
    @staticmethod
    def valid_path_string(path : str):
        return is_valid_filepath(file_path=path, platform="auto")
            
    @staticmethod
    def does_exists(path : str | Path):
        return Path(path).exists()

    @staticmethod
    def is_relative_to(path1 : Path, path2 : Path):
        return path2.is_relative_to(path1)

    @staticmethod
    def same_path(path1 : Path, path2 : Path):
        try:
            return path1.samefile(path2)
        except FileNotFoundError:
            return False

    @staticmethod
    def check_if_file(path : Path) -> bool:
        return path.is_file()

    @staticmethod
    def check_if_valid_name(name : str) -> bool:
        return is_valid_filename(filename=name, platform="auto")
    
    @staticmethod
    def check_if_toml_file(path : Path) -> bool:
        return path.suffix == ".toml"    
