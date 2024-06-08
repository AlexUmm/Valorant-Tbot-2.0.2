#These are all the dependencies for the script to run.
#If you get any errors make sure you installed all the requirments in requirements.txt
#https://www.unknowncheats.me/forum/index.php is where I found the original source.
#https://www.unknowncheats.me/forum/valorant/622597-fastest-python-valorant-triggerbot-fr-fr.html
#Then I added a gui and some tweeks and features of my own like Auto Counter Strafe!
#Compiled by @DavidUmm (discord xahlicks)
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
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
import os
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.modalview import ModalView
from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window
from kivy.config import Config
from kivy.animation import Animation
from kivy.uix.widget import Widget
from datetime import datetime, timedelta


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

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

#Add/Remove hotkeys here!
#Find virtual-key codes here: https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes

KEY_MAP = {
    'Right Mouse' : '0x02', 'Mouse Side 1' : '0x05', 'Mouse Side 2' : '0x06',
    'Left Shift' : '0x10', 'Left Control' : '0x11', 'Left Alt' : '0x12', 
    'V' : '0x59', 'C' : '0x43', 'X' : '0x58', 'Z' : '0x5A'
}
#The GUI spam starts here...
class ToggleSwitch(BoxLayout):
    def __init__(self, text, active, callback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.size_hint_x = None
        self.width = 100
        self.height = 60
        self.spacing = 10

        self.label = Label(text=text, color=(1, 1, 1, 1), size_hint=(1, 0.5))
        self.toggle = ToggleButton(
            text='ON' if active else 'OFF',
            state='down' if active else 'normal',
            background_color=(0, 1, 0, 1) if active else (1, 0, 0, 1),
            on_press=self.on_toggle,
            size_hint=(1, 0.5)
        )
        self.callback = callback

        self.add_widget(self.label)
        self.add_widget(self.toggle)

    def on_toggle(self, instance):
        is_active = instance.state == 'down'
        animation = Animation(background_color=(0, 1, 0, 1) if is_active else (1, 0, 0, 1), duration=0.3)
        animation.start(instance)
        instance.text = 'ON' if is_active else 'OFF'
        self.callback(is_active)

class SpotifyGUI(BoxLayout):
    def __init__(self, triggerbot_instance, **kwargs):
        super().__init__(**kwargs)
        self.triggerbot = triggerbot_instance
        self.orientation = 'vertical'
        self.padding = 20  # 
        self.spacing = 0

        self.add_widget(Image(source=resource_path('jett.png'), size_hint=(1, .35), allow_stretch=True, keep_ratio=False))

        top_options_layout = BoxLayout(orientation='horizontal', spacing=40, size_hint_y=None, height=60)

        self.always_enabled_toggle = ToggleSwitch(
            text="Always Enabled",
            active=self.triggerbot.always_enabled,
            callback=self.toggle_always_enabled
        )
        top_options_layout.add_widget(self.always_enabled_toggle)

        top_options_layout.add_widget(Widget(size_hint_x=None, width=20))

        self.auto_counter_strafe_toggle = ToggleSwitch(
            text="Auto Counter Strafe",
            active=self.triggerbot.auto_counter_strafe,
            callback=self.toggle_auto_counter_strafe
        )
        top_options_layout.add_widget(self.auto_counter_strafe_toggle)

        
        self.add_widget(top_options_layout)

        controls_layout = GridLayout(cols=2, spacing=20, size_hint=(1, 0.6))

        self.trigger_delay_label = Label(text=f"Trigger Delay (ms): {self.triggerbot.trigger_delay}", color=(1, 1, 1, 1), halign='center', valign='middle')
        self.trigger_delay_label.bind(size=self.trigger_delay_label.setter('text_size'))
        controls_layout.add_widget(self.trigger_delay_label)
        self.trigger_delay_slider = Slider(min=10, max=200, value=self.triggerbot.trigger_delay, step=10)
        self.trigger_delay_slider.bind(value=self.update_trigger_delay)
        controls_layout.add_widget(self.create_label_slider("Trigger Delay:", self.trigger_delay_slider))

        self.base_delay_label = Label(text=f"Base Delay (s): {self.triggerbot.base_delay:.2f}", color=(1, 1, 1, 1), halign='center', valign='middle')
        self.base_delay_label.bind(size=self.base_delay_label.setter('text_size'))
        controls_layout.add_widget(self.base_delay_label)
        self.base_delay_slider = Slider(min=0.01, max=5.00, value=self.triggerbot.base_delay, step=0.01)
        self.base_delay_slider.bind(value=self.update_base_delay)
        controls_layout.add_widget(self.create_label_slider("Base Delay:", self.base_delay_slider))

        self.color_tolerance_label = Label(text=f"Color Tolerance: {self.triggerbot.color_tolerance}", color=(1, 1, 1, 1), halign='center', valign='middle')
        self.color_tolerance_label.bind(size=self.color_tolerance_label.setter('text_size'))
        controls_layout.add_widget(self.color_tolerance_label)
        self.color_tolerance_slider = Slider(min=10, max=100, value=self.triggerbot.color_tolerance, step=5)
        self.color_tolerance_slider.bind(value=self.update_color_tolerance)
        controls_layout.add_widget(self.create_label_slider("Color Tolerance:", self.color_tolerance_slider))

        self.add_widget(controls_layout)

        self.triggerbot_btn = Button(text="Stop Triggerbot", size_hint=(1, 0.1), background_color=(0, 1, 0, 1))  # Dark green
        self.triggerbot_btn.bind(on_press=self.toggle_triggerbot)
        self.add_widget(self.triggerbot_btn)

        self.change_hotkey_btn = Button(text="Change Hotkey", size_hint=(1, 0.1), background_color=(0.1, 0.1, 0.1, 1))  # Dark grey
        self.change_hotkey_btn.bind(on_press=self.open_hotkey_popup)
        self.add_widget(self.change_hotkey_btn)

        self.exit_btn = Button(text="Exit", size_hint=(1, 0.1), background_color=(0.1, 0.1, 0.1, 1))  # Dark grey
        self.exit_btn.bind(on_press=self.exit_program)
        self.add_widget(self.exit_btn)

    def create_label_slider(self, text, slider):
        layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=50)
        label = Label(text=text, size_hint=(1, 0.5), color=(1, 1, 1, 1), halign='center', valign='middle')
        label.bind(size=label.setter('text_size'))
        layout.add_widget(label)
        layout.add_widget(slider)
        return layout

    def update_trigger_delay(self, instance, value):
        self.triggerbot.trigger_delay = int(value)
        self.trigger_delay_label.text = f"Trigger Delay (ms): {self.triggerbot.trigger_delay}"
        self.triggerbot.save_config()

    def update_base_delay(self, instance, value):
        self.triggerbot.base_delay = float(value)
        self.base_delay_label.text = f"Base Delay (s): {self.triggerbot.base_delay:.2f}"
        self.triggerbot.save_config()

    def update_color_tolerance(self, instance, value):
        self.triggerbot.color_tolerance = int(value)
        self.color_tolerance_label.text = f"Color Tolerance: {self.triggerbot.color_tolerance}"
        self.triggerbot.save_config()

    def toggle_triggerbot(self, instance):
        self.triggerbot.paused = not self.triggerbot.paused
        if self.triggerbot.paused:
            self.triggerbot_btn.text = "Start Triggerbot"
            self.triggerbot_btn.background_color = (1, 0, 0, 1)  # Dark red
        else:
            self.triggerbot_btn.text = "Stop Triggerbot"
            self.triggerbot_btn.background_color = (0, 1, .1, 1)  # Dark green

    def toggle_always_enabled(self, value):
        self.triggerbot.always_enabled = value
        self.triggerbot.save_config()

    def toggle_auto_counter_strafe(self, value):
        self.triggerbot.auto_counter_strafe = value
        if value:
            self.triggerbot.setup_auto_counter_strafe()
        else:
            keyboard.unhook_all()
        self.triggerbot.save_config()

    def exit_program(self, instance):
        self.triggerbot.exit_program = True
        self.triggerbot.exiting()

    def open_hotkey_popup(self, instance):
        self.hotkey_popup = HotkeyPopup(self.triggerbot)
        self.hotkey_popup.open()


