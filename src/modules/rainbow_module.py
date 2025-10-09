from datetime import datetime
from pymirror.pmmodule import PMModule
from pymirror.pmscreen import PMGfx
from pmlogger import _debug, _trace

class RainbowModule(PMModule):
	def __init__(self, pm, config):
		super().__init__(pm, config)
		self._rainbow = config.rainbow
		self.first_time = True

	def render(self, force: bool = False) -> bool:
		_debug(f"Rainbow module render at {datetime.now()}")
		self.bitmap.clear()
		gfx = self.gfx
		x = gfx.x0
		y = gfx.y0
		width = int(gfx.x1 - gfx.x0)
		height = int(gfx.y1 - gfx.y0)
		dw = width / 3 / 256
		dx = 0
		x = int(dx)
		for r in range(256):
			gfx.color = f"#{r:02x}0000"  # Red to black
			gfx.color = "#fff"
			self.bitmap.line(gfx, (x, y, x+1, y + height))
			dx += dw
			x = int(dx)
		for g in range(256):
			gfx.color = f"#00{g:02x}00"  # Green to black
			self.bitmap.line(gfx, (x, y, x+1, y + height))
			dx += dw
			x = int(dx)
		for b in range(256):
			gfx.color = f"#0000{b:02x}"  # Blue to black
			self.bitmap.line(gfx, (x, y, x+1, y + height))
			dx += dw
			x = int(dx)
		return True

	def exec(self):
		_debug(f"Rainbow module exec at {datetime.now()}")
		if self.first_time:
			self.first_time = False
			return 1
		return 1

	def onEvent(self, event):
		pass

