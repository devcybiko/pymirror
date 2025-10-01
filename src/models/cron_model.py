from dataclasses import dataclass, field
from models.pmmodel import PMModel

@dataclass
class CronModel(PMModel):
    first_delay: str
    delay: str
    repeat: str
    event: dict = field(default_factory=dict)