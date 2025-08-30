from pymirror.pmmodule import PMModule
from pymirror.pmlogger import _debug

class WindowManagerModule(PMModule):
	def __init__(self, pm, config):
		super().__init__(pm, config)
		self._window_manager = config.window_manager
		self.subscribe("RawKeyboardEvent")

	def render(self, force: bool = False) -> bool:
		pass

	def exec(self):
		pass

	def onRawKeyboardEvent(self, event):
		_debug("window_manager", event)
		if event.key_name == "KEY_TAB":
			if event.pressed and not event.repeat:
				self.pm.next_focus_module()
		else:
			if self.pm.focus_module:
				if event.pressed and not event.repeat:
					event.event = "KeyboardEvent"
					event.module = self.pm.focus_module.name
					_debug("... republishing event", event)
					self.pm.publish_event(event)