from dataclasses import dataclass, field

from datetime import datetime

from glslib.strftime import strftime_by_example
from pmgfxlib.pmgfx import PMGfx
from pymirror.pmrect import PMRect
from components.pm_component import PMComponent
from pmgfxlib import PMBitmap
from glslib.tuples import _add
from glslib.logger import _die, _debug, _print

@dataclass
class PMPlotAxisConfig:
    min: float
    max: float
    margin: int = 40
    color: str = "blue"
    tic_interval: float = 1.0
    n_tics: int = None
    tic_height: int = 10
    format: str = "{:.2f}"
    line_width: int = 2
    data: list = field(default_factory=list) # x_axis only
    title: str = "AXIS"
    _size: float = None

@dataclass
class PMPlotTraceConfig:
    data: list
    color: str = "blue"
    label_color: str = "black"
    line_width: int = 2
    width: int = 20
    x_offset: int = 0
    type: str = "line" # or "bar"
    format: str = "{:.2f}"
    label_format: str = None
    data: list = field(default_factory=list) 
    column: str = None   
    _width: str = None # scale bar width by trip days

@dataclass
class PMPlotComponentConfig:
    x_axis: PMPlotAxisConfig
    y_axis: PMPlotAxisConfig
    rect: PMRect
    title: str = None

@dataclass
class PMPointConfig:
    y: float
    color: str = None
    width: int = None
    line_width: int = None
    label: str = None
    halign: str = "center"
    _width: float = None # scaled relative to x-axis

