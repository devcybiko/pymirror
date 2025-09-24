# weather.py
# https://openweathermap.org/api/one-call-3#current

import copy
import subprocess

from pymirror.pmmodule import PMModule
from pymirror.utils.utils import expand_dict
from pymirror.pmcard import PMCard

class CliModule(PMCard):
	def __init__(self, pm, config):
		super().__init__(pm, config)
		self._cli = config.cli
		self.timer.set_timeout(self._cli.cycle_seconds * 1000)
		self.update("", "", "")  # Initialize with empty strings

	def exec(self) -> bool:
		is_dirty = super().exec()
		if self.timer.is_timedout():
			self.timer.reset() 
			self.stdout = subprocess.check_output(self._cli.command, shell=True, text=True).strip()
			context = {
				"title": self.name,
				"stdout": self.stdout,
				"command": self._cli.command,
			}
			dict = {
				"header": self._cli.header,
				"body": self._cli.body,
				"footer": self._cli.footer,
			}
			expand_dict(dict, context)
			self.update(dict.get('header'), dict.get('body'), dict.get('footer'))
			is_dirty = True
		return is_dirty

	def onEvent(self, event):
		pass			
