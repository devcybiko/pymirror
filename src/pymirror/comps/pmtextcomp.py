from models.text_model import TextModel
from pmgfxlib.pmgfx import PMGfx
from pymirror.pmrect import PMRect
from pymirror.pmtimer import PMTimer
from pymirror.comps.pmcomponent import PMComponent
from pmgfxlib import PMBitmap
from pymirror.utils.utils import SafeNamespace, non_null

class PMTextComp(PMComponent):
    def __init__(self, gfx: PMGfx, config: TextModel, x0: int = None, y0: int = None, width: int = None, height: int = None):
        super().__init__(gfx, config)
        self.text = self._config.text or ""
        self.gfx = gfx
        x0 = non_null(x0, 0)
        y0 = non_null(y0, 0)
        self.rect = PMRect(x0, y0, 0, 0)
        self.rect.width = non_null(width, 1)
        self.rect.height = non_null(height, 1)
        self.clip = non_null(self._config.clip, False)
        self.use_baseline = non_null(self._config.font_baseline, False)
        self.hscroll = non_null(self._config.hscroll, False)
        self._hscroll_delay = 100
        self._hscroll_timer = PMTimer(0)
        if self.hscroll:
            self._hscroll_timer = PMTimer(self._hscroll_delay)
        self._hoffset = 0
        self._dx = -10
        self._last_text = None

    def render(self, bitmap: PMBitmap) -> None:
        if not self.text:
            return
        gfx = bitmap.gfx_push(self.gfx)
        lines = gfx.font.text_split(self.text, self.rect, gfx.wrap)
        bitmap.text_box(self.rect, lines, valign=gfx.valign, halign=gfx.halign, clip=self.clip, use_baseline=self.use_baseline)
        bitmap.gfx_pop()
        self.clean()

    def update(self, text: str = None) -> None:
        self.text = text
        # if text is not None:
        #     self.text = text
        # else:
        #     self.text = self._last_text

    def is_dirty(self) -> bool:
        """Check if the text has changed since the last render."""
        # if self._hscroll_timer.is_timedout():
        #     self._hoffset += self._dx
        #     if self._hoffset < -self.rect.width:
        #         self._hoffset = self.rect.width
        #     self._hscroll_timer.set_timeout(self._hscroll_delay)
        #     return True
        return self.text != self._last_text

    def clean(self) -> bool:
        """Mark the text as clean, i.e., no changes since last render."""
        self._last_text = self.text
        return True