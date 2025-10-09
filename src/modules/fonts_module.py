import os
from pymirror.pmmodule import PMModule
from utils.utils import SafeNamespace
from pymirror.pmlogger import _debug, _error

class FontsModule(PMModule):
	def __init__(self, pm, config: SafeNamespace):
		super().__init__(pm, config)
		self._text = config.fonts
		self.text = None
		self.font_list = self._load_font_list()
		self.font_item = 0
		self.max_items = 10
		self.timer.set_timeout(self._text.delay_ms)

	def _load_font_list(self):
		"""Load the list of available fonts from fontlist.txt"""
		font_list = []
		# Get the path to fontlist.txt relative to the project root
		with open("./fontlist.txt", 'r') as f:
			for line in f:
				_debug(line)
				font_file = line.strip().split(":")[0].strip()  # Remove comments and whitespace
				font_name = os.path.basename(font_file).split('.')[0]  # Get the font name without extension
				# test if font_file exists
				if os.path.isfile(font_file):
					font_list.append(font_name)
				else:
					_error(f"Font file {font_file} not found.")
		# return sorted(font_list)
		return font_list

	def render(self, force: bool = False) -> int:
		gfx = self.bitmap.gfx_push()
		text = self.bitmap.text
		self.bitmap.clear()
		gfx.text_color = "#fff"  # Set text color to white
		for i in range(self.max_items):
			n = (self.font_item + i) % len(self.font_list)
			gfx.set_font(self.font_list[n], gfx.font_size)
			text(self.font_list[n], 0, 0 + i * gfx.font_size)
			# color = color_to_tuple(gfx.text_color)
			# color = _mul(color, (0.90, 0.90, 0.90))
			# gfx.text_color = color_from_tuple(color)
		gfx = self.bitmap.gfx_pop()
		return True

	def exec(self):
		if self.timer.is_timedout():
			self.timer.reset()
			self.font_item += 3
			return True
		return False

