from dataclasses import dataclass

@dataclass
class CliConfig:
    cycle_seconds: int
    command: str
    header: str
    body: str
    footer: str

