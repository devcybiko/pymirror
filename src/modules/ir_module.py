from devices.ir_device import IRDevice
from pymirror.pmlogger import _debug
from pymirror.pmmodule import PMModule

class IrModule(PMModule):
    def __init__(self, pm, config):
        super().__init__(pm, config)
        self._ir = config.ir
        self.name = self._ir.name
        self.remote = IRDevice()

    def render(self, force: bool = False) -> bool:
        # nothing to see here
        pass

    def _read_remote(self):
        ## add any messages that have come from the ir remote
        while remote_event := self.remote.get_key_event():
            _debug(f"Received event from remote: {remote_event}")
            ## translate into raw keyboard event
            event = {
                "event": "RawKeyboardEvent",
                "scancode": remote_event["scancode"],
                'key_name': remote_event["key_name"],
                'scancode': remote_event["scancode"],
                'pressed': remote_event["pressed"],
                'repeat': remote_event["repeat"]
            }
            _debug("\n--- ir event")
            _debug(event)
            _debug("")
            self.publish_event(event)

    def exec(self):
        self._read_remote()
        return False