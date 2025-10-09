from pymirror.pmmodule import PMModule
from utils.utils import SafeNamespace
from pmgfxlib.pmbitmap import PMBitmap

class PhotoModule(PMModule):
	def __init__(self, pm, config: SafeNamespace):
		super().__init__(pm, config)
		self._photo = config.photo
		self.photo = PMBitmap().load(self._photo.path)
		if self._photo.scale:
			self.photo.scale(self.bitmap.gfx.width, self.bitmap.gfx.height, self._photo.scale)
		self.dirty = True
	
	def render(self, force: bool = False) -> bool:
		self.bitmap.clear()
		## scale the image to fit the bitmap
		x0 = 0
		y0 = 0
		if self._photo.valign == "top":
			y0 = 0
		elif self._photo.valign == "bottom":
			y0 = self.bitmap.gfx.height - self.photo.gfx.height
		elif self._photo.valign == "center":
			y0 = (self.bitmap.gfx.height - self.photo.gfx.height) // 2
		if self._photo.halign == "left":
			x0 = 0
		elif self._photo.halign == "right":
			x0 = self.bitmap.gfx.width - self.photo.gfx.width
		elif self._photo.halign == "center":
			x0 = (self.bitmap.gfx.width - self.photo.gfx.width) // 2
		self.bitmap.paste(self.photo, x0, y0)
		self.dirty = False
		return True

	def exec(self):
		return self.dirty

