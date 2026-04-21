import copy

from munch import DefaultMunch
from pymirror.pmtile import PMTile
from components.pm_text_component import PMTextComponent

from dataclasses import dataclass
from mixins.font_mixin import FontMixin
from mixins.text_mixin import TextMixin

@dataclass
class TextConfig(TextMixin, FontMixin):
    text: str = None
    height: int = None

class TextTile(PMTile):
	def __init__(self, pm, config: DefaultMunch):
		super().__init__(pm, config)
		self._text = pm.configurator.from_dict(config.text, TextConfig)
		self._textcomp = PMTextComponent(self.bitmap.gfx, self._text, 0, 0, self.bitmap.width, self.bitmap.height)

	def render(self, force: bool = False) -> int:
		self._textcomp.render(self.bitmap)
		self._textcomp.clean()
		return True

	def exec(self):
		return self._textcomp.is_dirty()

