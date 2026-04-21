from dataclasses import dataclass
from datetime import datetime

from dateutil.relativedelta import relativedelta

from configs.config_config import ConfigConfig
from glslib.glsdb import GLSDb
from pymirror.pmtile import PMTile
from components.pm_plot_component import PMPlotComponent, PMPlotComponentConfig, PMPlotAxisConfig

@dataclass
class PlotConfig:
    x_axis: dict
    y_axis: dict
    refresh_time: str = "60s"
    database_url: str = None
    sql: str = None
    width: int = None
    height: int = None

class PlotTile(PMTile):
    def __init__(self, pm, config: ConfigConfig):
        super().__init__(pm, config)
        print(f"Initializing PlotTile with config: {config}")
        self._plot: PlotConfig = PlotConfig(**config.plot)
        now = datetime.now()
        x_axis=PMPlotAxisConfig(min=now, max=(now + relativedelta(days=5)), margin=40, tic_interval=86400, format="{:%Y-%m-%d}", data=[], color="red")
        y_axis=PMPlotAxisConfig(min=0, max=10, margin=40, tic_interval=5.0, format="${:.2f}", color="blue")
        for i in range(6):
            x_axis.data.append((now + relativedelta(days=i/2)).timestamp())
        plot_config: PMPlotComponentConfig = PMPlotComponentConfig(x_axis=x_axis,y_axis=y_axis,rect=self.bitmap.rect)
        self.plot = PMPlotComponent(self.bitmap.gfx, plot_config)
        self.timer.set_timeout(self._plot.refresh_time)
        self.db = GLSDb(self._plot.database_url)
        data = [1.5,2,3.75,4,5,1.99]
        self.plot.add_trace(data, color="blue", width=2, format="${:.2f}")
        data = [7,6,5,4,3,2]
        self.plot.add_trace(data, color="purple", width=2, format="${:.2f}")

 
    def render(self, force: bool) -> bool:
        if not (self.plot.is_dirty() or force):
            return False
        self.plot.render(self.bitmap)
        self.plot.clean()
        return True

    def exec(self) -> bool:
        if not self.timer.is_timedout(): 
            return False
            # return is_dirty # early exit if not timed out
        self.timer.reset(self._plot.refresh_time)
        self.rows = self.db.query(self._plot.sql)
        self.plot._dirty = True
        return True