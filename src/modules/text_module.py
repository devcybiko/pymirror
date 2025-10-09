import copy
from pymirror.pmmodule import PMModule
from utils.utils import SafeNamespace
from pymirror.comps.pmtextcomp import PMTextComp

class TextModule(PMModule):
	def __init__(self, pm, config: SafeNamespace):
		super().__init__(pm, config)
		self._textcomp = PMTextComp(self.bitmap.gfx, config.text, 0, 0, self.bitmap.width, self.bitmap.height)

	def render(self, force: bool = False) -> int:
		self._textcomp.render(self.bitmap)
		self._textcomp.clean()
		return True

	def exec(self):
		return self._textcomp.is_dirty()

