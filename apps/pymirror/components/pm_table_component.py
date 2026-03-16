from pmgfxlib.pmgfx import PMGfx
from pymirror.pmrect import PMRect
from components.pm_component import PMComponent
from pmgfxlib import PMBitmap
from pmutils import non_null

from dataclasses import dataclass
from mixins.font_mixin import FontMixin
from mixins.text_mixin import TextMixin

@dataclass
class TableConfig(TextMixin, FontMixin):
    header: list[str] = None
    rows: int = None
    cols: int = None
    height: int = None
    width: int = None
    row_height: int = None
    col_width: int = None
    reversed: bool = False

class PMCell:
    def __init__(self, value=None, format=None, halign="center", valign="center", bg_color="#333", text_color="#fff"):
        self.value = value 
        self.format = format
        self.halign = halign
        self.valign = valign
        self.bg_color = bg_color
        self.text_color = text_color

    def _format(self, value):
        if self.format:
            try:
                return self.format.format(value)
            except (ValueError, TypeError):
                print(f"Error formatting {type(value)}value '{value}' with format '{self.format}' - assuming string")
                return str(value)
        return str(value)

    def render(self, bm: PMBitmap, x: int, y: int, w: int, h: int, value):
        if value is not None:
            text = self._format(value)
            bm.gfx.text_bg_color = self.bg_color
            bm.gfx.text_color = self.text_color
            bm.text_box((x, y, x + w, y + h), text, halign=self.halign, valign=self.valign)
            bm.rectangle((x, y, x + w, y + h), fill=None)

class PMRow:
    def __init__(self, cells: list):
        self.cells = cells

    def render(self, bitmap: PMBitmap) -> None:
        pass

class PMTableComponent(PMComponent):
    def __init__(self, gfx: PMGfx, config: TableConfig, x0: int = None, y0: int = None, width: int = None, height: int = None):
        super().__init__(gfx, config)
        self._table = config
        self.gfx = gfx
        self.rect = PMRect(x0, y0, 0, 0)
        self.rect.width = non_null(width, 100)
        self.rect.height = non_null(config.height, height, 100)
        self.set_rows([[50.509] * self._table.cols] * self._table.rows)
        self.default_cell = PMCell(format="${:.2f}", halign="right", valign="center")
        self.header_cell = PMCell(halign="center", valign="center", text_color="#ff0", bg_color="#080")
        self._dirty = True

    def is_dirty(self):
        return self._dirty

    def clean(self):
        self._dirty = False

    def set_rows(self, rows: list):
        self.rows = rows

    def _render_cell(self, bm: PMBitmap, x: int, y: int, w: int, h: int, value):
        if isinstance(value, PMCell):
            value.render(bm, x, y, w, h, value.value)
        else:
            self.default_cell.render(bm, x, y, w, h, value)

    def _render_header_cell(self, bm: PMBitmap, x: int, y: int, w: int, h: int, value):
        if isinstance(value, PMCell):
            value.render(bm, x, y, w, h, value.value)
        else:
            self.header_cell.render(bm, x, y, w, h, value)

    def _render_header_row(self, bm: PMBitmap, y: int, h: int, header_row):
        cell_width = self.rect.width // self._table.cols
        x = 0
        for header_value in header_row:
            self._render_header_cell(bm, x, y, cell_width, h, header_value)
            x += cell_width

    def _render_row(self, bm: PMBitmap, y: int, h: int, row):
        cell_width = self._table.col_width or (self.rect.width // self._table.cols)
        x = 0
        for col in row:
            self._render_cell(bm, x, y, cell_width, h, col)
            x += cell_width

    def render(self, bm: PMBitmap) -> None:
        # Render the table to the bitmap
        bm.gfx_push(self.gfx)
        rows = self.rows
        if self._table.reversed:
            rows = reversed(self.rows)
        cell_height = self._table.row_height or (self.rect.height // self._table.rows)
        y = 0
        if self._table.header:
            self._render_header_row(bm, y, cell_height, self._table.header)
            y += cell_height
        for row in rows:
            if y + cell_height > self.rect.height:
                break
            self._render_row(bm, y, cell_height, row)
            y += cell_height
        bm.gfx_pop()
