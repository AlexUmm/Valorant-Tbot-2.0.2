#7058838634083181522829
#6133973231399143428431
#9878949508561529469839
#7964531536164000166235
#5893615132455524884713
UUID = "286f7e5221e6480f96b143d64ca85058"
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

import ctypes

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

user32, kernel32, shcore = (
    WinDLL("user32", use_last_error=True),
    WinDLL("kernel32", use_last_error=True),
    WinDLL("shcore", use_last_error=True),
)

shcore.SetProcessDpiAwareness(2)
WIDTH, HEIGHT = [user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)]

def calculate_grab_zone(pixel_fov):
    ZONE = max(1, min(5, pixel_fov))
    return (
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

KEY_MAP = {
    'Right Mouse': '0x02', 'Mouse Side 1': '0x05', 'Mouse Side 2': '0x06',
    'Left Shift': '0x10', 'Left Control': '0x11', 'Left Alt': '0x12',
    'V': '0x56', 'C': '0x43', 'X': '0x58', 'Z': '0x5A'
}

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
        self.padding = 20
        self.spacing = 10

        self.add_widget(Image(source=resource_path('jett.png'), size_hint=(1, .35), allow_stretch=True, keep_ratio=False))

        options_layout = GridLayout(cols=2, spacing=[90, 10], padding=[10, 10, 10, 10], size_hint_y=None, height=200)

        self.always_enabled_toggle = ToggleSwitch(
            text="Always Enabled",
            active=self.triggerbot.always_enabled,
            callback=self.toggle_always_enabled
        )
        options_layout.add_widget(self.always_enabled_toggle)

        self.auto_counter_strafe_toggle = ToggleSwitch(
            text="Auto Counter Strafe",
            active=self.triggerbot.auto_counter_strafe,
            callback=self.toggle_auto_counter_strafe
        )
        options_layout.add_widget(self.auto_counter_strafe_toggle)

        self.humanization_toggle = ToggleSwitch(
            text="Humanization",
            active=self.triggerbot.humanization,
            callback=self.toggle_humanization
        )
        options_layout.add_widget(self.humanization_toggle)

        self.sticky_aim_toggle = ToggleSwitch(
            text="Sticky Aim (WIP)",
            active=self.triggerbot.sticky_aim,
            callback=self.toggle_sticky_aim
        )
        options_layout.add_widget(self.sticky_aim_toggle)

        self.add_widget(options_layout)

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

        self.pixel_fov_label = Label(text=f"Pixel FOV: {self.triggerbot.pixel_fov}", color=(1, 1, 1, 1), halign='center', valign='middle')
        self.pixel_fov_label.bind(size=self.pixel_fov_label.setter('text_size'))
        controls_layout.add_widget(self.pixel_fov_label)
        self.pixel_fov_slider = Slider(min=1, max=5, value=self.triggerbot.pixel_fov, step=1)
        self.pixel_fov_slider.bind(value=self.update_pixel_fov)
        controls_layout.add_widget(self.create_label_slider("Pixel FOV:", self.pixel_fov_slider))

        self.add_widget(controls_layout)

        self.triggerbot_btn = Button(text="Stop Triggerbot", size_hint=(1, 0.1), background_color=(0, 1, 0, 1))
        self.triggerbot_btn.bind(on_press=self.toggle_triggerbot)
        self.add_widget(self.triggerbot_btn)

        self.change_hotkey_btn = Button(text="Change Hotkey", size_hint=(1, 0.1), background_color=(0.1, 0.1, 0.1, 1))
        self.change_hotkey_btn.bind(on_press=self.open_hotkey_popup)
        self.add_widget(self.change_hotkey_btn)

        self.exit_btn = Button(text="Exit", size_hint=(1, 0.1), background_color=(0.1, 0.1, 0.1, 1))
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

    def update_pixel_fov(self, instance, value):
        self.triggerbot.pixel_fov = int(value)
        self.pixel_fov_label.text = f"Pixel FOV: {self.triggerbot.pixel_fov}"
        self.triggerbot.update_grab_zone()
        self.triggerbot.save_config()

    def toggle_triggerbot(self, instance):
        self.triggerbot.paused = not self.triggerbot.paused
        if self.triggerbot.paused:
            self.triggerbot_btn.text = "Start Triggerbot"
            self.triggerbot_btn.background_color = (1, 0, 0, 1)
        else:
            self.triggerbot_btn.text = "Stop Triggerbot"
            self.triggerbot_btn.background_color = (0, 1, 0, 1)

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

    def toggle_humanization(self, value):
        self.triggerbot.humanization = value
        self.triggerbot.save_config()

    def toggle_sticky_aim(self, value):
        self.triggerbot.sticky_aim = value
        if value:
            self.triggerbot.start_sticky_aim()
        else:
            self.triggerbot.stop_sticky_aim()
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

        self.submit_button = Button(text='Submit', background_color=(0.1, 0.1, 0.1, 1))
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
        self.humanization = False
        self.sticky_aim = False
        self.sticky_aim_thread = None
        self.sticky_aim_stop_event = threading.Event()

        self.R = 250 
        self.G = 100 
        self.B = 250 

        with open('config.json') as json_file:
            self.config = json.load(json_file)

        self.trigger_hotkey = int(self.config["trigger_hotkey"], 16)
        self.always_enabled = self.config["always_enabled"]
        self.trigger_delay = self.config["trigger_delay"]
        self.base_delay = self.config["base_delay"]
        self.pixel_fov = self.config["pixel_fov"]
        self.humanization = self.config.get("humanization", False)
        self.sticky_aim = self.config.get("sticky_aim", False)

        self.update_grab_zone()

    def update_grab_zone(self):
        self.grab_zone = calculate_grab_zone(self.pixel_fov)
        logging.debug(f"Updated GRAB_ZONE dimensions: {self.grab_zone}")

    def initialize(self):
        self.sct = dxcam.create(output_color='BGRA', output_idx=0)
        self.initialized = True

        if self.auto_counter_strafe:
            self.setup_auto_counter_strafe()

        if self.sticky_aim:
            self.start_sticky_aim()

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

    def adjust_pointer_speed(self, slow):
        SPI_SETMOUSESPEED = 0x0071
        speed = 1 if slow else 10  # Slow speed = 1, Normal speed = 10
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETMOUSESPEED, 0, speed, 0)
        if slow:
            logging.debug("Pointer speed set to slow")
        else:
            logging.debug("Pointer speed set to normal")

    def searcherino(self):
        if self.paused:
            return
        logging.debug("Grabbing screen...")
        img = np.array(self.sct.grab(self.grab_zone))
        while img.any() == None:
            img = np.array(self.sct.grab(self.grab_zone))

        pixels = img.reshape(-1, 4)
        logging.debug(f"Total pixels scanned: {len(pixels)}")

        logging.debug(f"Sample pixel values (first 10): {pixels[:10, :3]}")

        color_mask = (
                    (pixels[:, 0] > self.R - 25) & (pixels[:, 0] < self.R + 25) &
                    (pixels[:, 1] > self.G - 20) & (pixels[:, 1] < self.G + 20) &
                    (pixels[:, 2] > self.B - 20) & (pixels[:, 2] < self.B + 20)
        )
        matching_pixels = pixels[color_mask]
        logging.debug(f"Found {len(matching_pixels)} matching pixels with tolerance {self.pixel_fov}")

        if self.triggerbot and len(matching_pixels) > 0:
            delay_percentage = self.trigger_delay / 100.0
            actual_delay = self.base_delay + self.base_delay * delay_percentage
            logging.debug(f"Sleeping for {actual_delay} seconds before shooting")
            time.sleep(actual_delay)
            if self.humanization:
                shots = np.random.randint(1, 5)
                for _ in range(shots):
                    keyboard.press_and_release("k")
                    time.sleep(np.random.uniform(0.01, 0.05))
                logging.debug(f"Shot fired {shots} times!")
            else:
                keyboard.press_and_release("k")
                logging.debug("Shot fired!")

    def sticky_aim_scan(self):
        while not self.sticky_aim_stop_event.is_set():
            if self.paused:
                time.sleep(0.1)
                continue
            logging.debug("Grabbing screen for sticky aim...")
            img = np.array(self.sct.grab(self.grab_zone))
            while img.any() == None:
                img = np.array(self.sct.grab(self.grab_zone))

            pixels = img.reshape(-1, 4)
            logging.debug(f"Total pixels scanned for sticky aim: {len(pixels)}")

            logging.debug(f"Sample pixel values for sticky aim (first 10): {pixels[:10, :3]}")

            color_mask = (
                    (pixels[:, 0] > self.R - 15) & (pixels[:, 0] < self.R + 15) &
                    (pixels[:, 1] > self.G - 20) & (pixels[:, 1] < self.G + 20) &
                    (pixels[:, 2] > self.B - 15) & (pixels[:, 2] < self.B + 15)
            )
            matching_pixels = pixels[color_mask]
            logging.debug(f"Found {len(matching_pixels)} matching pixels for sticky aim with tolerance {self.pixel_fov}")

            if len(matching_pixels) > 0:
                self.adjust_pointer_speed(True)
            else:
                self.adjust_pointer_speed(False)

            time.sleep(0.1)

    def start_sticky_aim(self):
        if self.sticky_aim_thread is None or not self.sticky_aim_thread.is_alive():
            self.sticky_aim_stop_event.clear()
            self.sticky_aim_thread = threading.Thread(target=self.sticky_aim_scan)
            self.sticky_aim_thread.start()
            logging.debug("Sticky aim scanning started")

    def stop_sticky_aim(self):
        if self.sticky_aim_thread is not None and self.sticky_aim_thread.is_alive():
            self.sticky_aim_stop_event.set()
            self.sticky_aim_thread.join()
            logging.debug("Sticky aim scanning stopped")

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
        data["pixel_fov"] = self.pixel_fov
        data["auto_counter_strafe"] = self.auto_counter_strafe
        data["humanization"] = self.humanization
        data["sticky_aim"] = self.sticky_aim
        with open('config.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def exiting(self):
        logging.debug("Exiting...")
        self.stop_sticky_aim()
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

    def build(self):
        self.triggerbot.initialize()
        self.triggerbot_thread = threading.Thread(target=self.triggerbot.starterino)
        self.triggerbot_thread.start()

        return SpotifyGUI(self.triggerbot)

if __name__ == "__main__":
    Window.size = (390, 690)

    triggerbot_instance = triggerbot()
    SpotifyApp(triggerbot_instance).run()

UUID = "286f7e5221e6480f96b143d64ca85058"

#7058838634083181522829
#6133973231399143428431
#9878949508561529469839
#7964531536164000166235
#5893615132455524884713
