# weather.py
# https://openweathermap.org/api/one-call-3#current

from datetime import datetime
from dataclasses import dataclass
from models.module_model import ModuleModel
from pmgfxlib import PMBitmap
from pymirror.pmcard import PMCard
from pymirror.utils.utils import SafeNamespace
from pymirror.pmlogger import _debug, _print

@dataclass
class ForecastConfig:
    days: int = 3  # Number of days to forecast
    days_offset: int = 0  # Offset for the forecast days
    icon_size: str = "small"  # Size of the forecast icons (None, small, medium, large)
    lines: int = 3

class ForecastModule(PMCard):
    def __init__(self, pm, config: ModuleModel):
        super().__init__(pm, config)
        self._forecast = config.forecast
        self.subscribe("WeatherForecastEvent")
        self.dirty = False
        self.weather_response = None

    def _load_icon(self, icon_code: str, size: str, width: int = None, height: int = None, scale: str = None) -> PMBitmap:
        # Load the weather icon bitmap based on the icon code and size
        size = {"small": "", "medium": "@2x", "large": "@4x"}.get(size, "")
        icon_path = f"./weather_icons/{icon_code}{size}.png"
        _debug(f"Loading weather icon from {icon_path}")
        return PMBitmap().load(icon_path, width=width, height=height, scale=scale)

    def _render_text(self, c: SafeNamespace) -> None:
        if self.weather_response == None:
            return
        text_x0 = c.cell_width * c.col
        text_y0 = c.y0 + c.new_icon_height
        msg = datetime.fromtimestamp(self.weather_response.daily[c.id].dt).strftime("%A")
        msg += f", {self.weather_response.daily[c.id].temp.day}°F"
        msg += f"\n{self.weather_response.daily[c.id].weather[0].description}"
        c.text_rect = (text_x0, text_y0, text_x0 + c.cell_width - 1, text_y0 + c.text_height - 1)
        _debug(f"Forecast text rect: {c.text_rect}, msg: {msg}")
        self.bitmap.text_box(
            c.text_rect,
            msg,
            valign="center",
            halign="center"
        )

    def _select_row_config(self, c: SafeNamespace) -> None:
        dims = {
            1: ((0,),),
            2: ((0,1),),
            3: ((0, 1),(2,)),
            4: ((0, 1), (2, 3),),
            5: ((0, 1, 2), (3, 4),),
            6: ((0, 1, 2), (3, 4, 5),),
            7: ((0, 1, 2, 3), (4, 5, 6),),
            8: ((0, 1, 2), (3, 4, 5), (6, 7),),
            9: ((0, 1, 2), (3, 4, 5), (6, 7, 8),)
        }
        c.rows = dims[c.days]
        _debug(f"Forecast rows: {self._forecast.days}: {c.rows}")
        c.n_rows = len(c.rows)

    def _initial_values(self, c: SafeNamespace) -> None:
        c.w = self.bitmap.width
        c.h = self.bitmap.height
        c.row = 0
        c.x0, c.y0 = 0, 0 # top-left corner of cell
        c.px, c.py = 4, 4 # icon padding
        c.days = min(self._forecast.days, len(self.weather_response.daily), 9)
        c.text_height = (self.bitmap.gfx.font.height) * self._forecast.lines
        self._select_row_config(c)
        c.cell_height = c.h // c.n_rows
        c.max_icon_height = c.cell_height - c.text_height - c.py * 2
        _debug(f"Forecast cell_height: {c.cell_height}")
        _debug(f"Forecast max_icon_height: {c.max_icon_height}")

    def _render_icon(self, c: SafeNamespace):
        _debug(f"render icon {c.id} for {c.max_icon_width}x{c.max_icon_height}")
        bm = self._load_icon(
            self.weather_response.daily[c.id].weather[0].icon,
            self._forecast.icon_size,
            width=c.max_icon_width,
            height=c.max_icon_height,
            scale="fit"
        )
        c.new_icon_height = bm._img.height + c.py * 2
        c.new_icon_width = bm._img.width + c.px * 2
        c.rx = c.w - c.cell_width * c.n_cols
        c.ry = c.h - c.cell_height * c.n_rows
        c.x0 = c.cell_width * c.col
        c.y0 = c.cell_height * c.row
        c.icon_x0 = c.x0 + c.px + (c.cell_width - c.new_icon_width) // 2
        c.icon_y0 = c.y0 + c.py
        _debug(f"Forecast icon {c.id}: {bm._img.size}, rx={c.rx}, ry={c.ry}, x0={c.x0}, y0={c.y0}, col={c.col}, row={c.row}")
        self.bitmap.paste(bm, c.icon_x0, c.icon_y0)

    def render(self, force: bool = False) -> bool:
        if not (self.dirty or force):
            return False
        if not self.weather_response:
            return False
        self.bitmap.clear()
        c = SafeNamespace()
        self._initial_values(c)
        for row_ids in c.rows:
            c.col = 0
            c.n_cols = len(row_ids)
            c.cell_width = c.w // c.n_cols
            c.max_icon_width = c.cell_width - c.px * 2
            for id in row_ids:
                c.id = id
                self._render_icon(c)
                self._render_text(c)
                # self.bitmap.rect(self.gfx, c.text_rect, fill=None)
                c.col += 1
            c.row += 1
        self.dirty = False
        return False
    
    def onWeatherForecastEvent(self, event):
        self.dirty = True
        self.weather_response = event.data

    def exec(self) -> bool:
        return self.dirty # state changed