class HotkeyPopup(ModalView):
    def __init__(self, triggerbot_instance, **kwargs):
        super().__init__(**kwargs)
        self.triggerbot = triggerbot_instance
        self.size_hint = (None, None)
        self.size = (400, 200)
        self.auto_dismiss = False

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.label = Label(text='Select new hotkey:', color=(1, 1, 1, 1), halign='center', valign='middle')
        self.label.bind(size=self.label.setter('text_size'))
        layout.add_widget(self.label)

        self.hotkey_spinner = Spinner(
            text='Select Key',
            values=list(KEY_MAP.keys()),
            size_hint=(1, 0.5)
        )
        layout.add_widget(self.hotkey_spinner)

        self.submit_button = Button(text='Submit', background_color=(0.1, 0.1, 0.1, 1))  # Dark grey
        self.submit_button.bind(on_press=self.change_hotkey)
        layout.add_widget(self.submit_button)

        self.add_widget(layout)

    def change_hotkey(self, instance):
        selected_key = self.hotkey_spinner.text
        if selected_key in KEY_MAP:
            new_hotkey = int(KEY_MAP[selected_key], 16)
            self.triggerbot.update_hotkey(new_hotkey)
            self.dismiss()
        else:
            self.label.text = 'Invalid selection. Try again.'

class triggerbot:
    def __init__(self):
        self.sct = None
        self.triggerbot = False
        self.triggerbot_toggle = True
        self.exit_program = False 
        self.toggle_lock = threading.Lock()
        self.paused = False
        self.initialized = False
        self.auto_counter_strafe = False

#Set Outline Color Here
#Colors I Use;
#Red: 250, 25, 25
#Purple: 250, 100, 250
#Yellow: 210, 220, 80
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
#If when Auto Counter Strafe is enabled and cpu usages spikes
#Just adjust the time.sleep values to .1
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

class SpotifyApp(App): 
    def __init__(self, triggerbot_instance, **kwargs):
        super().__init__(**kwargs)
        self.triggerbot = triggerbot_instance
        self.title = "Spotify"
 
  # Set GUI Title "Spotify", you can use anything you want like "Valtracker.gg" etc..

    def build(self):
        self.triggerbot.initialize()
        self.triggerbot_thread = threading.Thread(target=self.triggerbot.starterino)
        self.triggerbot_thread.start()

        return SpotifyGUI(self.triggerbot)

if __name__ == "__main__":
   
    Window.size = (380, 570) 
 
 # Adjust GUI Width and Hieght (380, 570) is default

    triggerbot_instance = triggerbot()
    SpotifyApp(triggerbot_instance).run()
