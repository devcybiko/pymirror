#!/usr/bin/env python3
"""
Non-blocking keyboard input utilities for PyMirror
Reads directly from keyboard device files instead of stdin to avoid side effects
"""
import os
import select
import glob
from typing import Optional, List
from evdev import InputDevice, ecodes

class KeyboardDevice:
    """
    Direct keyboard device reader that avoids stdin side effects.
    Reads from /dev/input/eventX devices directly.
    Can optionally grab the device exclusively to prevent console echo.
    """
    
    def __init__(self, device_path: Optional[str] = None, grab_device: bool = True):
        self.device = None  # Primary device for reading
        self.device_path = device_path
        self.grab_device = grab_device
        self.is_grabbed = False
        self.grabbed_devices = []  # List of all grabbed devices
        self._find_and_setup_keyboard()
    
    def _find_keyboard_devices(self) -> List[str]:
        """Find all keyboard input devices"""
        keyboard_devices = []
        
        # Look for all event devices
        event_devices = glob.glob('/dev/input/event*')
        
        for device_path in event_devices:
            try:
                device = InputDevice(device_path)
                # Check if device has keyboard capabilities
                capabilities = device.capabilities()
                if ecodes.EV_KEY in capabilities:
                    # Check if it has standard keyboard keys (not just mouse buttons)
                    keys = capabilities[ecodes.EV_KEY]
                    # Look for common keyboard keys
                    keyboard_keys = [ecodes.KEY_A, ecodes.KEY_SPACE, ecodes.KEY_ENTER, ecodes.KEY_ESC]
                    if any(key in keys for key in keyboard_keys):
                        keyboard_devices.append(device_path)
                        print(f"Found keyboard device: {device_path} - {device.name}")
                device.close()
            except (OSError, PermissionError):
                # Skip devices we can't access
                continue
        
        return keyboard_devices
    
    def _find_and_setup_keyboard(self):
        """Find and setup keyboard devices, grabbing all if requested"""
        if self.device_path:
            # Use specified device
            try:
                self.device = InputDevice(self.device_path)
                print(f"Using specified keyboard device: {self.device_path}")
                if self.grab_device:
                    self._grab_device(self.device, self.device_path)
                return
            except (OSError, PermissionError) as e:
                print(f"Cannot access specified device {self.device_path}: {e}")
        
        # Auto-find keyboard devices
        keyboard_devices = self._find_keyboard_devices()
        
        if not keyboard_devices:
            print("No keyboard devices found!")
            return
        
        # First, set up the primary device for reading
        for device_path in keyboard_devices:
            try:
                self.device = InputDevice(device_path)
                self.device_path = device_path
                print(f"Using primary keyboard device: {device_path} - {self.device.name}")
                break
            except (OSError, PermissionError) as e:
                print(f"Cannot access {device_path}: {e}")
                continue
        
        # Now, if grabbing is requested, grab ALL keyboard devices
        if self.grab_device and keyboard_devices:
            print(f"Attempting to grab {len(keyboard_devices)} keyboard device(s) to prevent console echo...")
            grabbed_count = 0
            
            for device_path in keyboard_devices:
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
            
            print(f"Successfully grabbed {grabbed_count}/{len(keyboard_devices)} keyboard devices")
            if grabbed_count < len(keyboard_devices):
                print("Warning: Some keyboard devices could not be grabbed - console echo may still occur")
            
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
    
    def get_key_event(self) -> Optional[dict]:
        """
        Get a keyboard event without blocking.
        Returns None if no key event, or a dict with key info if pressed.
        """
        if not self.device:
            return None
        
        # Check if input is available
        r, _, _ = select.select([self.device], [], [], 0)
        
        if self.device in r:
            try:
                for event in self.device.read():
                    if event.type == ecodes.EV_KEY:
                        # Handle key press (value == 1), key repeat (value == 2), and key release (value == 0)
                        if event.value == 1:  # Key press
                            return {
                                'keycode': event.code,
                                'key_name': ecodes.KEY[event.code] if event.code in ecodes.KEY else f'UNKNOWN_{event.code}',
                                'scancode': event.code,
                                'pressed': True,
                                'repeat': False
                            }
                        elif event.value == 2:  # Key repeat (auto-repeat when held down)
                            return {
                                'keycode': event.code,
                                'key_name': ecodes.KEY[event.code] if event.code in ecodes.KEY else f'UNKNOWN_{event.code}',
                                'scancode': event.code,
                                'pressed': True,
                                'repeat': True
                            }
                        elif event.value == 0:  # Key release
                            return {
                                'keycode': event.code,
                                'key_name': ecodes.KEY[event.code] if event.code in ecodes.KEY else f'UNKNOWN_{event.code}',
                                'scancode': event.code,
                                'pressed': False,
                                'repeat': False
                            }
            except OSError:
                # Device might have been disconnected
                print("Keyboard device disconnected")
                self.device = None
        
        return None
    
    def get_key_char(self) -> Optional[str]:
        """
        Get a keyboard character without blocking.
        Returns None if no key pressed, or the character/key name if pressed.
        """
        event = self.get_key_event()
        if not event or not event['pressed']:
            return None
        
        key_name = event['key_name']
        
        # Map common keys to characters
        key_map = {
            'KEY_A': 'a', 'KEY_B': 'b', 'KEY_C': 'c', 'KEY_D': 'd', 'KEY_E': 'e',
            'KEY_F': 'f', 'KEY_G': 'g', 'KEY_H': 'h', 'KEY_I': 'i', 'KEY_J': 'j',
            'KEY_K': 'k', 'KEY_L': 'l', 'KEY_M': 'm', 'KEY_N': 'n', 'KEY_O': 'o',
            'KEY_P': 'p', 'KEY_Q': 'q', 'KEY_R': 'r', 'KEY_S': 's', 'KEY_T': 't',
            'KEY_U': 'u', 'KEY_V': 'v', 'KEY_W': 'w', 'KEY_X': 'x', 'KEY_Y': 'y',
            'KEY_Z': 'z', 'KEY_SPACE': ' ', 'KEY_ENTER': '\n', 'KEY_ESC': '\x1b',
            'KEY_1': '1', 'KEY_2': '2', 'KEY_3': '3', 'KEY_4': '4', 'KEY_5': '5',
            'KEY_6': '6', 'KEY_7': '7', 'KEY_8': '8', 'KEY_9': '9', 'KEY_0': '0',
        }
        
        return key_map.get(key_name, key_name)
    
    def close(self):
        """Close keyboard devices and release all grabs"""
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
            print(f"Released grab on {len(self.grabbed_devices)} keyboard device(s)")
        
        self.grabbed_devices.clear()
        self.is_grabbed = False
        
        # Close primary device
        if self.device:
            self.device.close()
            self.device = None


# Example usage and testing
if __name__ == "__main__":
    print("Testing direct keyboard device input with exclusive grab.")
    print("This will prevent keystrokes from appearing in the console.")
    print("Press keys or 'q' to quit:")
    print("Note: You may need to run with sudo for device access")
    
    # Test the new KeyboardDevice class with grab enabled (default)
    kbd = KeyboardDevice(grab_device=True)
    
    if not kbd.device:
        print("No keyboard device found or accessible. Try running with sudo.")
        exit(1)
    
    print(f"Using device: {kbd.device_path}")
    if kbd.is_grabbed:
        print("Device is exclusively grabbed - keystrokes won't appear in console")
    else:
        print("Device is NOT grabbed - keystrokes may appear in console")
    
    print("Press keys (q to quit):")
    
    try:
        import time
        while True:
            # Test raw event method
            event = kbd.get_key_event()
            if event:
                if event['pressed']:
                    print(f"Key pressed: {event['key_name']} (code: {event['keycode']})")
                    if event['key_name'] == 'KEY_Q':
                        print("Quitting...")
                        break
            
            # Simulate other work
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nInterrupted by Ctrl+C")
    finally:
        kbd.close()
        print("Keyboard device closed and grab released.")
