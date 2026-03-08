from datetime import datetime

from dateutil.relativedelta import relativedelta

from munch import DefaultMunch
from sqlalchemy import Table
from configs.config_config import ConfigConfig
from configs.plot_config import PlotConfig
from pmdb.pmdb import PMDb
from pymirror.pmmodule import PMModule
from pymirror.comps.pmplotcomp import PMPlotComp, PMPlotCompConfig, PMPlotAxisConfig
from pymirror.pmrect import PMRect

class PlotModule(PMModule):
    def __init__(self, pm, config: ConfigConfig):
        super().__init__(pm, config)
        print(f"Initializing PlotModule with config: {config}")
        self._plot: PlotConfig = PlotConfig(**config.plot)
        now = datetime.now()
        x_axis=PMPlotAxisConfig(min=now, max=(now + relativedelta(days=5)), margin=40, tic_interval=86400, format="{:%Y-%m-%d}", data=[], color="red")
        y_axis=PMPlotAxisConfig(min=0, max=10, margin=40, tic_interval=5.0, format="${:.2f}", color="blue")
        for i in range(6):
            x_axis.data.append((now + relativedelta(days=i/2)).timestamp())
        plot_config: PMPlotCompConfig = PMPlotCompConfig(x_axis=x_axis,y_axis=y_axis,rect=self.bitmap.rect)
        self.plot = PMPlotComp(self.bitmap.gfx, plot_config)
        self.timer.set_timeout(self._plot.refresh_time)
        self.db = PMDb({"url": self._plot.database})
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