#!/usr/bin/env python3
import lirc
import time

LUT = {
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
    def __init__(self, program_name="pymirror", lut=LUT):
        self.program_name = program_name
        self.key_name_lut = lut
        self.connection = None
        self.last_command = None
        self.last_time = 0
        self.key_down = False
        self.REPEAT_THRESHOLD = 0.10
        self.KEYUP_THRESHOLD = 0.10
        self.event_buffer = []
        
        # Try different LIRC connection methods
        try:
            # Method 1: Try RawConnection (doesn't need lircrc)
            self.connection = lirc.RawConnection()
            print(f"Connected to LIRC using RawConnection")
        except Exception as e:
            print(f"RawConnection failed: {e}")
            try:
                # Method 2: Try LircdConnection without parameters
                self.connection = lirc.LircdConnection()
                print(f"Connected to LIRC using LircdConnection")
            except Exception as e:
                print(f"LircdConnection failed: {e}")
                print("Make sure lircd is running and accessible")
                self.connection = None

    def _new_event(self, command=None):
        return {
            "command": command,
            "repeat": False,
            "pressed": False,
            "released": False,
            "key_name": None
        }

    def get_key_event(self):
        if not self.connection:
            return None
            
        # First, check if we have buffered events to return
        if self.event_buffer:
            return self.event_buffer.pop(0)
        
        now = time.time()
        
        try:
            # Try to read from LIRC
            if hasattr(self.connection, 'readline'):
                # RawConnection method
                line = self.connection.readline(timeout=0.05)  # 50ms timeout
            else:
                # Other connection types
                line = self.connection.receive(timeout=0.05)
                
            if line:
                # Parse LIRC line format: "code repeat_count button_name remote_name"
                parts = line.strip().split()
                if len(parts) >= 3:
                    code = parts[0]
                    repeat_count = int(parts[1])
                    button_name = parts[2]
                    
                    result = self._new_event(button_name)
                    
                    if button_name == self.last_command:
                        if (
                            self.key_down
                            and (now - self.last_time) < self.REPEAT_THRESHOLD
                        ):
                            result["repeat"] = True
                            result["pressed"] = True
                        else:
                            # Same key pressed after threshold - treat as new press
                            result["pressed"] = True
                            self.key_down = True
                    else:
                        # Different key - implicitly release previous key
                        if self.last_command is not None and self.key_down:
                            self.key_down = False
                        result["pressed"] = True
                        self.key_down = True

                    self.last_command = button_name
                    self.last_time = now
                    
                    # Look up key name
                    result["key_name"] = button_name
                    
                    self.event_buffer.append(result)
                    
        except Exception as e:
            # Timeout or other error - that's normal for non-blocking read
            pass

        # Check for key up
        if (
            not self.event_buffer  # No new events buffered
            and self.key_down
            and self.last_command is not None
            and (now - self.last_time) > self.KEYUP_THRESHOLD
        ):
            result = self._new_event(self.last_command)
            result["released"] = True
            result["pressed"] = False
            result["key_name"] = self.last_command
            self.key_down = False
            self.event_buffer.append(result)

        # Return the first buffered event, if any
        if self.event_buffer:
            return self.event_buffer.pop(0)
        
        return None

    def close(self):
        if self.connection:
            try:
                self.connection.close()
            except:
                pass


if __name__ == "__main__":
    ir = IRDevice()
    
    if not ir.connection:
        print("Failed to connect to LIRC. Make sure lircd is running.")
        exit(1)
    
    print("Listening for IR commands...")
    
    try:
        while True:
            event = ir.get_key_event()
            if event:
                print("IR event:", event)
            time.sleep(0.01)  # Small delay
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        ir.close()
