from devices.keyboard_device import KeyboardDevice
from pmlogger import _debug
from pymirror.pmmodule import PMModule

class KeyboardModule(PMModule):
    def __init__(self, pm, config):
        super().__init__(pm, config)
        self._ir = config.ir
        self.name = self._ir.name
        self.keyboard = KeyboardDevice()

    def render(self, force: bool = False) -> bool:
        # nothing to see here
        pass

    def _read_keyboard(self):
        ## add any messages that have come from the keyboard
        while key_event := self.keyboard.get_key_event():
            _debug(f"Received event from keyboard: {key_event}")
            event = {
                "event": "RawKeyboardEvent",
                "keycode":  key_event["keycode"],
                'key_name': key_event["key_name"],
                'scancode': key_event["scancode"],
                'pressed': key_event["pressed"],
                'repeat': key_event["repeat"]
            }
            self.publish_event(event)

    def exec(self):
        self._read_keyboard()
        return False