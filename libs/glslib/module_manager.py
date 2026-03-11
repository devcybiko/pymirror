import re
import importlib.util
import importlib.abc
import sys
import os
from glslib.logger import _die, _print, _error

# Custom loader for loading code from bytes (from zip)
class ZipModuleLoader(importlib.abc.Loader):
    def __init__(self, name, code_bytes):
        self.name = name
        self.code_bytes = code_bytes

    def create_module(self, spec):
        return None  # Use default module creation

    def exec_module(self, module):
        exec(self.code_bytes, module.__dict__)

def _extract_imports(code):
    """
    Extract imported module names from the given code string.
    Returns a set of module names.
    """
    imports = []
    lines = code.splitlines()
    for line in lines:
        import_match = re.match(r"^\s*import\s+(\w+)", line)
        if import_match:
            imports.append(import_match.group(1))
        from_import_match = re.match(r"^\s*from\s+\.\s+import\s+(\w+)", line)
        if from_import_match:
            imports.append(from_import_match.group(1))
    return list(imports)

class ModuleManager:
    def __init__(self):
        pass
    
    @staticmethod
    def append_module(folder, package_name, module_name):
        filename = os.path.abspath(os.path.join(folder, module_name + ".py"))
        print(f"Loading module {package_name}.{module_name} from {filename}...")
        spec = importlib.util.spec_from_file_location(package_name, filename)
        module = importlib.util.module_from_spec(spec)
        print(f"...Registering module {package_name}.{module_name} in sys.modules...")
        sys.modules[f"{package_name}.{module_name}"] = module
        spec.loader.exec_module(module)

    @staticmethod
    def load_modules(folder: str, package_name: str, die_trying: bool = False):
        _print(f"Loading modules from package {package_name} in folder {folder}...")
        path = os.path.abspath(folder)
        _print(f"Resolved path: {path}")
        package_path = os.path.join(path, package_name)
        _print(f"Package path: {package_path}")
        sys.path.insert(0, package_path)
        _print(f"Added {package_path} to sys.path")
        init_file = os.path.join(package_path, "__init__.py")
        _print(f"Looking for __init__.py at {init_file}...")
        if not os.path.isfile(init_file):
            _print(f"__init__.py not found at {init_file}")
            _error(f"Package {package_name} must have an __init__.py file at {init_file}")
            if die_trying:
                _die(f"Package {package_name} must have an __init__.py file at {init_file}")
        else:
            _print(f"Found __init__.py at {init_file}")
            with open(init_file, "r") as f:
                lines = f.read().splitlines()
                imports = _extract_imports("\n".join(lines))
            for module in imports:
                ModuleManager.append_module(package_path, package_name, module)
