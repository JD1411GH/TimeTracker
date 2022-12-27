# import standard packages
import pandas as pd
import configparser
import os
from datetime import date, timedelta

# Import google apis
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# globals
config = configparser.ConfigParser()
configfile = os.path.join(os.path.dirname(__file__), "config.ini")
config.read(configfile)


class Db:
    def __init__(self) -> None:
        gc = gspread.oauth(credentials_filename='credentials.json',
                           authorized_user_filename='token.json')
        sheet = gc.open_by_key(config['DEFAULT']['GSHEET_ID'])
        ws = sheet.get_worksheet(0)
        self.df_timerdb = pd.DataFrame(ws.get_all_records())
        self.df_timerdb['date'] = pd.to_datetime(self.df_timerdb['date'])
        self.df_timerdb.set_index('date', inplace=True)
        self.df_timerdb['duration'] = pd.to_numeric(
            self.df_timerdb['duration'])

    def get_week_data(self, wk=None):
        pivot = pd.pivot_table(data=self.df_timerdb,
                               index='date', values='duration', aggfunc='sum')

        today = date.today()
        start = today - timedelta(days=today.weekday())
        startdate = pd.to_datetime(start)
        enddate = pd.to_datetime(start + timedelta(days=6))

        filter = pivot.index.to_series().between(startdate, enddate)
        return pivot[filter]
