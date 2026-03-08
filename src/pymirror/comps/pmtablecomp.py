from configs.table_config import TableConfig
from pmgfxlib.pmgfx import PMGfx
from pymirror.pmrect import PMRect
from pymirror.comps.pmcomponent import PMComponent
from pmgfxlib import PMBitmap
from pmutils import non_null

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

class PMTableComp(PMComponent):
    def __init__(self, gfx: PMGfx, config: TableConfig, x0: int = None, y0: int = None, width: int = None, height: int = None):
        super().__init__(gfx, config)
        print(44, config)
        self._table = config
        self.gfx = gfx
        self.rect = PMRect(x0, y0, 0, 0)
        self.rect.width = non_null(width, 100)
        self.rect.height = non_null(config.height, height, 100)
        self.set_rows([[50.509] * self._table.cols] * self._table.rows)
        self.default_cell = PMCell(format="${:.2f}", halign="right", valign="center")
        self.header_cell = PMCell(halign="center", valign="center", text_color="#f00", bg_color="#555")
        self._table.has_header = True
        self._dirty = True

    def is_dirty(self):
        return self._dirty

    def clean(self):
        self._dirty = False

    def set_rows(self, rows: list):
        self.rows = rows

    def _render_cell(self, bm: PMBitmap, x: int, y: int, w: int, h: int, row_n: int, col_n: int):
        value = self.rows[row_n][col_n]
        if isinstance(value, PMCell):
            value.render(bm, x, y, w, h, value.value)
        else:
            self.default_cell.render(bm, x, y, w, h, self.rows[row_n][col_n])

    def _render_header_cell(self, bm: PMBitmap, x: int, y: int, w: int, h: int, row_n: int, col_n: int):
        value = self.rows[row_n][col_n]
        if isinstance(value, PMCell):
            value.render(bm, x, y, w, h, value.value)
        else:
            self.header_cell.render(bm, x, y, w, h, self.rows[row_n][col_n])

    def _render_header_row(self, bm: PMBitmap, y: int, h: int, row_n: int):
        cell_width = self.rect.width // self._table.cols
        for col_n in range(self._table.cols):
            x = col_n * cell_width
            w = cell_width
            self._render_header_cell(bm, x, y, w, h, row_n, col_n)

    def _render_row(self, bm: PMBitmap, y: int, h: int, row_n: int):
        cell_width = self.rect.width // self._table.cols
        for col_n in range(self._table.cols):
            x = col_n * cell_width
            w = cell_width
            self._render_cell(bm, x, y, w, h, row_n, col_n)

    def render(self, bm: PMBitmap) -> None:
        # Render the table to the bitmap
        bm.gfx_push(self.gfx)
        cell_height = self._table.row_height or (self.rect.height // self._table.rows)
        y = 0
        row_n = 0
        if self._table.has_header:
            self._render_header_row(bm, y, cell_height, row_n)
            y += cell_height
        while row_n < len(self.rows):
            if y + cell_height > self.rect.height:
                break
            if self._table.has_header and row_n == 0:
                ## we already rendered the header row
                row_n += 1
                continue
            actual_row = row_n if not self._table.reversed else (len(self.rows) - 1 - row_n)
            self._render_row(bm, y, cell_height, actual_row)
            y += cell_height
            row_n += 1
        bm.gfx_pop()
