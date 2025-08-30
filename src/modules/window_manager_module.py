from pymirror.pmmodule import PMModule
from pymirror.pmlogger import _debug

class WindowManagerModule(PMModule):
	def __init__(self, pm, config):
		super().__init__(pm, config)
		self._window_manager = config.window_manager
		self.name = self._window_manager.name
		self.alerts = config.alerts or []
		if type(self.alerts) is not list:
			self.alerts = [self.alerts]
		self.window_managertab = WindowManagertab([alert.window_manager for alert in self.alerts])

	def render(self, force: bool = False) -> bool:
		pass

	def exec(self):
		alert_indexes = self.window_managertab.check()
		if not alert_indexes:
			return
		for i in alert_indexes:
			alert = self.alerts[i]
			_debug(f"Alert triggered: {alert.event}")
			self.publish_event(alert.event)
		return False