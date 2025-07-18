from datetime import datetime
from pymirror.pmmodule import PMModule

class Fps(PMModule):
	def __init__(self, pm, config):
		super().__init__(pm, config)
		self.last_time = datetime.now()
		self._fps = config.fps

	def render(self, force: bool = False) -> bool:
		now = datetime.now()
		delta = now - self.last_time
		self.last_time = now
		fps = 1 / delta.total_seconds() if delta.total_seconds() > 0 else 0
		text_box = self.bitmap.text_box
		self.bitmap.clear()
		text_box(self.gfx, f"FPS: {fps:.2f}", (0,0,self.gfx.width,self.gfx.height), valign=self._fps.valign, halign=self._fps.halign)
		return True

	def exec(self):
		return True

	def onEvent(self, event):
		pass			

