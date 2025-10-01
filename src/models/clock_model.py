from dataclasses import dataclass, field
from models.pmmodel import PMModel

@dataclass
class ClockModel(PMModel):
    date_format: str
