from dataclasses import dataclass

@dataclass
class PlotConfig:
    x_axis: dict
    y_axis: dict
    refresh_time: str = "60s"
    database_url: str = None
    sql: str = None
    width: int = None
    height: int = None
