from random import random, randint, choice  # Import the functions you need
from modules.photo_module import PhotoModule
from pymirror.pmmodule import PMModule
from pymirror.pmtimer import PMTimer
from pymirror.utils import SafeNamespace, _height, _str_to_rect, _width
from pmgfxlib.pmbitmap import PMBitmap
from pymirror.pmlogger import _debug
from pymirror.pmrect import PMRect
import os

class SlideshowModule(PMModule):
	def __init__(self, pm, config: SafeNamespace):
		super().__init__(pm, config)
		self._slideshow = config.slideshow
		self.alt_rect = PMRect(*_str_to_rect(self._slideshow.rect))
		self.photo_number = 0
		self.photos = self.load_folder(self._slideshow.folder)
		self.timer = PMTimer(self._slideshow.interval_secs * 1000)
		self.dirty = False
		self.path = None
		self.frame_bm = None
		if self._slideshow.frame:
			self.frame_bm = PMBitmap().load(self._slideshow.frame)
			self.frame_bm.scale(self.bitmap.width, self.bitmap.height, "stretch")
		self.subscribe("KeyboardEvent")

	def _randomize_list(self):
		if self._slideshow.randomize:
			## randomize the self.photos list
			

	def load_folder(self, folder: str):
		""" Load all photo paths from the given folder """
		paths = []
		for photo_path in os.listdir(folder):
			path = os.path.join(folder, photo_path)
			paths.append(path)
		_debug(f"Loaded {len(paths)} photos from {folder}")
		return paths

	def render(self, force: bool = False) -> bool:
		img_width, img_height = int(self.bitmap.width * _width(self.alt_rect)), int(self.bitmap.height * _height(self.alt_rect))
		img_bm = PMBitmap().load(self.photos[self.photo_number], img_width, img_height, self._slideshow.scale)
		new_x0 = (self.bitmap.width - img_bm.width) // 2
		new_y0 = (self.bitmap.height - img_bm.height) // 2
		self.bitmap.clear()
		self.bitmap.paste(img_bm, new_x0, new_y0, img_bm)
		if self.frame_bm:
			self.bitmap.paste(self.frame_bm, 0, 0, self.frame_bm) ## overlay the frame
		self.dirty = False
		return False
	
	def exec(self):
		if self.timer.is_timedout():
			self.timer.reset()
			if self._slideshow.randomize:
				self.photo_number = randint(0, len(self.photos) - 1)
			else:
				self.photo_number = (self.photo_number + 1) % len(self.photos)
			self.dirty = True
		return self.dirty

	def onKeyboardEvent(self, event):
		print("slideshow_module", event)
		if event.key_name == "KEY_LEFT":
			self.photo_number = (self.photo_number + len(self.photos) -1) % len(self.photos)
			self.timer.reset()
			self.dirty = True
		if event.key_name == "KEY_RIGHT":
			self.photo_number = (self.photo_number + 1) % len(self.photos)
			self.timer.reset()
			self.dirty = True
		pass