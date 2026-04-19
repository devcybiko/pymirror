from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from munch import DefaultMunch

from glslib.to_types import to_munch
from pymirror.pmmodule import ModuleConfig

from glslib.glsdb import GLSDb
from glslib.strftime import strftime_by_example
from components.pm_plot_component import PMPlotAxisConfig, PMPlotComponent, PMPlotComponentConfig, PMPlotTraceConfig, PMPointConfig
from pymirror.pmmodule import PMModule

@dataclass
class TuroTrendsTraceConfig(PMPlotTraceConfig):
    nickname: str = None

@dataclass
class TuroTrendsConfig:
    database_url: str
    refresh_time: str
    column: str = "average_earnings"
    x_axis: dict = None
    y_axis: dict = None
    traces: list[TuroTrendsTraceConfig] = None
    start_date: str = "2025-12-01"
    window_size: int = 30

class TuroTrendsModule(PMModule):
    def __init__(self, pm, config: ModuleConfig):
        super().__init__(pm, config)
        self._trends: TuroTrendsConfig = DefaultMunch.fromDict(
            TuroTrendsConfig(**config.turo_trends).__dict__
        )
        self.turo_db = GLSDb(self._trends.database_url)
        self.date_format = strftime_by_example(self._trends.date_format or "%Y-%m-%d")
        self.time_format = strftime_by_example(self._trends.time_format or "%H:%M:%S")
        self.plot_config: PMPlotComponentConfig = None
        self.x_axis_config: PMPlotAxisConfig = PMPlotAxisConfig(**self._trends.x_axis)
        self.x_axis_config.format = strftime_by_example(self._trends.x_axis.format or self._trends.date_format or "%Y-%m-%d")
        self.y_axis_config: PMPlotAxisConfig = PMPlotAxisConfig(**self._trends.y_axis)
        self.y_axis_config.format = strftime_by_example(self._trends.y_axis.format or self._trends.date_format or "%Y-%m-%d")
        self.sql_file: str = self._trends.sql_file or  Path(__file__).parent / "turo_plot.sql"

    def _create_query(self, vehicle_nickname="sentra"):
        sql = f"""
            SELECT * 
            FROM qtrips 
            WHERE TRUE 
            AND vehicle_nickname = '{vehicle_nickname}'
            ORDER BY date
        """
        return sql

    def render(self, force: bool) -> bool:
        self.plot.render(self.bitmap)
        return False  # we will render in exec when we have the data

    def _aggregate_data(self, window):
        window_size = len(window)
        if window_size == 0:
            return
        count = sum([1 for trip in window if trip is not None])
        daily_earnings = sum([trip.daily_earnings for trip in window if trip is not None])
        daily_distance_traveled = sum([trip.daily_distance_traveled for trip in window if trip is not None])
        avg_count = round((count/window_size if window_size else 0 )* 100, 1)
        avg_earnings = round(daily_earnings/count if count else 0, 2)
        avg_distance = round(daily_distance_traveled/count if count else 0, 0)
        data = DefaultMunch()
        data.count = count
        data.daily_earnings = daily_earnings
        data.daily_distance_traveled = daily_distance_traveled
        data.avg_count = avg_count
        data.avg_earnings = avg_earnings
        data.avg_distance = avg_distance
        return data

    def _collect_averages(self, vehicle_nickname, start_date, window_size):
        records = []
        sql = f"""
            SELECT * 
            FROM qtrips 
            WHERE TRUE 
            AND vehicle_nickname = '{vehicle_nickname}'
            ORDER BY date
        """
        trips = self.turo_db.query(sql)
        trips = to_munch(trips)

        trip_index = 0
        trip = trips[trip_index]
        the_date = start_date
        end_date = datetime.now().date()
        window = [None] * window_size
        while the_date <= end_date:
            trip = None
            if trip_index < len(trips):
                trip = trips[trip_index]
            if trip and the_date == trip.date.date():
                # print(trip.date, trip.daily_earnings, trip.daily_distance_traveled)
                window.append(trip)
                window.pop(0)
                trip_index += 1
            else:
                # print(the_date, None, None)
                trip = None # for record.booked, below
                window.append(None)
                window.pop(0)
            record = self._aggregate_data(window)
            record.index = len(records)
            record.date = the_date
            record.booked = 1 if trip is not None else 0
            records.append(record)
            the_date += timedelta(days=1)
        return records

    def _date_to_timestamp(self, d):
        return int(datetime.combine(d, datetime.min.time()).timestamp())


    def _date_to_datetime(self, d):
        return datetime.combine(d, datetime.min.time())

    def exec(self) -> bool:
        if not self.timer.is_timedout():
            return False
            # return is_dirty # early exit if not timed out
        self.timer.reset(self._trends.refresh_time)
        start_date = datetime.strptime(self._trends.start_date, "%Y-%m-%d").date()
        end_date = datetime.now().date()
        delta_days = (end_date - start_date).days
        self.x_axis_config.min = self._date_to_datetime(start_date)
        self.x_axis_config.max = self._date_to_datetime(end_date)
        traces = self._trends.traces
        self.plot_config = PMPlotComponentConfig(self.x_axis_config, self.y_axis_config, rect=self.bitmap.rect, title=self._trends.title)
        self.plot = PMPlotComponent(self.bitmap.gfx, self.plot_config)
        for trace_cfg in traces:
            print(132, trace_cfg, self._trends.window_size)
            records = self._collect_averages(trace_cfg.nickname, start_date=start_date, window_size=self._trends.window_size or delta_days)
            trace = TuroTrendsTraceConfig(**trace_cfg)
            points = []
            for record in records:
                print(137, self._trends.column, record)
                self.x_axis_config.data.append(self._date_to_datetime(record.date))
                point = PMPointConfig(
                    y=record[trace_cfg.column],
                )
                points.append(point)
            self.plot.add_trace(trace, points)
        return True
