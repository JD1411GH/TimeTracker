# import global packages
from ast import arg
from threading import Thread
from timeit import repeat
import easygui

# import local packages
from menu import *
from db import *
from utils import *
from sedtimer import SedTimer


class Cli:
    def __init__(self) -> None:
        self.th_main = Thread(target=self._th_main)
        self.db = Db()
        self.sed = SedTimer(self._handler_sed)

    def _th_main(self):
        if self.db.is_timer_running():
            self.sed.start()
        self.show_menu()

    def _handler_sed(self, str):
        repeat = easygui.ynbox(str,
                               "Sedentary reminder", ('Repeat', 'Don\'t Repeat'))
        if not repeat:
            self.sed.cancel()

    def run(self):
        self.th_main.start()


    def show_menu(self):
        self.show_stats()
        menu = Menu()
        menu.add(MenuItem("Start Timer", self.start_timer))
        menu.add(MenuItem("Stop Timer", self.stop_timer))
        menu.add(MenuItem("Refresh", self.show_menu))
        menu.add(MenuItem("Time Correction", self.add_correction))
        menu.add(MenuItem("Mark holiday / half day", self.mark_day))
        menu.add(MenuItem("Show previous records", self.show_prev_stats))
        while True:
            menu.show()

    def show_stats(self, wk=None):
        (df, deficit_week) = self.db.get_week_data(wk)
        if df is not None:
            mycls()
            print(df)
            print()
            print(f"weekly deficit: {deficit_week}")

        deficit_overall = self.db.get_deficit_overall()
        print(f"overall deficit: {deficit_overall}")

        print(f"timer running: {self.db.is_timer_running()}")

    def start_timer(self):
        # start the task timer
        if not self.db.is_timer_running():
            status = self.db.start_timer()
            myassert(status, "Timer could not be started")

        # start the sedentary timer
        if not self.sed.is_running():
            self.sed.start()

        self.show_menu()

    def stop_timer(self):
        status = self.db.stop_timer()
        myassert(status, "Timer could not be stopped")
        self.show_menu()

    def add_correction(self):
        cor = input("Enter mins to add: ")
        self.db.add_correction(int(cor))
        self.show_menu()

    def mark_day(self):
        self.show_menu()

    def show_prev_stats(self):
        self.show_menu()
