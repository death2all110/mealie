import pathlib
import re
from dataclasses import dataclass, field

from _gen_utils import log, render_python_template
from _static import PROJECT_DIR

template = """# This file is auto-generated by gen_schema_exports.py
{% for file in data.module.files %}{{ file.import_str() }}
{% endfor %}

__all__ = [
    {% for file in data.module.files %}
    {%- for class in file.classes -%}
    "{{ class }}",
    {%- endfor -%}
    {%- endfor %}
]

"""

SCHEMA_PATH = PROJECT_DIR / "mealie" / "schema"

SKIP = {"static", "__pycache__"}


class PyFile:
    import_path: str
    """The import path of the file"""

    classes: list[str]
    """A list of classes in the file"""

    def __init__(self, path: pathlib.Path):
        self.import_path = path.stem
        self.classes = []

        self.classes = PyFile.extract_classes(path)

    def import_str(self) -> str:
        """Returns a string that can be used to import the file"""
        return f"from .{self.import_path} import {', '.join(self.classes)}"

    @staticmethod
    def extract_classes(file_path: pathlib.Path) -> list[str]:
        name = file_path.stem

        if name == "__init__" or name.startswith("_"):
            return []

        classes = re.findall(r"(?m)^class\s(\w+)", file_path.read_text())
        return classes


@dataclass
class Modules:
    directory: pathlib.Path
    """The directory to search for modules"""

    files: list[PyFile] = field(default_factory=list)
    """A list of files in the directory"""

    def __post_init__(self):
        for file in self.directory.glob("*.py"):
            if file.name.startswith("_"):
                continue

            pfile = PyFile(file)

            if len(pfile.classes) > 0:
                self.files.append(pfile)

            else:
                log.debug(f"Skipping {file.name} as it has no classes")


def find_modules(root: pathlib.Path) -> list[Modules]:
    """Finds all the top level modules in the provided folder"""
    modules: list[Modules] = []
    for file in root.iterdir():
        if file.is_dir() and file.name not in SKIP:

            modules.append(Modules(directory=file))

    return modules


def main():

    modules = find_modules(SCHEMA_PATH)

    for module in modules:
        log.debug(f"Module: {module.directory.name}")
        for file in module.files:
            log.debug(f"  File: {file.import_path}")
            log.debug(f"    Classes: [{', '.join(file.classes)}]")

        render_python_template(template, module.directory / "__init__.py", {"module": module})


if __name__ == "__main__":
    main()
