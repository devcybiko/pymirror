import copy

from munch import DefaultMunch
from pymirror.pmmodule import PMModule
from pymirror.components.pmtextcomp import PMTextComp

from dataclasses import dataclass
from configs.mixins.font_mixin import FontMixin
from configs.mixins.text_mixin import TextMixin

@dataclass
class TextConfig(TextMixin, FontMixin):
    text: str = None
    height: int = None

class TextModule(PMModule):
	def __init__(self, pm, config: DefaultMunch):
		super().__init__(pm, config)
		self._text = pm.configurator.from_dict(config.text, TextConfig)
		self._textcomp = PMTextComp(self.bitmap.gfx, self._text, 0, 0, self.bitmap.width, self.bitmap.height)

	def render(self, force: bool = False) -> int:
		self._textcomp.render(self.bitmap)
		self._textcomp.clean()
		return True

	def exec(self):
		return self._textcomp.is_dirty()

