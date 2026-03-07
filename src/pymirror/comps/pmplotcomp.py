from dataclasses import dataclass, field

from datetime import timedelta, datetime

from pmgfxlib.pmgfx import PMGfx
from pymirror.pmrect import PMRect
from pymirror.comps.pmcomponent import PMComponent
from pmgfxlib import PMBitmap

@dataclass
class PMPlotXAxisConfig:
    min: float
    max: float
    margin: int = 40
    tic_interval: float = 1.0
    format: str = "{:.2f}"
    datatype: type = datetime  # default to datetime
    data: list = field(default_factory=list)
    _min: float = None
    _max: float = None
    _data: list = field(default_factory=list)

@dataclass
class PMPlotYAxisConfig:
    min: float
    max: float
    margin: int = 40
    tic_interval: float = 1.0
    format: str = "{:.2f}"
    datatype: type = float
    data: list = field(default_factory=list)
    _min: float = None
    _max: float = None
    _data: list = field(default_factory=list)

@dataclass
class PMPlotTraceConfig:
    data: list
    color: str = "blue"
    width: int = 2
    format: str = "{:.2f}"
    _data: list = field(default_factory=list)

@dataclass
class PMPlotCompConfig:
    x_axis: PMPlotXAxisConfig
    y_axis: PMPlotYAxisConfig
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
        self.traces = []

    def is_dirty(self):
        return self._dirty

    def clean(self):
        self._dirty = False

    def add_trace(self, data, color="blue", width=2, format="{:.2f}"):
        self.traces.append(PMPlotTraceConfig(data, color, width, format))

    def _compute_bounds(self):
        # X bounds
        self.xmin = self._plot.x_axis._min
        self.xmax = self._plot.x_axis._max
        # Y bounds
        self.ymin = self._plot.y_axis._min
        self.ymax = self._plot.y_axis._max
        # Avoid zero range for y
        if self.ymin == self.ymax:
            self.ymax += 1

    def _sx(self, x):
        xmin, xmax = self.xmin, self.xmax
        sx = self._plot.x_axis.margin + (x - xmin) * (self.rect.width - 2 * self._plot.x_axis.margin) / (xmax - xmin)
        print(89, x, xmin, xmax, sx)
        return sx

    def _sy(self, y):
        # Support both float and datetime for axis math
        ymin, ymax = self.ymin, self.ymax
        return (
            self.rect.height - self._plot.x_axis.margin
            - (y - ymin) * (self.rect.height - 2 * self._plot.x_axis.margin) / (ymax - ymin)
        )

    def _render_x_axis(self, bm: PMBitmap):
        bm.line(
            (
                self._plot.x_axis.margin,
                self.rect.height - self._plot.x_axis.margin,
                self.rect.width - self._plot.x_axis.margin,
                self.rect.height - self._plot.x_axis.margin,
            ),
            color="black",
        )

        bm.line((self._plot.x_axis.margin, self._plot.x_axis.margin, self._plot.x_axis.margin, self.rect.height - self._plot.x_axis.margin), color="black")

        # x-axis tic marks using tic_interval
        tic_height = 6
        x_start = self.xmin
        x_end = self.xmax
        x_tic = self._plot.x_axis.tic_interval
        x_format = self._plot.x_axis.format
        x_datatype = self._plot.x_axis.datatype
        x_val = x_start
        while x_val <= x_end + 1e-8:
            sx = self._sx(x_val)
            y_base = self.rect.height - self._plot.x_axis.margin
            bm.line((sx, y_base, sx, y_base + tic_height), color="black")
            try:
                if x_datatype == datetime:
                    x_val_dt = datetime.fromtimestamp(x_val)
                    label = x_format.format(x_val_dt)
                else:
                    label = x_format.format(x_datatype(x_val))
            except Exception:
                label = str(x_val)
            bm.gfx.text_color = "black"
            bm.text(label, sx, y_base + tic_height + 2)
            x_val += x_tic

    def _render_y_axis(self, bm: PMBitmap):
        y_tic_height = 6
        y_start = self.ymin
        y_end = self.ymax
        y_tic = self._plot.y_axis.tic_interval
        y_format = self._plot.y_axis.format
        y_datatype = self._plot.y_axis.datatype
        y_val = y_start
        while y_val <= y_end + 1e-8:
            sy = self._sy(y_val)
            x_base = self._plot.x_axis.margin
            bm.line((x_base - y_tic_height, sy, x_base, sy), color="black")
            # Only print whole number y-values
            if abs(float(y_val) - round(float(y_val))) < 1e-6:
                try:
                    if y_datatype == datetime:
                        y_val_dt = datetime.fromtimestamp(y_val)
                        label = y_format.format(y_val_dt)
                    else:
                        label = y_format.format(y_datatype(y_val))
                except Exception:
                    label = str(y_val)
                bm.gfx.text_color = "black"
                bm.text(label, x_base - y_tic_height - 2, sy)
            y_val += y_tic

    def _render_traces(self, bm: PMBitmap):
        for trace in self.traces:
            data = trace._data
            color = trace.color
            width = trace.width
            format = trace.format
            for i in range(len(data) - 1):
                x0, y0 = self.x_axis._data[i], data[i]
                x1, y1 = self.x_axis._data[i + 1], data[i + 1]
                line = (self._sx(x0), self._sy(y0), self._sx(x1), self._sy(y1))
                print(170, line)
                bm.line(line, color=color, width=width)
                # Print y-value at each point
                bm.gfx.text_color = color if isinstance(color, str) else "black"
                bm.text(format.format(y0), self._sx(x0) + 4, self._sy(y0) - 8)
            # Print last y-value
            bm.gfx.text_color = color if isinstance(color, str) else "black"
            bm.text(format.format(data[-1]), self._sx(self.x_axis._data[-1]) + 4, self._sy(data[-1]) - 8)

    def _convert_list_to_floats(self, datalist):
        new_datalist = []
        for i, val in enumerate(datalist):
            if isinstance(val, datetime):
                new_datalist.append(val.timestamp())
            else:
                new_datalist.append(float(val))
        return new_datalist

    def _convert_data_to_floats(self):
        self.x_axis._data = self._convert_list_to_floats(self.x_axis.data)
        for trace in self.traces:
            trace._data = self._convert_list_to_floats(trace.data)
        self.x_axis._min = self.x_axis.min.timestamp() if isinstance(self.x_axis.min, datetime) else float(self.x_axis.min)
        self.x_axis._max = self.x_axis.max.timestamp() if isinstance(self.x_axis.max, datetime) else float(self.x_axis.max)
        self.y_axis._min = self.y_axis.min.timestamp() if isinstance(self.y_axis.min, datetime) else float(self.y_axis.min)
        self.y_axis._max = self.y_axis.max.timestamp() if isinstance(self.y_axis.max, datetime) else float(self.y_axis.max)

    def render(self, bm: PMBitmap) -> None:
        bm.gfx_push(self.gfx)
        bm.rectangle((0, 0, self.rect.width, self.rect.height), fill="white")
        self._convert_data_to_floats()
        self._compute_bounds()
        self._render_x_axis(bm)
        self._render_y_axis(bm)
        self._render_traces(bm)
        bm.gfx_pop()