class PMPlotComponent(PMComponent):
    def __init__(
        self,
        gfx: PMGfx,
        config: PMPlotComponentConfig,
    ):
        super().__init__(gfx, config)
        _debug(f"Initializing PMPlotComp with config: {config}")
        self._plot = config
        self.gfx = gfx
        self.rect = config.rect
        self._dirty = True
        self.x_axis = self._plot.x_axis
        self.y_axis = self._plot.y_axis
        self.x_axis._size = self.rect.width - self.x_axis.margin * 2
        self.y_axis._size = self.rect.height - self.y_axis.margin * 2
        self.traces = []


    def is_dirty(self):
        return self._dirty

    def clean(self):
        self._dirty = False

    def add_trace(self, trace_config: PMPlotTraceConfig, data=[]):
        _debug(f"Adding trace with data: {trace_config.data}, color: {trace_config.color}, line_width: {trace_config.line_width}, format: {trace_config.format}")
        if data:
            trace_config.data = data
        self.traces.append(trace_config)
        for i, point in enumerate(trace_config.data):
            if type(point) != PMPointConfig:
                trace_config.data[i] = PMPointConfig(y=point)
        self._dirty = True

    def _to_float(self,val):
        if val is None:
            return None
        if isinstance(val, datetime):
            return val.timestamp()
        return float(val)

    def _sx(self, v):
        return self._scale(v, self.x_axis)

    def _sy(self, v):
        return self._scale(v, self.y_axis)

    def _scale(self, _v, axis):
        if _v is None:
            return None
        v = self._to_float(_v)
        min, max = self._to_float(axis.min), self._to_float(axis.max)
        scale = (v - min) * (axis._size) / (max - min)
        return scale

    def _to_label(self, val: float, exampler, format):
        try:
            if isinstance(exampler, datetime):
                datetime_format = strftime_by_example(format)
                val = datetime.fromtimestamp(val).strftime(datetime_format)
                return val
            else:
                return format.format(val)
        except Exception:
            return str(val)

    def _render_axis(self, bm: PMBitmap, axis: PMPlotAxisConfig, dx, dy):
        # axis
        x0 = self.x_axis.margin
        y0 = self.rect.height - self.y_axis.margin
        x_axis_w = self.rect.width - self.x_axis.margin * 2
        y_axis_h = self.rect.height - self.y_axis.margin * 2
        bm.line((x0, y0, x0 + dx * x_axis_w, y0 - dy * y_axis_h), color=axis.color)
        _debug(f"Rendering axis with min={axis.min}, max={axis.max}, tic_interval={axis.tic_interval}, format='{axis.format}'")
        # tics and labels
        tic_size = axis.tic_height / 2
        start = self._to_float(axis.min)
        end = self._to_float(axis.max)
        n_tics = axis.n_tics
        tic_interval = axis.tic_interval
        if not n_tics:
            # prefer n_tics over tic_interval if both are provided, but calculate n_tics if tic_interval is provided
            n_tics = (end - start) / self._to_float(axis.tic_interval)
        else:
            tic_interval = (end - start) / n_tics
            _debug(f"Calculated tic_interval: {tic_interval} based on n_tics: {n_tics}")
        if n_tics > 100:
            _die(f"Warning: number of tics ({n_tics}) is very high for axis with range {start} to {end} and tic_interval {axis.tic_interval}. Consider increasing tic_interval or setting n_tics to a reasonable number.")
        format = axis.format
        val = start
        while n_tics >= 0:
            sval = self._scale(val, axis)
            bm.gfx.text_color = axis.color
            # base rect for tic
            tic_rect = (x0, y0, x0, y0) 
            # move to tic position
            tic_rect = _add(tic_rect, (dx * sval, -dy * sval, dx * sval, -dy * sval)) 
            # move down/left to center
            tic_rect = _add(tic_rect, (-dy * tic_size, -dx * tic_size, dy * tic_size, dx * tic_size)) 
            if tic_rect[0] > (x_axis_w + self.x_axis.margin) or tic_rect[1] < 0:
                _debug(f"Skipping tic at val={val} because tic_rect={tic_rect} is outside of plot rect={self.rect}")
                val += tic_interval
                n_tics -= 1
                continue
            bm.line(tic_rect, color=axis.color)
            # draw label
            tic_rect = _add(tic_rect, (-dy * axis.margin, dx * tic_size * 4, -dy * axis.margin, dx * tic_size * 4))
            bm.gfx.text_color = axis.color
            bm.gfx.text_bg_color = None
            label = self._to_label(val, axis.min, format)
            bm.text_box(tic_rect, label)
            val += tic_interval

    def _render_lines(self, bm: PMBitmap, x, y, ly, trace):
            x_data = self.x_axis.data
            y_data = trace.data
            line_width = trace.line_width
            format = trace.format
            for i in range(len(y_data) - 1):
                point = y_data[i]
                x0, y0 = self._to_float(x_data[i]), self._to_float(point.y)
                next_point = y_data[i + 1]
                x1, y1 = self._to_float(x_data[i + 1]), self._to_float(next_point.y)
                # Print y-value at each point
                if y0 is None:
                    continue
                bm.gfx.text_color = point.color or trace.color
                rect = (x + self._sx(x0), ly - self._sy(y0), x + self._sx(x0), ly - self._sy(y0))
                bm.text_box(rect, format.format(y0))
                if y1 is None:
                    continue # skip if data is missing
                line = (x + self._sx(x0), y - self._sy(y0), x + self._sx(x1), y - self._sy(y1))
                bm.line(line, color=point.color or trace.color, width=line_width)

            # Print last y-value
            last_point = y_data[-1]
            if last_point is None:
                return
            bm.gfx.text_color = last_point.color or trace.color
            sx0 = self._sx(x_data[-1])
            sy0 = self._sy(last_point.y)
            if sy0 is None or sx0 is None:
                return
            rect =(x + sx0, ly - sy0, x + sx0, ly - sy0)
            print(199, format)
            bm.text_box(rect, format.format(last_point.y))

    def _render_bars(self, bm: PMBitmap, x, y, label_y, trace):                
            x_data = self.x_axis.data
            y_data = trace.data
            format = trace.format
            for i in range(len(y_data)):
                point = y_data[i]
                bar_width = point.width or trace.width
                if point._width is not None:
                    bar_width = self._sx(self.x_axis.min.timestamp() + point._width)
                x0, y0 = self._to_float(x_data[i]), self._to_float(point.y)
                # Print y-value at each point
                if y0 is None:
                    continue
                
                bar_rect = PMRect(0,0,0,0)
                bar_rect.x0 = x + self._sx(x0) + trace.x_offset
                bar_rect.y0 = y - self._sy(y0)
                bar_rect.x1 = x + self._sx(x0) + trace.x_offset
                bar_rect.y1 = y
                if point.halign == "center":
                    bar_rect.x0 -= bar_width // 2
                    bar_rect.x1 += bar_width // 2
                else:
                    bar_rect.x1 += bar_width

                bm.gfx.text_color = point.color or trace.color
                label_rect = PMRect(bar_rect.x0, bar_rect.y0 - 30, bar_rect.x1, bar_rect.y0)
                bm.text_box(label_rect, format.format(y0))

                bm.gfx.text_color = trace.label_color
                bm.gfx.color = "black"
                bm.gfx.bg_color = point.color or trace.color
                bm.rectangle(bar_rect)
                bm.text_box(bar_rect, point.label or "")

    def _render_traces(self, bm: PMBitmap):
        x = self.x_axis.margin
        y = self.rect.height - self.y_axis.margin
        label_y = y - bm.gfx.font.pitch // 2

        for trace in self.traces:
            if trace.type == "line":
                self._render_lines(bm, x, y, label_y, trace)
            elif trace.type == "bar":
                self._render_bars(bm, x, y, label_y, trace)
            else:
                self._render_lines(bm, x, y, label_y, trace)

    def _convert_list_to_floats(self, datalist):
        new_datalist = []
        for i, val in enumerate(datalist):
            if isinstance(val, datetime):
                new_datalist.append(val.timestamp())
            else:
                new_datalist.append(float(val))
        return new_datalist

    def _render_title(self, bm: PMBitmap):
        gfx = bm.gfx_push()
        gfx.text_bg_color = None
        gfx.set_font("DejaVuSans", 2.0)
        bm.gfx.text_color = None
        if self._plot.title:
            bm.gfx.text_color = self.x_axis.color
            bm.text_box((0,0,self.rect.width, self.rect.height), self._plot.title, halign="center", valign="top")
        if self._plot.x_axis.title and self._plot.y_axis.title:
            bm.gfx.text_color = self.x_axis.color
            bm.text_box((0,0,self.rect.width, self.rect.height), self.x_axis.title, halign="center", valign="bottom")
        if self._plot.y_axis.title:
            gfx.text_bg_color="gray"
            bm.gfx.text_color = self.y_axis.color
            x, y, w, h = bm.gfx.font.getbbox(self.y_axis.title)
            print(280, x, y, w, h)
            bm.text(self.y_axis.title, 0, (self.rect.height - w)/2, angle=-90)
        bm.gfx_pop()

    def render(self, bm: PMBitmap) -> None:
        bm.gfx_push(self.gfx)
        bm.rectangle((0, 0, self.rect.width, self.rect.height), fill="white")
        self._render_title(bm)
        self._render_axis(bm, self.x_axis, dx=1, dy=0)
        self._render_axis(bm, self.y_axis, dx=0, dy=1)
        self._render_traces(bm)
        bm.gfx_pop()
