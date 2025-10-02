import os
from pymirror.pmmodule import PMModule
from pymirror.pmlogger import _debug

class PymirrorControllerModule(PMModule):
	def __init__(self, pm, config):
		super().__init__(pm, config)
		self.subscribe("PyMirrorEvent")

	def render(self, force: bool = False) -> bool:
		return False

	def exec(self):
		return False

	def onEvent(self, event):
		_debug(f"Received event: {event}")
		if event.event != "PyMirrorEvent":
			_debug(f"Received unknown event type: {event.type}")
			return
		
		if event.debug in [True, False, "true", "false", "on", "off"]:
			_debug(f"Received debug event: {event.debug}")
			self.pm.debug = event.debug in [True, "true", "on"]
			self.pm.full_render()

		if event.refresh in [True, False, "true", "false", "on", "off"]:
			_debug(f"Received refresh event: {event.refresh}")
			## clear the screen on the next iteration
			self.pm._clear_screen = event.refresh in [True, "true", "on"]

		if event.purge: 
			_debug(f"Received purge event: {event.refresh}")
			os.system("rm -f caches/*")
			os.system("rm -f src/pmserver/static/output.*")

		if event.remote_display in [True, False, "true", "false", "on", "off"]:
			if event.remote_display in [False, "false", "off"]:
				_debug("Received remote display event: Off")
				# turn off the screen output (used by the web display)
				self.screen._screen.output_file = None
			else:
				_debug("Received remote display event: True")
				# turn on the screen output (used by the web display)
				self.screen._screen.output_file = "./src/pmserver/static/output.jpg"

		if event.restart: 
			_debug(f"Received restart event: {event.restart}")
			raise Exception("Terminating for restart")

		if event.reboot: 
			_debug(f"Received reboot event: {event.reboot}")
			os.system("sudo reboot")

		if event.error != None: 
			raise Exception(f"PyMirrorController received error event:\n{event.error}")

