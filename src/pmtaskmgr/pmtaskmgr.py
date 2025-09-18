import argparse
from dataclasses import dataclass
import importlib
import os
import time
from icecream import ic as icprint
from dotenv import load_dotenv
from munch import DefaultMunch

from pmdb.pmdb import PMDb, PMDbConfig
from pymirror.utils import expand_dict, from_dict, munchify, json_read, snake_to_pascal


@from_dict
@dataclass
class PMTaskMgrConfig:
    pmdb: dict
    tasks: list[dict]

class PMTaskMgr:
    def __init__(self, config_fname: str):
        self._config = self._load_config(config_fname)
        self.pmdb = PMDb(self._config.pmdb)
        self.tasks = []
        self._load_tasks()
        pass
    
    def _dbinit():
        pass

    def _load_config(self, config_fname) -> PMTaskMgrConfig:
        # read .env file if it exists
        load_dotenv()
        # Load the main configuration file
        icprint(config_fname)
        config = json_read(config_fname)
        icprint(config)
        # Load secrets from .secrets file if specified
        secrets_path = config.get("secrets")
        if secrets_path:
            secrets_path = os.path.expandvars(secrets_path)
        else:
            secrets_path = ".secrets"
        load_dotenv(dotenv_path=secrets_path)
        # Expand environment variables in the config
        expand_dict(config, os.environ)
        obj = PMTaskMgrConfig.from_dict(config)
        icprint(obj)
        config = munchify(obj)
        return config

    def _load_tasks(self):
        for task_config in self._config.tasks:
            ## load the module dynamically
            if type(task_config) is str:
                ## if moddef is a string, it is the name of a module config file
                ## load the module definition from the file
                ## the file should be in JSON format
                config = munchify(json_read(task_config))
                if config == None:
                    raise Exception(f"ERROR: reading {task_config}")
                task_config = munchify(config)

            ## import the module using its name
            ## all modules should be in the "modules" directory
            icprint(task_config)
            mod = importlib.import_module("tasks."+task_config["class"]+"_task")
        
            ## get the class from inside the module
            ## convert the file name to class name inside the module
            ## by convention the filename is snake_case and the class name is PascalCase
            clazz_name = snake_to_pascal(task_config["class"])
            print(f"Loading task class {clazz_name} from {mod.__name__}")
            clazz = getattr(mod, clazz_name + "Task", None)

            ## create an instance of the class (module)
            ## and pass the PyMirror instance and the module config to it
            ## See pymirror.PMModule for the expected constructor
            obj = clazz(self, task_config)

            ## add the module to the list of modules
            self.tasks.append(obj)

    def run(self):
        while True:
            for task in self.tasks:
                task.exec()
                time.sleep(3)
            

def main():
    parser = argparse.ArgumentParser(description="PMTaskManager")
    parser.add_argument(
        "-c", "--config",
        default="./configs/rpi/tasks.json",
        help="Path to config JSON file (default: config.json)"
    )

    args = parser.parse_args()
    pmtaskmgr = PMTaskMgr(args.config)
    pmtaskmgr.run()

if __name__ == "__main__":
    main()