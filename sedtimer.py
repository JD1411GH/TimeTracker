# import standard packages
from threading import Thread
import configparser
import os
from datetime import timedelta
import time

# globals
config = configparser.ConfigParser()
configfile = os.path.join(os.path.dirname(__file__), "config.ini")
config.read(configfile)


class SedTimer:
    def __init__(self, handler) -> None:
        self.th_sed = Thread(target=self._th_timer, args=[handler,])
        self.flg_cancel = False
        self.flg_stop = False

    def _th_timer(self, handler):
        init = int(config['DEFAULT']['SED_TIMER'])
        eta = timedelta(minutes=init)
        while not self.flg_stop:
            time.sleep(1)
            eta -= timedelta(seconds=1)
            if eta.total_seconds() <= 0:
                handler("Time to take a walk")
                eta = timedelta(minutes=init)

    def is_running(self):
        return self.th_sed.is_alive()

    def start(self):
        if not self.flg_cancel:
            self.th_sed.start()

    def stop(self):
        if self.is_running():
            self.flg_stop = True

    def cancel(self):
        self.flg_stop = True
        self.flg_cancel = True
