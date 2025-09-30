from dataclasses import dataclass, field
from models.pmmodel import PMModel

@dataclass
class PymirrorModel(PMModel):
    debug: bool = False
    secrets: str = ".secrets"
    force_render: bool = False
    positions: dict = field(default_factory=dict)