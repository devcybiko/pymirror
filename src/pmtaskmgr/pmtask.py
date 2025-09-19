from munch import DefaultMunch, munchify

from pmdb.pmdb import PMDb


class PMTask:
    def __init__(self, pmtm, config: dict):
        self._task = munchify(config, factory=DefaultMunch)
        self.pmtm: "PMTaskMgr" = pmtm
        self.pmdb: PMDb = pmtm.pmdb
        self.name = self._task.name
        self.cron = self._task.cron
        if not (self.name or self.cron):
            raise ValueError("task must have both a name and a cron")
        pass