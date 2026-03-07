from dataclasses import dataclass

@dataclass
class PlotConfig:
    x_axis: dict
    y_axis: dict
    foo: bool = False
    refresh_time: str = "60s"
    database: str = None
    sql: str = None
    width: int = None
    height: int = None
