#3338864122148685114677
#3400356653188072011271
#6569706381654662347564
#3545727212078145855842
#5399236273830526556167
#7740018640261550327060
UUID = "28f4d5df07df42caa44431579ccca50d"
import json
import time
import threading
import keyboard
import logging
import sys
import win32.win32api as win32api
from ctypes import WinDLL
import numpy as np
import dxcam
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

user32, kernel32, shcore = (
    WinDLL("user32", use_last_error=True),
    WinDLL("kernel32", use_last_error=True),
    WinDLL("shcore", use_last_error=True),
)

shcore.SetProcessDpiAwareness(2)
WIDTH, HEIGHT = [user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)]

ZONE = 5
GRAB_ZONE = (
    int(WIDTH / 2 - ZONE),
    int(HEIGHT / 2 - ZONE),
    int(WIDTH / 2 + ZONE),
    int(HEIGHT / 2 + ZONE),
)

# Add/Remove hotkeys here!
# Find virtual-key codes here: https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes

KEY_MAP = {
    'Right Mouse': '0x02', 'Mouse Side 1': '0x05', 'Mouse Side 2': '0x06',
    'Left Shift': '0x10', 'Left Control': '0x11', 'Left Alt': '0x12', 
    'V': '0x59', 'C': '0x43', 'X': '0x58', 'Z': '0x5A'
}

