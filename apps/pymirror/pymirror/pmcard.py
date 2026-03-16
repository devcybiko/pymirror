from pymirror.pmmodule import ModuleConfig
from modules.text_module import TextConfig
from components.pm_text_component import PMTextComponent
from pymirror.pmmodule import PMModule
from pmutils import non_null

from dataclasses import dataclass

@dataclass
class CardConfig:
    header: TextConfig = None
    body: TextConfig = None
    footer: TextConfig = None
    timeout: int = 1

class PMCard(PMModule):
    def __init__(self, pm, config: ModuleConfig):
        super().__init__(pm, config)
        if getattr(self._config, "card", None) is None:
            self._config.card = {}
        self._card: CardConfig = pm.configurator.from_dict(self._config.card, CardConfig)
        self._card.header = non_null(self._card.header, TextConfig())
        self._card.body = non_null(self._card.body, TextConfig())
        self._card.footer = non_null(self._card.footer, TextConfig())
        self._header = self._make_header()
        self._footer = self._make_footer()
        self._body = self._make_body()

    def _make_header(self):
        width = self.bitmap.width
        height = non_null(self._card.header.height, self.bitmap.gfx.font.height, 1)
        return PMTextComponent(self.bitmap.gfx, self._card.header, width=width, height=height)

    def _make_footer(self):
        footer_height = non_null(self._card.footer.height, self.bitmap.gfx.font.height, 1)
        y0 = self.bitmap.height - footer_height
        width = self.bitmap.width
        return PMTextComponent(self.bitmap.gfx, self._card.footer, y0=y0, width=width)

    def _make_body(self):
        y0 = self._header.height
        height = self.bitmap.height - self._header.height - self._footer.height
        width = self.bitmap.width
        return PMTextComponent(self.bitmap.gfx, self._card.body, y0=y0, width=width, height=height)

    def set_header(self, text: str) -> None:
        self._header.update(text)

    def set_body(self, text: str) -> None:
        self._body.update(text)

    def set_footer(self, text: str) -> None:
        self._footer.update(text)
        
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
