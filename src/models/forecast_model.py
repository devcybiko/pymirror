from dataclasses import dataclass

@dataclass
class ForecastModel:
    days: int = 3  # Number of days to forecast
    days_offset: int = 0  # Offset for the forecast days
    icon_size: str = "small"  # Size of the forecast icons (None, small, medium, large)
    lines: int = 3
