from dataclasses import dataclass, field
from models.pmmodel import PMModel

@dataclass
class ClockModel:
    date_format: str
