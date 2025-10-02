from dataclasses import dataclass, field

@dataclass
class CronConfig:
    first_delay: str
    delay: str
    repeat: str
    event: dict = field(default_factory=dict)    
    alerts: dict = field(default_factory=dict)