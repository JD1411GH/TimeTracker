# import kivy packages
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button


class MainLayout(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        self.add_widget(Label(text="Name: "))


class MainApp(App):
    def build(self):
        return MainLayout()

class Gui:
    def __init__(self) -> None:
        pass

    def run(self):
        MainApp().run()
