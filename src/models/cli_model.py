from dataclasses import dataclass
from models.pmmodel import PMModel

@dataclass
class CliModel:
    cycle_seconds: str
    command: str
    header: str
    body: str
    footer: str

