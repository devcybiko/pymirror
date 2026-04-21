from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from munch import DefaultMunch

from pymirror.pmtile import TileConfig

from glslib.glsdb import GLSDb
from glslib.gson import json_dumps
from glslib.strftime import strftime_by_example
from glslib.to_types import to_munch
from components.pm_plot_component import PMPlotAxisConfig, PMPlotComponent, PMPlotComponentConfig, PMPlotTraceConfig, PMPointConfig
from pymirror.pmtile import PMTile
from glslib.logger import _die, _debug, _print

@dataclass
class TuroPlotConfig:
    database_url: str
    x_column: str 
    traces: list = None
    sql: str = None
    sql_file: str = "turo_plot.sql"
    sql_params: dict = None
    refresh_time: str = "60s"
    nmonths: int = 3
    start_date: str = datetime.now().strftime("%Y-%m-%d")
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M:%S"
    x_axis: dict = None
    y_axis: dict = None
    vehicle_column: str = "vehicle_nickname"
    title: str = ""

class TuroPlotTile(PMTile):
    def __init__(self, pm, config: TileConfig):
        super().__init__(pm, config)
        self._turo: TuroPlotConfig = DefaultMunch.fromDict(
            TuroPlotConfig(**config.turo_plot).__dict__
        )
        self.turo_db = GLSDb(self._turo.database_url)
        self.date_format = strftime_by_example(self._turo.date_format or "%Y-%m-%d")
        self.time_format = strftime_by_example(self._turo.time_format or "%H:%M:%S")
        self.plot_config: PMPlotComponentConfig = None
        self.x_axis_config: PMPlotAxisConfig = PMPlotAxisConfig(**self._turo.x_axis)
        self.x_axis_config.format = strftime_by_example(self._turo.x_axis.format or self._turo.date_format or "%Y-%m-%d")
        self.y_axis_config: PMPlotAxisConfig = PMPlotAxisConfig(**self._turo.y_axis)
        self.y_axis_config.format = strftime_by_example(self._turo.y_axis.format or self._turo.date_format or "%Y-%m-%d")
        self.sql_file: str = self._turo.sql_file or  Path(__file__).parent / "turo_plot.sql"

    def _create_query(self):
        # Read the SQL file
        if self._turo.sql:
            sql_content = self._turo.sql
        else:
            sql_file = self.sql_file
            with open(sql_file, 'r') as f:
                sql_content = f.read()
            if self._turo.sql_params:
                sql_content = sql_content.format(**self._turo.sql_params)
        return sql_content

    def render(self, force: bool) -> bool:
        self.plot.render(self.bitmap)
        return False  # we will render in exec when we have the data

    def _min(self, _data, preferred=0, default=0):
        data = [d for d in _data if d is not None]
        if preferred is not None:
            return preferred
        return min(data, default=default)

    def _max(self, _data, preferred=0, default=0):
        data = [d for d in _data if d is not None]
        if preferred is not None:
            return preferred
        return max(data, default=default)

    def exec(self) -> bool:
        if not self.timer.is_timedout():
            return False
            # return is_dirty # early exit if not timed out
        self.timer.reset(self._turo.refresh_time)
        rows = self.turo_db.query(self._create_query())
        x_column_name = self._turo.x_column
        y_columns = [trace.column for trace in self._turo.traces]
        z_rows, x_axis, all_values = self._collate_data(rows, x_column_name, y_columns, self._turo.traces)
        self._compute_x_axis(x_axis)
        self._compute_y_axis(all_values)
        self.plot_config = PMPlotComponentConfig(self.x_axis_config, self.y_axis_config, rect=self.bitmap.rect, title=self._turo.title)
        self.plot = PMPlotComponent(self.bitmap.gfx, self.plot_config)
        for trace_data in self._turo.traces:
            vehicle_nickname = trace_data.vehicle
            # Create a copy without the 'vehicle' key instead of deleting
            trace_dict = {k: v for k, v in trace_data.items() if k not in ['vehicle', 'vehicle_column']}
            vehicle_trace = PMPlotTraceConfig(**trace_dict)
            vehicle_points = []
            for k, v in z_rows.items():
                point_data = v[vehicle_nickname]
                if point_data[vehicle_trace.column] is None:
                    point = None
                else:
                    _width = None
                    label_format = vehicle_trace.label_format or "'label_format'"
                    # Flatten point_data to include all trip fields for eval
                    eval_context = dict(point_data)
                    if point_data.get('trip'):
                        eval_context.update(point_data.trip)
                    label = eval(label_format, {}, eval_context)
                    if vehicle_trace._width:
                        _width = eval(vehicle_trace._width, {}, eval_context)
                    point = PMPointConfig(
                        y=point_data.trip.get(vehicle_trace.column, 0), 
                        _width=_width,
                        label=label,
                        halign="left"
                    )
                vehicle_points.append(point)
            self.plot.add_trace(vehicle_trace, vehicle_points)
        return True

    def _compute_y_axis(self, all_values):
        self.y_axis_config.min = self._min(
            all_values, preferred=self.y_axis_config.min, default=0
        )
        _debug(f"y_axis_config.min: {self.y_axis_config.min}")
        self.y_axis_config.max = self._max(
            all_values, preferred=self.y_axis_config.max, default=100
        )
        _debug(f"y_axis_config.max: {self.y_axis_config.max}")

    def _compute_x_axis(self, x_axis):
        self.x_axis_config.data = x_axis
        self.x_axis_config.min = self._min(
            x_axis, preferred=self.x_axis_config.min, default=0
        )
        self.x_axis_config.max = self._max(
            x_axis, preferred=self.x_axis_config.max, default=100
        )
        _debug(f"x_axis: {json_dumps(x_axis)}")
        return x_axis

    def _collate_data(self, rows, x_column_name, y_columns, traces):
        # all collected values for y axis to determine min and max for scaling. 
        # we will ignore None values.
        # NOTE: they should all be the same "scale" (e.g. dollars per day) 
        # since they will be plotted on the same y-axis, 
        # so we can determine the min and max from all values combined.
        # z_rows: {
        #    "x_value": {
        #       "vehicle": {"column_name": 3,  "column_name": 50.5 },
        #       "vehicle": { "column_name": 3, "column_name": 50.5},
        #    },
        #    "2026-01-01": {
        #       "sentra": {"trip_days": 3,  "total_earnings": 50.5 },
        #       "cx5": { "trip_days": 3, "total_earnings": 50.5},
        #    },
        #    "2026-01-02": {
        #       "sentra": null,
        #       "cx5": { "trip_days": 5,"total_earnings": 150.5}
        #    },
        #    "2026-01-03": {
        #       "sentra": {"trip_days": 6, "total_earnings": 250.5},
        #       "cx5": null
        #    }
        # }
        all_values = []
        x_axis = []
        z_rows = DefaultMunch()
        for row in rows:
            trip = to_munch(row)
            x_value = trip[x_column_name]
            if z_rows[str(x_value)] is None:
                x_axis.append(x_value)
                z_rows[str(x_value)] = DefaultMunch()
            z_row = z_rows[str(x_value)]
            for trace in traces:
                if z_row[trace.vehicle] == None: z_row[trace.vehicle] = DefaultMunch()
                vehicle_row = z_row[trace.vehicle]
                for y_column in y_columns:
                    if trip[trace.vehicle_column] == trace.vehicle:
                        vehicle_row["_x_axis"] = x_value # for debugging
                        vehicle_row["trip"] = trip # for debugging
                        vehicle_row[y_column] = trip[y_column]
                    if trip[y_column] is not None:
                        all_values.append(trip[y_column])
        _print(json_dumps(z_rows))
        _print(json_dumps(x_axis))
        _print(json_dumps(all_values))
        return z_rows, x_axis, all_values
