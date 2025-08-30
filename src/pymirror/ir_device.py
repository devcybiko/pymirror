#!/usr/bin/env python3
"""
Non-blocking IR remote input utilities for PyMirror
Uses ir-keytable to capture IR events without blocking the main loop
"""
import subprocess
import os
import select
import time
import re
from typing import Optional, Dict, List, Tuple

# Default IR remote key mapping
IR_KEY_MAP = {
    # Add your remote's key mappings here
    # Format is hex value (without 0x): "KEY_NAME"
    "40": "KEY_OK",       # Example mapping - center/OK button
    "45": "KEY_UP",       # Example mapping
    "44": "KEY_DOWN",     # Example mapping
    "43": "KEY_LEFT",     # Example mapping
    "46": "KEY_RIGHT",    # Example mapping
    # Add more mappings based on your IR remote
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
        self.buffer = ""
        self.key_last_time: Dict[str, float] = {}  # Track last press times for each key
        self.protocols = "rc-5,rc-5-sz,jvc,sony,nec,sanyo,mce_kbd,rc-6,sharp,xmp"
        
        # Start the ir-keytable process
        self._start_ir_process()
    
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
            print(f"IR device initialized: listening for {self.protocols} protocols")
            
        except Exception as e:
            print(f"Failed to start ir-keytable: {e}")
            self.process = None
    
    def _parse_scancode(self, line: str) -> Optional[str]:
        """Extract scancode from ir-keytable output line"""
        if "scancode = " not in line:
            return None
            
        try:
            # Extract the scancode without the 0x prefix
            match = re.search(r'scancode = (0x[0-9a-fA-F]+)', line)
            if match:
                return match.group(1).replace("0x", "").lower()
        except:
            pass
        return None
    
    def _parse_protocol(self, line: str) -> Optional[str]:
        """Extract protocol from ir-keytable output line"""
        try:
            if "protocol(" in line:
                match = re.search(r'protocol\(([^)]+)\)', line)
                if match:
                    return match.group(1)
        except:
            pass
        return "unknown"
    
    def _is_repeat(self, line: str) -> bool:
        """Check if line indicates a key repeat"""
        return " repeat" in line
        
    def get_key_event(self) -> Optional[dict]:
        """
        Get an IR key event without blocking.
        Returns None if no key event, or a dict with key info if pressed.
        """
        if not self.process:
            return None
        
        # Check if process is still running
        if self.process.poll() is not None:
            print("IR process exited, restarting...")
            self._start_ir_process()
            return None
            
        # Non-blocking read with small timeout
        rlist, _, _ = select.select([self.process.stdout], [], [], 0.01)
        
        # Process any new data
        if self.process.stdout in rlist:
            try:
                chunk = self.process.stdout.read(1024)
                if chunk:
                    self.buffer += chunk
                    
                    # Process complete lines in buffer
                    while "\n" in self.buffer:
                        line, self.buffer = self.buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue

                        now = time.time()
                        scancode = self._parse_scancode(line)
                        
                        if not scancode:
                            continue
                            
                        protocol = self._parse_protocol(line)
                        is_repeat = self._is_repeat(line)
                        
                        # Update last press time
                        self.key_last_time[scancode] = now
                        
                        # Get key name from mapping
                        key_name = self.key_map.get(scancode, f"IR_{scancode}")
                        
                        # Return the key event
                        return {
                            'scancode': scancode,
                            'key_name': key_name,
                            'keycode': int(scancode, 16) if scancode.isalnum() else 0,
                            'protocol': protocol,
                            'pressed': True,
                            'repeat': is_repeat
                        }
            except Exception as e:
                print(f"Error reading IR data: {e}")
        
        # Check for key releases (timeout based)
        now = time.time()
        expired_keys = []
        
        # First, collect all expired keys
        for sc, last_time in self.key_last_time.items():
            if now - last_time > self.key_up_timeout:
                expired_keys.append(sc)
        
        # Process one expired key at a time, but remove it immediately
        if expired_keys:
            sc = expired_keys[0]
            # Remove from tracking dict immediately to prevent repeat releases
            del self.key_last_time[sc]
            
            key_name = self.key_map.get(sc, f"IR_{sc}")
            return {
                'scancode': sc,
                'key_name': key_name,
                'keycode': int(sc, 16) if sc.isalnum() else 0,
                'protocol': "unknown",
                'pressed': False,
                'repeat': False
            }
            
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
                print("IR device closed")
            except Exception as e:
                print(f"Error closing IR device: {e}")
            finally:
                self.process = None


# Example usage and testing
if __name__ == "__main__":
    print("Testing IR remote input.")
    print("Press remote buttons or Ctrl+C to quit")
    
    ir = IRDevice()
    
    if not ir.process:
        print("Failed to start ir-keytable process")
        exit(1)
    
    try:
        while True:
            # Test raw event method
            event = ir.get_key_event()
            if event:
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
