#!/usr/bin/env python3
"""
Non-blocking IR remote input utilities for PyMirror
Uses ir-keytable to capture IR events without blocking the main loop
"""
import json
import subprocess
import os
import select
import time
import re
from typing import Optional, Dict, List, Tuple
from pymirror.pmlogger import _debug, _error, _debug

# Default IR remote key mapping
IR_KEY_MAP = {
        69: "KEY_ONE",
        70: "KEY_TWO",
        71: "KEY_THREE",
        68: "KEY_FOUR",
        64: "KEY_FIVE",
        67: "KEY_SIX",
        7: "KEY_SEVEN",
        21: "KEY_EIGHT",
        9: "KEY_NINE",
        25: "KEY_ZERO",
        22: "KEY_NUMBERSIGN",
        13: "KEY_ASTERISK",
        24: "KEY_UP",
        8: "KEY_LEFT",
        90: "KEY_RIGHT",
        82: "KEY_DOWN",
        28: "KEY_ENTER"
}

class IRDevice:
    """
    IR Remote device reader that captures events from ir-keytable.
    Provides a non-blocking interface similar to KeyboardDevice.
    """
    
    def __init__(self, key_map: Optional[Dict[str, str]] = None, key_up_timeout: float = 0.3):
        """
        Initialize the IR device interface
        
        Args:
            key_map: Optional mapping from scancodes to key names
            key_up_timeout: Time in seconds before considering a key released
        """
        self.key_map = key_map if key_map is not None else IR_KEY_MAP
        self.key_up_timeout = key_up_timeout
        self.process = None
        self.buffer = []
        self.key_last_time: Dict[str, float] = {}  # Track last press times for each key
        self.protocols = "rc-5,rc-5-sz,jvc,sony,nec,sanyo,mce_kbd,rc-6,sharp,xmp"
        
        # Start the ir-keytable process
        self._start_ir_process()
    
    def _parse_ir_test_line(self, line):
        # 2869.090042: lirc protocol(nec): scancode = 0x19
        # 2868.980048: lirc protocol(nec): scancode = 0x19 repeat
        # 2869.190079: event type EV_MSC(0x04): scancode = 0x19
        # 2869.190079: event type EV_SYN(0x00).

        if line[0] not in "0123456789": 
            return None
        words = [word.strip() for word in line.split(":")]
        _debug("words:", words)
        event = {
            "line": line,
            "time": float(words[0]),
            "raw": {
                "type": words[1],
                "scancode": words[2] if len(words) > 2 else None
            }
        }
        if words[1].startswith("lirc"):
            # words = [2869.090042, lirc protocol(nec), scancode = 0x19]
            # words = [2868.980048, lirc protocol(nec), scancode = 0x19 repeat]

            parts = words[1].replace("(", " ").replace(")", " ").split()
            # words[1] = lirc protocol(nec)
            # parts = [lirc, protocol, nec]
            protocol = parts[2]
            event["type"] = "lirc"
            event["protocol"] =  protocol

            parts = words[2].split()
            # words[2] = scancode = 0x19 repeat
            # parts = [scancode, =, 0x19, repeat]
            scancode = parts[2]
            keycode = int(scancode, 16)
            event["scancode"] = scancode
            event["keycode"] = keycode
            event["key_name"] = self.key_map.get(keycode, "IR_" + scancode)
            event["pressed"] = True
            event["repeat"] = len(parts) > 3

        elif words[1].startswith('event'):
            # 2869.190079: event type EV_MSC(0x04): scancode = 0x19
            # 2869.190079: event type EV_SYN(0x00).
            parts = words[1].replace("(", " ").replace(")", " ").replace(".", " ").split()
            _debug("... parts:", parts)
            type = parts[2]
            code = parts[3]
            event["type"] = type
            event["code"] = code
            event["repeat"] = False

            if len(words) > 2:
                parts = words[2].split()
                _debug("... ... parts 2:", parts)
                scancode = parts[2]
                keycode = int(parts[2], 16)
                event["scancode"] = parts[2]
                event["keycode"] = keycode
                event["key_name"] = self.key_map.get(keycode, "IR_" + scancode)
            else:
                event["scancode"] = None
                event["keycode"] = None
                event["key_name"] = None

            event["pressed"] = True
        else:
            _error("Unknown ir_test line", line)
            return None
        return event

    def _start_ir_process(self):
        """Start the ir-keytable process with unbuffered output"""
        try:
            # Command to run ir-keytable with unbuffered output
            cmd = [
                "stdbuf", "-o0",  # Make stdout unbuffered
                "ir-keytable",
                "-v", "-t",       # Verbose, testing mode
                "-p", self.protocols  # Protocols to listen for
            ]
            
            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            # Make stdout non-blocking
            os.set_blocking(self.process.stdout.fileno(), False)
            _debug(f"IR device initialized: listening for {self.protocols} protocols")
            
        except Exception as e:
            _debug(f"Failed to start ir-keytable: {e}")
            self.process = None
            
    def _get_key_event(self) -> Optional[dict]:
        """
        Get an IR key event without blocking.
        Returns None if no key event, or a dict with key info if pressed.
        """
        if not self.process:
            _error("Please start the IR process")
            return None
        
        # Check if process is still running
        if self.process.poll() is not None:
            _error("IR process exited, restarting...")
            self._start_ir_process()
            return None
            
        # Non-blocking read with small timeout
        rlist, _, _ = select.select([self.process.stdout], [], [], 0.001)
        if rlist and self.process.stdiout in rlist:
            # Process any new data
            chunk = self.process.stdout.read(1024) or ""
            print("chunk:", chunk)
            self.buffer.extend(chunk.split("\n"))
            print("buffer: ", self.buffer)

        line = ""
        while self.buffer:
            line = self.buffer[0].strip()
            self.buffer = self.buffer[1:]
            if line:
                break
        _debug("...", line)
        if not line:
            return None

        event = self._parse_ir_test_line(line)
        return event
        
    def get_key_event(self, types=["lirc"]):
        while event := self._get_key_event():
            if not types:
                # if no types specified, return all types
                return event
            if event["type"] in types:
                # if a type is specified, and our event is in it, return it
                return event
        return None
    

    def _save(self):
        # Check for key releases (timeout based)
        now = time.time()
        expired_keys = []
        
        # First, collect all expired keys
        for sc, last_time in self.key_last_time.items():
            if now - last_time > self.key_up_timeout:
                expired_keys.append(sc)
        
        # Process one expired key at a time, but remove it immediately
        if expired_keys:
            scancode = expired_keys[0]
            # Remove from tracking dict immediately to prevent repeat releases
            del self.key_last_time[sc]
            keycode = int(scancode, 16) if sc.isalnum() else 0
            key_name = self.key_map.get(keycode, f"IR_{sc}")
            return None
            # return {
            #     'scancode': scancode,
            #     'key_name': key_name,
            #     'keycode': keycode,
            #     'protocol': "unknown",
            #     'pressed': False,
            #     'repeat': False
            # }
        return None
    
    def get_key_char(self) -> Optional[str]:
        """
        Get an IR key character without blocking.
        Returns None if no key pressed, or the key name if pressed.
        """
        event = self.get_key_event()
        if not event or not event['pressed']:
            return None
            
        # IR remotes don't have characters, so just return the key name
        return event['key_name']
    
    def close(self):
        """Terminate the ir-keytable process"""
        if self.process:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                _debug("IR device closed")
            except Exception as e:
                _debug(f"Error closing IR device: {e}")
            finally:
                self.process = None


# Example usage and testing
if __name__ == "__main__":
    print("Testing IR remote input.")
    print("Press remote buttons or Ctrl+C to quit")
    
    ir = IRDevice()
    
    if not ir.process:
        _error("Failed to start ir-keytable process")
        exit(1)
    
    try:
        while True:
            # Test raw event method
            event = ir.get_key_event()
            if event:
                print(json.dumps(event, indent=2))
                if event['pressed']:
                    repeat_str = " (REPEAT)" if event['repeat'] else ""
                    print(f"Key pressed: {event['key_name']} (scancode: 0x{event['scancode']}){repeat_str}")
                else:
                    print(f"Key released: {event['key_name']} (scancode: 0x{event['scancode']})")
            
            # Simulate other work
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nInterrupted by Ctrl+C")
    finally:
        ir.close()
        print("IR device closed.")
