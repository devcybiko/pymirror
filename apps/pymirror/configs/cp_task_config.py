
from dataclasses import dataclass

@dataclass
class CpTaskConfig:
    cron: str = "*:15:00"
    from_file: str
    to_file: str
    cp_command: str = "scp {from_file} {to_file}"
