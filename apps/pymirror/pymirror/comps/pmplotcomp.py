from dataclasses import dataclass, field

from datetime import timedelta, datetime

from pmgfxlib.pmgfx import PMGfx
from pymirror.pmrect import PMRect
from pymirror.comps.pmcomponent import PMComponent
from pmgfxlib import PMBitmap
from pmutils import _add, _sub

@dataclass
class PMPlotAxisConfig:
    min: float
    max: float
    margin: int = 40
    color: str = "blue"
    tic_interval: float = 1.0
    tic_height: int = 10
    format: str = "{:.2f}"
    data: list = field(default_factory=list)
    _size: float = None

@dataclass
class PMPlotTraceConfig:
    data: list
    color: str = "blue"
    width: int = 2
    format: str = "{:.2f}"
    data: list = field(default_factory=list)    

@dataclass
class PMPlotCompConfig:
    x_axis: PMPlotAxisConfig
    y_axis: PMPlotAxisConfig
    rect: PMRect

class PMPlotComp(PMComponent):
    def __init__(
        self,
        gfx: PMGfx,
        config: PMPlotCompConfig,
    ):
        super().__init__(gfx, config)
        print(f"Initializing PMPlotComp with config: {config}")
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

    def add_trace(self, data, color="blue", width=2, format="{:.2f}"):
        self.traces.append(PMPlotTraceConfig(data, color, width, format))

    def _scale(self, v, axis):
        min, max = self._to_float(axis.min), self._to_float(axis.max)
        scale = (v - min) * (axis._size) / (max - min)
        return scale

    def _sx(self, v):
        return self._scale(v, self.x_axis)

    def _sy(self, v):
        return self._scale(v, self.y_axis)

    def _to_float(self, val):
        if isinstance(val, datetime):
            return val.timestamp()
        return float(val)

    def _to_label(self, val: float, template, format):
        if isinstance(template, datetime):
            val = datetime.fromtimestamp(val)
        try:
            return format.format(val)
        except Exception:
            return str(val)

    def _render_axis(self, bm: PMBitmap, axis: PMPlotAxisConfig, dx, dy):
        # axis
        x0 = self.x_axis.margin
        y0 = self.rect.height - self.y_axis.margin
        w = self.rect.width - self.x_axis.margin * 2
        h = self.rect.height - self.y_axis.margin * 2
        bm.line((x0, y0, x0 + dx * w, y0 - dy * h), color=axis.color)

        # tics and labels
        tic_size = axis.tic_height / 2
        start = self._to_float(axis.min)
        end = self._to_float(axis.max)
        tic = self._to_float(axis.tic_interval)
        format = axis.format
        val = start
        while val <= end + tic + 1e-8:
            sval = self._scale(val, axis)
            bm.gfx.text_color = axis.color
            # base rect for tic
            rect = (x0, y0, x0, y0) 
            # move to tic position
            rect = _add(rect, (dx * sval, -dy * sval, dx * sval, -dy * sval)) 
            # move down/left to center
            rect = _add(rect, (-dy * tic_size, -dx * tic_size, dy * tic_size, dx * tic_size)) 
            bm.line(rect, color=axis.color)
            # draw label
            rect = _add(rect, (-dy * axis.margin, dx * tic_size * 4, -dy * axis.margin, dx * tic_size * 4))
            bm.gfx.text_color = axis.color
            bm.gfx.text_bg_color = None
            label = self._to_label(val, axis.min, format)
            bm.text_box(rect, label)
            val += tic

    def _render_traces(self, bm: PMBitmap):
        x = self.x_axis.margin
        y = self.rect.height - self.y_axis.margin
        ly = y - bm.gfx.font.pitch // 2

        for trace in self.traces:
            data = trace.data
            color = trace.color
            width = trace.width
            format = trace.format
            x_data = self.x_axis.data
            y_data = trace.data
            for i in range(len(data) - 1):
                x0, y0 = self._to_float(x_data[i]), self._to_float(y_data[i])
                x1, y1 = self._to_float(x_data[i + 1]), self._to_float(y_data[i + 1])
                line = (x + self._sx(x0), y - self._sy(y0), x + self._sx(x1), y - self._sy(y1))
                bm.line(line, color=color, width=width)
                # Print y-value at each point
                bm.gfx.text_color = color
                rect = (x + self._sx(x0), ly - self._sy(y0), x + self._sx(x0), ly - self._sy(y0))
                bm.text_box(rect, format.format(y0))
            # Print last y-value
            bm.gfx.text_color = color
            rect =(x + self._sx(self.x_axis.data[-1]), ly - self._sy(y_data[-1]), x + self._sx(self.x_axis.data[-1]), ly - self._sy(y_data[-1]))
            bm.text_box(rect, format.format(y_data[-1]))

    def _convert_list_to_floats(self, datalist):
        new_datalist = []
        for i, val in enumerate(datalist):
            if isinstance(val, datetime):
                new_datalist.append(val.timestamp())
            else:
                new_datalist.append(float(val))
        return new_datalist

    def render(self, bm: PMBitmap) -> None:
        bm.gfx_push(self.gfx)
        bm.rectangle((0, 0, self.rect.width, self.rect.height), fill="white")
        self._render_axis(bm, self.x_axis, dx=1, dy=0)
        self._render_axis(bm, self.y_axis, dx=0, dy=1)
        self._render_traces(bm)
        bm.gfx_pop()
