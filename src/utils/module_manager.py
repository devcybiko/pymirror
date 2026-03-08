import zipfile
import importlib.util
import importlib.abc
import sys
import os

# Custom loader for loading code from bytes (from zip)
class ZipModuleLoader(importlib.abc.Loader):
    def __init__(self, name, code_bytes):
        self.name = name
        self.code_bytes = code_bytes

    def create_module(self, spec):
        return None  # Use default module creation

    def exec_module(self, module):
        exec(self.code_bytes, module.__dict__)

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
    def append_module_from_zip(zip_file, module_name, zip_path, package=None):
        """
        Load a module from a zip file and attach it to sys.modules and optionally a package.
        zip_file: a ZipFile object
        module_name: e.g. "foo"
        zip_path: e.g. "foo.py" or "subdir/foo.py"
        package: parent package name (string) or None
        """
        code_bytes = zip_file.read(zip_path)
        loader = ZipModuleLoader(module_name, code_bytes)
        spec = importlib.util.spec_from_loader(module_name, loader, is_package=False)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        sys.modules[module_name] = module
        if package:
            if package in sys.modules:
                setattr(sys.modules[package], module_name, module)
        return module

    @staticmethod
    def load_modules(folder: str, package_name: str):
        if folder.endswith(".zip"):
            return ModuleManager.load_modules_from_zip(folder, package=package_name)
        path = os.path.abspath(folder)
        package_path = os.path.join(path, package_name)
        sys.path.insert(0, package_path)
        for filename in os.listdir(package_path):
            full_path = os.path.join(package_path, filename)
            if filename.endswith(".py") and not filename.startswith("__"):
                print(f"Found module file: {filename} in package: {package_name}")
                module_name = filename[:-3]  # Remove .py extension
                ModuleManager.append_module(package_path, package_name, module_name)
            elif os.path.isdir(full_path) and not filename.startswith("__"):
                print(f"Found subpackage: {filename} in package: {package_name}")
                for sub_filename in os.listdir(full_path):
                    if sub_filename.endswith(".py") and not sub_filename.startswith("__"):
                        print(f"Found module file: {sub_filename} in subpackage: {filename}")
                        sub_module_name = sub_filename[:-3]  # Remove .py extension
                        ModuleManager.append_module(full_path, f"{package_name}.{filename}", sub_module_name)

    @staticmethod
    def load_modules_from_zip(zip_path, package=None):
        """
        Load all .py modules from a zip file and merge them into a package if specified.
        zip_path: path to the .zip file
        package: parent package name (string) or None
        """
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if name.endswith('.py') and not name.endswith('__init__.py'):
                    # Module name: strip path and .py
                    module_name = name.rsplit('/', 1)[-1][:-3]
                    ModuleManager.append_module_from_zip(zf, module_name, name, package=package)