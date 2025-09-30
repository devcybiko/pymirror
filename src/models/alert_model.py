from dataclasses import dataclass
from models.pmmodel import PMModel

@dataclass
class AlertModel(PMModel):
    header: str = None
    body: str = None
    footer: str = None
    timeout: int = 1
