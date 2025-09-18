from munch import munchify


class PMTask:
    def __init__(self, pmtm, config: dict):
        self._task = munchify(config)
        self.pmtm = pmtm
        self.pmdb = pmtm.pmdb
        self.name = self._task.name
        self.cron = self._task.cron
        pass