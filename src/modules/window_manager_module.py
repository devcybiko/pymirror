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

	def onRawKeyboardEvent(self, event):
		mod_n = self._find_focus_module_n
		if event.key_name == "TAB":
