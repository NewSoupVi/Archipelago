import zipfile
from pathlib import Path
from zipfile import is_zipfile

world_folder = Path(__file__).parent.parent.parent

if is_zipfile(world_folder):
    with zipfile.ZipFile(world_folder) as apworld:
        patches = [
            Path(zipinfo.filename) for zipinfo in apworld.infolist()
            if len(Path(zipinfo.filename).parts) > 1 and Path(zipinfo.filename).parts[-2] == "patches"
        ]
        patches = [path for path in patches if path.suffix in (".py", ".pyc")]
else:
    patches = [*Path(__file__).parent.glob("*.py"), *Path(__file__).parent.glob("*.pyc")]

patch_module_names = [path.stem for path in patches if path.stem != Path(__file__).stem]

__all__ = patch_module_names