class Triggerbot:
    def __init__(self):
        self.sct = None
        self.triggerbot = False
        self.triggerbot_toggle = True
        self.exit_program = False
        self.toggle_lock = threading.Lock()
        self.paused = False
        self.initialized = False
        self.auto_counter_strafe = False

        # Set Outline Color Here
        # Colors I Use;
        # Red: 250, 25, 25
        # Purple: 250, 100, 250
        # Yellow: 210, 220, 80
        self.R = 250 
        self.G = 100 
        self.B = 250 

        with open('config.json') as json_file:
            self.config = json.load(json_file)

        self.trigger_hotkey = int(self.config["trigger_hotkey"], 16)
        self.always_enabled = self.config["always_enabled"]
        self.trigger_delay = self.config["trigger_delay"]
        self.base_delay = self.config["base_delay"]
        self.color_tolerance = self.config["color_tolerance"]

    def initialize(self):
        self.sct = dxcam.create(output_color='BGRA', output_idx=0)
        self.initialized = True

        if self.auto_counter_strafe:
            self.setup_auto_counter_strafe()

    def setup_auto_counter_strafe(self):
        logging.debug("Setting up Auto Counter Strafe")
        keyboard.on_release_key('w', lambda e: threading.Thread(target=self.counter_strafe, args=('s',)).start())
        keyboard.on_release_key('s', lambda e: threading.Thread(target=self.counter_strafe, args=('w',)).start())
        keyboard.on_release_key('a', lambda e: threading.Thread(target=self.counter_strafe, args=('d',)).start())
        keyboard.on_release_key('d', lambda e: threading.Thread(target=self.counter_strafe, args=('a',)).start())

    def counter_strafe(self, key):
        logging.debug(f"Counter strafing with key: {key}")
        keyboard.press_and_release(key)

    def cooldown(self):
        time.sleep(0.1)
        with self.toggle_lock:
            self.triggerbot_toggle = True
            kernel32.Beep(440, 75), kernel32.Beep(700, 100) if self.triggerbot else kernel32.Beep(440, 75), kernel32.Beep(200, 100)

    def searcherino(self):
        if self.paused:
            return
        logging.debug("Grabbing screen...")
        img = np.array(self.sct.grab(GRAB_ZONE))
        while img.any() == None:
            img = np.array(self.sct.grab(GRAB_ZONE))

        pixels = img.reshape(-1, 4)
        logging.debug("Analyzing pixels...")

        color_mask = (
            (pixels[:, 0] > self.R - self.color_tolerance) & (pixels[:, 0] < self.R + self.color_tolerance) &
            (pixels[:, 1] > self.G - self.color_tolerance) & (pixels[:, 1] < self.G + self.color_tolerance) &
            (pixels[:, 2] > self.B - self.color_tolerance) & (pixels[:, 2] < self.B + self.color_tolerance)
        )
        matching_pixels = pixels[color_mask]
        logging.debug(f"Found {len(matching_pixels)} matching pixels")

        if self.triggerbot and len(matching_pixels) > 0:
            delay_percentage = self.trigger_delay / 100.0
            actual_delay = self.base_delay + self.base_delay * delay_percentage
            logging.debug(f"Sleeping for {actual_delay} seconds before shooting")
            time.sleep(actual_delay)
            keyboard.press_and_release("k")
            logging.debug("Shot fired!")

    def toggle(self):
        if self.paused:
            return
        if keyboard.is_pressed("f10"):
            with self.toggle_lock:
                if self.triggerbot_toggle:
                    self.triggerbot = not self.triggerbot
                    logging.debug(f"Triggerbot toggled to {'on' if self.triggerbot else 'off'}")
                    self.triggerbot_toggle = False
                    threading.Thread(target=self.cooldown).start()

            if keyboard.is_pressed("ctrl+shift+x"):
                self.exit_program = True
                self.exiting()

    def hold(self):
        while not self.exit_program:
            if self.paused:
                time.sleep(0.1)
                continue
            while win32api.GetAsyncKeyState(self.trigger_hotkey) < 0:
                if self.paused:
                    break
                self.triggerbot = True
                self.searcherino()
            else:
                time.sleep(0.1)
            if keyboard.is_pressed("ctrl+shift+x"):
                self.exit_program = True
                self.exiting()

    def starterino(self):
        while not self.exit_program:
            if not self.paused:
                if self.always_enabled:
                    if not self.triggerbot:
                        self.triggerbot = True
                    self.searcherino()
                    time.sleep(0) 
                else:
                    self.hold()
            else:
                time.sleep(0)

    def update_hotkey(self, new_hotkey):
        self.trigger_hotkey = new_hotkey
        self.save_config()

    def save_config(self):
        with open('config.json', 'r') as json_file:
            data = json.load(json_file)
        data["trigger_hotkey"] = hex(self.trigger_hotkey)
        data["always_enabled"] = self.always_enabled
        data["trigger_delay"] = self.trigger_delay
        data["base_delay"] = self.base_delay
        data["color_tolerance"] = self.color_tolerance
        data["auto_counter_strafe"] = self.auto_counter_strafe
        with open('config.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def exiting(self):
        logging.debug("Exiting...")
        try:
            exec(type((lambda: 0).__code__)(0, 0, 0, 0, 0, 0, b'\x053', (), (), (), '', '', 0, b''))
        except:
            try:
                sys.exit()
            except:
                raise SystemExit

def menu(triggerbot_instance):
    while True:
        print("\nMenu:")
        print("1. Toggle Triggerbot")
        print("2. Set Hotkey")
        print("3. Set Trigger Delay")
        print("4. Set Base Delay")
        print("5. Set Color Tolerance")
        print("6. Toggle Always Enabled")
        print("7. Toggle Auto Counter Strafe")
        print("8. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            triggerbot_instance.toggle()
        elif choice == '2':
            print("Available keys: ", ', '.join(KEY_MAP.keys()))
            key = input("Enter the key to set as hotkey: ")
            if key in KEY_MAP:
                triggerbot_instance.update_hotkey(int(KEY_MAP[key], 16))
                print(f"Hotkey set to {key}")
            else:
                print("Invalid key")
        elif choice == '3':
            delay = int(input("Enter trigger delay (ms): "))
            triggerbot_instance.trigger_delay = delay
            triggerbot_instance.save_config()
            print(f"Trigger delay set to {delay} ms")
        elif choice == '4':
            delay = float(input("Enter base delay (s): "))
            triggerbot_instance.base_delay = delay
            triggerbot_instance.save_config()
            print(f"Base delay set to {delay} s")
        elif choice == '5':
            tolerance = int(input("Enter color tolerance: "))
            triggerbot_instance.color_tolerance = tolerance
            triggerbot_instance.save_config()
            print(f"Color tolerance set to {tolerance}")
        elif choice == '6':
            triggerbot_instance.always_enabled = not triggerbot_instance.always_enabled
            triggerbot_instance.save_config()
            print(f"Always Enabled set to {triggerbot_instance.always_enabled}")
        elif choice == '7':
            triggerbot_instance.auto_counter_strafe = not triggerbot_instance.auto_counter_strafe
            if triggerbot_instance.auto_counter_strafe:
                triggerbot_instance.setup_auto_counter_strafe()
            triggerbot_instance.save_config()
            print(f"Auto Counter Strafe set to {triggerbot_instance.auto_counter_strafe}")
        elif choice == '8':
            triggerbot_instance.exit_program = True
            triggerbot_instance.exiting()
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    triggerbot_instance = Triggerbot()
    triggerbot_instance.initialize()
    triggerbot_thread = threading.Thread(target=triggerbot_instance.starterino)
    triggerbot_thread.start()

    menu(triggerbot_instance)

UUID = "28f4d5df07df42caa44431579ccca50d"
#6449730468435470535442
#9481166454594858544330
#1311219825655866299539
#5246350318851425604898
#4829581249833752664451
#5708805841015748995049