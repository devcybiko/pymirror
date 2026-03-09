from munch import DefaultMunch
from pmtaskmgr import PMTaskMgr
from glslib.strings import expand_string
from pmtask import PMTask
from glslib.logger import _debug, _error
import subprocess

class CpTask(PMTask):
    def __init__(self, pmtm: "PMTaskMgr", config):
        super().__init__(pmtm, config)
        self._task: DefaultMunch = config
        self.calendar_name = self._task.calendar_name

    def exec(self):
        cp_command = expand_string(self._task.cp_command, self._task.__dict__)
        print("Executing command:", cp_command,
            "from_file", self._task.from_file,
            "to_file", self._task.to_file
        )
        ## run the command
        result = subprocess.run(cp_command, shell=True, capture_output=True, text=True)
        print(result)
        if result.returncode != 0:
            _error(f"Command failed with return code {result.returncode}: {result.stderr}")
        else:
            _debug(f"Command executed successfully: {result.stdout}")
