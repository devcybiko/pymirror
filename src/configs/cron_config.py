from dataclasses import dataclass, field
from typing import List

@dataclass
class AlertConfig:
    cron: str
    description: str = None
    event: dict = field(default_factory=dict)

@dataclass
class CronConfig:
    alerts: List[AlertConfig] = field(default_factory=lambda: [AlertConfig(cron="*:00")])