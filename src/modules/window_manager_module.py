from pymirror.pmmodule import PMModule
from pymirror.pmlogger import _debug

class WindowManagerModule(PMModule):
	def __init__(self, pm, config):
		super().__init__(pm, config)
		self._window_manager = config.window_manager

	def render(self, force: bool = False) -> bool:
		pass

	def exec(self):
		pass

	def _find_focus_module_n(self):
		mod_n = None
			for i in range(0, len(self.pm.modules)):
				if self.focus_module == self.pm.modules[i]
					return i
		return None
	
	def onRawKeyboardEvent(self, event):
		mod_n = 
		if event.key_name == "TAB":
