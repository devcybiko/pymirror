from datetime import datetime
from pymirror.pmcard import PMCard

class AlertModule(PMCard):
	def __init__(self, pm, config):
		super().__init__(pm, config)
		self._alert = config.alert
		## update the card with initial values
		self.update(self._alert.header, self._alert.body, self._alert.footer)
		## set the timeout for the alert, if any
		self.timer.set_timeout(self._alert.timeout)
		## disable the alert if the timeout is 0 or less
		## this means the alert is not active
		self.disabled = self._alert.timeout < 0


	def exec(self) -> bool:
		## has there been a change in the alert text?
		is_dirty = super().exec()
		if self.timer.is_timedout(): 
			## the timer has expired
			## disable the alert (hiding it)
			## and publish an event to refresh the display
			self.disabled = True
			self.update(None, None, None)
			self.clean()  # mark the alert as clean
			self.publish_event({"event": "PyMirrorEvent", "refresh": True})
		return is_dirty

	def onEvent(self, event) -> None:
		self.disabled = False
		self.update(event.header, event.body, event.footer)
		self.timer.set_timeout(event.timeout, event.timeout)
