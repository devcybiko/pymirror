import copy
from dataclasses import dataclass

from pmgfxlib.pmgfx import PMGfx
from pymirror.pmrect import PMRect
from pymirror.comps.pmtextcomp import PMTextComp
from pymirror.pmmodule import PMModule
from pymirror.utils import from_dict, non_null

class PMCard(PMModule):
    def __init__(self, pm, config):
        super().__init__(pm, config)
        self._card = self._config.card
        self._header = PMTextComp(self.bitmap.gfx, self._card.header, width=self.bitmap.width, height=non_null(self._card.header.height, self.bitmap.gfx.font.height, 1))
        self._footer = PMTextComp(self.bitmap.gfx, self._card.footer, y0=self.bitmap.height - non_null(self._card.footer.height, self.bitmap.gfx.font.height, 0), width=self.bitmap.width)
        self._body = PMTextComp(self.bitmap.gfx, self._card.body, y0=self._header.height, height=self.bitmap.height - self._header.height - self._footer.height, width=self.bitmap.width)

    def update(self, header: str, body: str, footer: str) -> None:
        self._header.update(header)
        self._body.update(body)
        self._footer.update(footer)

    def clean(self) -> None:
        """Mark the card as clean, i.e. no changes since last render"""
        self._header.clean()
        self._body.clean()
        self._footer.clean()

    def is_dirty(self) -> bool:
        dirty = (
            self.dirty
            self._header.is_dirty()
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
