#!/usr/bin/env python3
"""
Non-blocking IR input utilities for PyMirror
Reads directly from IR device files instead of lirc to avoid side effects
"""
import os
import select
import glob
from typing import Optional, List
from evdev import InputDevice, ecodes

class IRDevice:
    """
    Direct IR device reader that avoids lirc dependencies.
    Reads from /dev/input/eventX devices directly.
    Can optionally grab the device exclusively.
    """
    
    def __init__(self, device_path: Optional[str] = None, grab_device: bool = False):
        self.device = None  # Primary device for reading
        self.device_path = device_path
        self.grab_device = grab_device
        self.is_grabbed = False
        self.grabbed_devices = []  # List of all grabbed devices
        self._find_and_setup_ir()
    
    def _find_ir_devices(self) -> List[str]:
        """Find all IR input devices"""
        ir_devices = []
        
        # Look for all event devices
        event_devices = glob.glob('/dev/input/event*')
        
        for device_path in event_devices:
            try:
                device = InputDevice(device_path)
                device_name = device.name.lower()
                capabilities = device.capabilities()
                
                # Check if device has IR capabilities
                is_ir_device = False
                
                # First, exclude obvious non-IR devices
                keyboard_keywords = ['keyboard', 'kbd', 'key']
                mouse_keywords = ['mouse', 'pointer', 'touchpad', 'trackball']
                system_keywords = ['system', 'power', 'sleep', 'lid']
                
                is_excluded = any(keyword in device_name for keyword in 
                                keyboard_keywords + mouse_keywords + system_keywords)
                
                if is_excluded:
                    print(f"Skipping (excluded): {device_path} - {device.name}")
                    device.close()
                    continue
                
                # Check by device name (common IR receiver names)
                ir_keywords = ['ir', 'remote', 'receiver', 'lirc', 'mce', 'cir', 'infrared']
                if any(keyword in device_name for keyword in ir_keywords):
                    is_ir_device = True
                    print(f"Found IR device by name: {device_path} - {device.name}")
                
                # Check by capabilities - but be more specific
                if ecodes.EV_MSC in capabilities:
                    msc_events = capabilities[ecodes.EV_MSC]
                    # IR devices typically have MSC_SCAN
                    if ecodes.MSC_SCAN in msc_events:
                        # Additional check: IR devices usually don't have extensive keyboard capabilities
                        if ecodes.EV_KEY in capabilities:
                            key_events = capabilities[ecodes.EV_KEY]
                            # If it has too many key events, it's probably a keyboard
                            if len(key_events) > 50:  # Keyboards typically have 100+ keys
                                print(f"Skipping (too many keys): {device_path} - {device.name} ({len(key_events)} keys)")
                                device.close()
                                continue
                        
                        is_ir_device = True
                        print(f"Found IR device by capabilities: {device_path} - {device.name}")
                
                if is_ir_device:
                    ir_devices.append(device_path)
                else:
                    print(f"Not IR device: {device_path} - {device.name}")
                
                device.close()
            except (OSError, PermissionError):
                # Skip devices we can't access
                continue
        
        return ir_devices
    
    def _find_and_setup_ir(self):
        """Find and setup IR devices, grabbing all if requested"""
        if self.device_path:
            # Use specified device
            try:
                self.device = InputDevice(self.device_path)
                print(f"Using specified IR device: {self.device_path}")
                if self.grab_device:
                    self._grab_device(self.device, self.device_path)
                return
            except (OSError, PermissionError) as e:
                print(f"Cannot access specified device {self.device_path}: {e}")
        
        # Auto-find IR devices
        ir_devices = self._find_ir_devices()
        
        if not ir_devices:
            print("No IR devices found!")
            return
        
        # First, set up the primary device for reading
        for device_path in ir_devices:
            try:
                self.device = InputDevice(device_path)
                self.device_path = device_path
                print(f"Using primary IR device: {device_path} - {self.device.name}")
                break
            except (OSError, PermissionError) as e:
                print(f"Cannot access {device_path}: {e}")
                continue
        
        # Now, if grabbing is requested, grab ALL IR devices
        if self.grab_device and ir_devices:
            print(f"Attempting to grab {len(ir_devices)} IR device(s)...")
            grabbed_count = 0
            
            for device_path in ir_devices:
                try:
                    # Use existing device if it's the primary one, otherwise create new
                    if device_path == self.device_path and self.device:
                        device = self.device
                    else:
                        device = InputDevice(device_path)
                    
                    if self._grab_device(device, device_path):
                        grabbed_count += 1
                        if device == self.device:
                            self.is_grabbed = True
                    else:
                        # Close device if we opened it but couldn't grab it (and it's not primary)
                        if device != self.device:
                            device.close()
                            
                except (OSError, PermissionError) as e:
                    print(f"Cannot access {device_path}: {e}")
                    continue
            
            print(f"Successfully grabbed {grabbed_count}/{len(ir_devices)} IR devices")
            
    def _grab_device(self, device: InputDevice, device_path: str) -> bool:
        """Attempt to grab a single device, return True if successful"""
        try:
            device.grab()
            self.grabbed_devices.append(device)
            print(f"✓ Grabbed: {device_path} - {device.name}")
            return True
        except OSError as e:
            print(f"✗ Could not grab {device_path}: {e}")
            return False
    
    def get_ir_event(self) -> Optional[dict]:
        """
        Get an IR event without blocking.
        Returns None if no IR event, or a dict with IR info if received.
        """
        if not self.device:
            return None
        
        # Check if input is available
        r, _, _ = select.select([self.device], [], [], 0)
        
        if self.device in r:
            try:
                for event in self.device.read():
                    if event.type == ecodes.EV_MSC and event.code == ecodes.MSC_SCAN:
                        # IR scancode event
                        return {
                            'scancode': event.value,
                            'protocol': self._guess_protocol(event.value),
                            'hex_code': f"0x{event.value:X}",
                            'timestamp': event.timestamp()
                        }
                    elif event.type == ecodes.EV_KEY:
                        # Some IR devices also send key events
                        if event.value == 1:  # Key press
                            return {
                                'keycode': event.code,
                                'key_name': ecodes.KEY[event.code] if event.code in ecodes.KEY else f'UNKNOWN_{event.code}',
                                'scancode': event.code,
                                'pressed': True,
                                'repeat': False,
                                'timestamp': event.timestamp()
                            }
                        elif event.value == 2:  # Key repeat
                            return {
                                'keycode': event.code,
                                'key_name': ecodes.KEY[event.code] if event.code in ecodes.KEY else f'UNKNOWN_{event.code}',
                                'scancode': event.code,
                                'pressed': True,
                                'repeat': True,
                                'timestamp': event.timestamp()
                            }
                        elif event.value == 0:  # Key release
                            return {
                                'keycode': event.code,
                                'key_name': ecodes.KEY[event.code] if event.code in ecodes.KEY else f'UNKNOWN_{event.code}',
                                'scancode': event.code,
                                'pressed': False,
                                'repeat': False,
                                'timestamp': event.timestamp()
                            }
            except OSError:
                # Device might have been disconnected
                print("IR device disconnected")
                self.device = None
        
        return None
    
    def _guess_protocol(self, scancode: int) -> str:
        """Basic protocol guess based on scancode (customize per your remote)"""
        if scancode & 0xFF00 == 0x0000:
            return "NEC"
        elif scancode & 0xFF00 == 0x0100:
            return "RC5"
        elif scancode & 0xFF00 == 0x0200:
            return "Sony"
        elif scancode & 0xFF000000 == 0xFF000000:
            return "NEC Extended"
        else:
            return "Unknown"
    
    def get_ir_command(self) -> Optional[str]:
        """
        Get a simplified IR command without blocking.
        Returns None if no IR event, or a string representation if received.
        """
        event = self.get_ir_event()
        if not event:
            return None
        
        if 'scancode' in event and 'protocol' not in event:
            # MSC_SCAN event
            return f"{event['protocol']}:{event['hex_code']}"
        elif 'key_name' in event and event.get('pressed', False):
            # Key event
            repeat_str = "_REPEAT" if event.get('repeat', False) else ""
            return f"KEY:{event['key_name']}{repeat_str}"
        
        return None
    
    def close(self):
        """Close IR devices and release all grabs"""
        # Release all grabbed devices
        for device in self.grabbed_devices:
            try:
                device.ungrab()
                # Only close devices that aren't our primary device
                if device != self.device:
                    device.close()
                print(f"Released grab on {device.path}")
            except OSError:
                pass  # Device might already be released
        
        if self.grabbed_devices:
            print(f"Released grab on {len(self.grabbed_devices)} IR device(s)")
        
        self.grabbed_devices.clear()
        self.is_grabbed = False
        
        # Close primary device
        if self.device:
            self.device.close()
            self.device = None


