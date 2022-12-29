# import kivy packages
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

# import main packages
from datetime import *

# import local packages
from db import Db


class Logger:
    def __init__(self, textinput) -> None:
        self.textinput = textinput

    def log(self, msg):
        self.textinput.text += f"[{datetime.now()}] {msg} \n"


class MainLayout(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1

        self.textinput = TextInput()
        self.add_widget(self.textinput)

        layout_button = GridLayout(cols=3)
        self.add_widget(layout_button)

        button_refresh = Button(text='Refresh')
        button_start = Button(text='Start')
        button_stop = Button(text='Stop')
        layout_button.add_widget(button_refresh)
        layout_button.add_widget(button_start)
        layout_button.add_widget(button_stop)

        button_start.bind(on_press=self.refresh)
        button_start.bind(on_press=self.start)
        button_stop.bind(on_press=self.stop)

        self.logger = Logger(self.textinput)
        self.refresh(None)

    def refresh(self, instance):
        self.logger.log("Reloading database...")
        self.db = None
        self.db = Db()
        if self.db.is_timer_running():
            self.logger.log("Timer is running")
        else:
            self.logger.log("Timer is stopped")

    def start(self, instance):
        self.refresh(instance)
        if not self.db.is_timer_running():
            status = self.db.start_timer()
            if not status:
                self.logger.log("Timer could not be started")
            else:
                self.logger.log("Timer started")
        else:
            self.logger.log("Timer is already running")

    def stop(self, instance):
        self.refresh(instance)
        status = self.db.stop_timer()
        if not status:
            self.logger.log("Timer could not be stopped")
        else:
            self.logger.log("Timer stopped")


class MainApp(App):
    def build(self):
        return MainLayout()
