from random import random

from pymirror.pmmodule import PMModule
from pymirror.pmtimer import PMTimer
from glslib.rects import _height, _str_to_rect, _width
from pmgfxlib.pmbitmap import PMBitmap
from glslib.logger import _debug
from pymirror.pmrect import PMRect
import os

from dataclasses import dataclass

@dataclass
class SlideshowConfig:
    folder: str
    scale: str = "fill"
    valign: str = "center"
    halign: str = "center"
    interval_time: str = "60s"
    randomize: bool = True
    frame: str = None
    rect: str = None

class SlideshowModule(PMModule):
	def __init__(self, pm, config):
		super().__init__(pm, config)
		self._slideshow: SlideshowConfig = pm.configurator.from_dict(config.slideshow, SlideshowConfig)
		self.alt_rect = PMRect(*_str_to_rect(self._slideshow.rect))
		self.photo_number = 0
		self.photos = self.load_folder(self._slideshow.folder)
		self._randomize_list()
		self.timer = PMTimer(self._slideshow.interval_time)
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
			self.photos = sorted(self.photos, key=lambda x: random())

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
		self.render_focus()
		self.dirty = False
		return False
	
	def exec(self):
		if self.timer.is_timedout():
			self.timer.reset()
			self.photo_number = (self.photo_number + 1) % len(self.photos)
			self.dirty = True
		return self.dirty

	def onKeyboardEvent(self, event):
		_debug("slideshow_module", event)
		if event.key_name == "KEY_LEFT":
			self.photo_number = (self.photo_number + len(self.photos) -1) % len(self.photos)
			self.timer.reset()
			self.dirty = True
		if event.key_name == "KEY_RIGHT":
			self.photo_number = (self.photo_number + 1) % len(self.photos)
			self.timer.reset()
			self.dirty = True
		pass