# Example usage and testing
if __name__ == "__main__":
    print("Testing direct IR device input.")
    print("Point your remote at the IR receiver and press buttons.")
    print("Press Ctrl+C to quit.")
    print("Note: You may need to run with sudo for device access")
    
    # Test the IR device class
    # ir = IRDevice(grab_device=False)  # Usually don't need to grab IR devices
    ir = IRDevice(path="/d")  # Usually don't need to grab IR devices
    
    if not ir.device:
        print("No IR device found or accessible. Try running with sudo.")
        print("Make sure your IR receiver is connected and recognized by the system.")
        exit(1)
    
    print(f"Using device: {ir.device_path}")
    print("Listening for IR commands...")
    
    try:
        import time
        while True:
            # Test raw event method
            event = ir.get_ir_event()
            if event:
                if 'scancode' in event and 'protocol' in event:
                    print(f"IR: {event['protocol']} scancode={event['hex_code']}")
                elif 'key_name' in event:
                    if event['pressed']:
                        repeat_str = " (REPEAT)" if event['repeat'] else ""
                        print(f"IR Key: {event['key_name']}{repeat_str}")
                    else:
                        print(f"IR Key Released: {event['key_name']}")
            
            # Test simplified command method
            command = ir.get_ir_command()
            if command:
                print(f"Command: {command}")
            
            # Simulate other work
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nInterrupted by Ctrl+C")
    finally:
        ir.close()
        print("IR device closed.")
