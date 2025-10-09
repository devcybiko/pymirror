import copy
from dataclasses import dataclass

from configs.card_config import CardConfig
from configs.module_config import ModuleConfig
from configs.text_config import TextConfig
from pmgfxlib.pmgfx import PMGfx
from pymirror.pmrect import PMRect
from pymirror.comps.pmtextcomp import PMTextComp
from pymirror.pmmodule import PMModule
from utils.utils import from_dict, non_null, pprint

class PMCard(PMModule):
    def __init__(self, pm, config: ModuleConfig):
        super().__init__(pm, config)
        if self._config.card == None:
            self._config.card = CardConfig()
        self._card = self._config.card
        self._card.header = non_null(self._card.header, TextConfig())
        self._card.body = non_null(self._card.body, TextConfig())
        self._card.footer = non_null(self._card.footer, TextConfig())
        self._header = self._make_header()
        self._footer = self._make_footer()
        self._body = self._make_body()

    def _make_header(self):
        width = self.bitmap.width
        height = non_null(self._card.header.height, self.bitmap.gfx.font.height, 1)
        return PMTextComp(self.bitmap.gfx, self._card.header, width=width, height=height)

    def _make_footer(self):
        footer_height = non_null(self._card.footer.height, self.bitmap.gfx.font.height, 1)
        y0 = self.bitmap.height - footer_height
        width = self.bitmap.width
        return PMTextComp(self.bitmap.gfx, self._card.footer, y0=y0, width=width)

    def _make_body(self):
        y0 = self._header.height
        height = self.bitmap.height - self._header.height - self._footer.height
        width = self.bitmap.width
        return PMTextComp(self.bitmap.gfx, self._card.body, y0=y0, width=width, height=height)

    def update(self, header: str, body: str, footer: str) -> None:
        self._header.update(header)
        self._body.update(body)
        self._footer.update(footer)

    def clean(self) -> None:
        """Mark the card as clean, i.e. no changes since last render"""
        self._header.clean()
        self._body.clean()
        self._footer.clean()
        self.dirty = False

    def is_dirty(self) -> bool:
        dirty = (
            self.dirty
            or self._header.is_dirty()
            or self._body.is_dirty()
            or self._footer.is_dirty()
        )
        return dirty

    def render(self, force: bool = False) -> bool:
        self.bitmap.clear()
        self._header.render(self.bitmap)
        self._body.render(self.bitmap)
        self._footer.render(self.bitmap)
        self.render_focus()
        self.clean()
        return True

    def exec(self) -> bool:
        is_dirty = self.is_dirty()
        return is_dirty
