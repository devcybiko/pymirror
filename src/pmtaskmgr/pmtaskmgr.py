import argparse
from dataclasses import dataclass
import importlib
import os
import sys
import time
import traceback
from icecream import ic as ic
from dotenv import load_dotenv
from munch import DefaultMunch

from pmdb.pmdb import PMDb, PMDbConfig
from pmtaskmgr.pmtask import PMTask
from pymirror.crontab import Crontab
from pymirror.utils.utils import expand_dict, from_dict, munchify, json_read, snake_to_pascal
from pymirror.pmlogger import _debug

@from_dict
@dataclass
class PMTaskMgrConfig:
    pmdb: dict
    tasks: list[dict]

class PMTaskMgr:
    def __init__(self, config_fname: str):
        self._config = self._load_config(config_fname)
        self.pmdb: PMDb = PMDb(self._config.pmdb)
        self.tasks: list[PMTask] = []
        self._load_tasks()
        self.task_dict: dict = self._make_task_dict()
        self.cronlist = self._make_cronlist()
        self.crontab = Crontab(self.cronlist)
        pass
    
    def _dbinit():
        pass

    def _make_cronlist(self):
        cronlist = []
        for task in self.tasks:
            cronlist.append(task.cron+"|"+task.name)
        return cronlist

    def _make_task_dict(self):
        task_dict = {}
        for task in self.tasks:
            ic(task.name)
            task_dict[task.name] = task
        return task_dict

    def _load_config(self, config_fname) -> PMTaskMgrConfig:
        # read .env file if it exists
        load_dotenv()
        # Load the main configuration file
        ic(config_fname)
        config = json_read(config_fname)
        ic(config)
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
        ic(obj)
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
            ic(task_config)
            module_name = "tasks."+task_config["class"]+"_task"
            ic(module_name)
            mod = importlib.import_module(module_name)
            ic(mod)
            ## get the class from inside the module
            ## convert the file name to class name inside the module
            ## by convention the filename is snake_case and the class name is PascalCase
            clazz_name = snake_to_pascal(task_config["class"])+"Task"
            print(f"Loading task class {clazz_name} from {mod.__name__}")
            clazz = getattr(mod, clazz_name, None)

            ## create an instance of the class (module)
            ## and pass the PyMirror instance and the module config to it
            ## See pymirror.PMModule for the expected constructor
            obj = clazz(self, task_config)

            ## add the module to the list of modules
            self.tasks.append(obj)

    def run(self):
        while True:
            task_names = self.crontab.check()
            ic(task_names)
            for task_name in task_names: 
                ic("calling", task_name)
                task = self.task_dict[task_name]
                task.exec()
            time.sleep(1)
            
def my_excepthook(exc_type, exc_value, exc_traceback):
    tb = traceback.extract_tb(exc_traceback)
    project_root = os.path.abspath(os.path.dirname(__file__))
    filtered_tb = [frame for frame in tb if frame.filename.startswith(project_root)]
    print(f"{exc_type.__name__}: {exc_value}")
    for frame in filtered_tb:
        print(f'  File "{frame.filename}", line {frame.lineno}, in {frame.name}')
        print(f'    {frame.line}')

# sys.excepthook = my_excepthook

if __name__ == "__main__":
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
    main()