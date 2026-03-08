from datetime import datetime
from pymirror.pmmodule import PMModule
from pymirror.pmtimer import PMTimer

class FpsModule(PMModule):
	def __init__(self, pm, config):
		super().__init__(pm, config)
		self.last_time = datetime.now()
		self.timer = PMTimer("1s")

	def render(self, force: bool = False) -> bool:
		now = datetime.now()
		delta = now - self.last_time
		self.last_time = now
		fps = 1 / delta.total_seconds() if delta.total_seconds() > 0 else 0
		self.bitmap.clear()
		self.bitmap.text_box((0, 0, self.bitmap.width-1, self.bitmap.height-1), f"FPS: {fps:.2f}", valign=self._moddef.valign, halign=self._moddef.halign)
		return True

	def exec(self):
		# if self.timer.is_timedout():
		# 	self.timer.reset()
		# 	return True
		return True

	def onEvent(self, event):
		pass			

