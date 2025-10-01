from dataclasses import dataclass

@dataclass
class AlertModel:
    header: str = None
    body: str = None
    footer: str = None
    timeout: int = 1
