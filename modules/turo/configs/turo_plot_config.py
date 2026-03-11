from dataclasses import dataclass
from datetime import datetime

@dataclass
class TuroPlotConfig:
    database_url: str
    x_column: str 
    traces: list = None
    refresh_time: str = "60s"
    nmonths: int = 3
    start_date: str = datetime.now().strftime("%Y-%m-%d")
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M:%S"
    x_axis: dict = None
    y_axis: dict = None
