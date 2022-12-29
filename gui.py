# import kivy packages
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput


class MainLayout(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1

        textinput = TextInput(text='Hello world')
        self.add_widget(textinput)

        layout_button = GridLayout(cols=2)
        self.add_widget(layout_button)

        button_start = Button(text='Start')
        button_stop = Button(text='Stop')
        layout_button.add_widget(button_start)
        layout_button.add_widget(button_stop)

class MainApp(App):
    def build(self):
        return MainLayout()

class Gui:
    def __init__(self) -> None:
        pass

    def run(self):
        MainApp().run()
        pass
