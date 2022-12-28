# import standard packages
import pandas as pd
import configparser
import os
from datetime import *

# Import google apis
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# globals
config = configparser.ConfigParser()
configfile = os.path.join(os.path.dirname(__file__), "config.ini")
config.read(configfile)


class Db:
    def __init__(self) -> None:
        # get google sheet
        gc = gspread.oauth(credentials_filename='credentials.json',
                           authorized_user_filename='token.json')
        sheet = gc.open_by_key(config['DEFAULT']['GSHEET_ID'])
        ws = sheet.worksheet('timer')
        self.df_timer = pd.DataFrame(ws.get_all_records())
        ws = sheet.worksheet('day')
        self.df_day = pd.DataFrame(ws.get_all_records())

        # format the received data for timer
        self.df_timer.set_index('id', inplace=True)
        self.df_timer['date'] = pd.to_datetime(self.df_timer['date'])
        self.df_timer['duration'] = pd.to_numeric(
            self.df_timer['duration'])

        # format the received data for day
        self.df_day['date'] = pd.to_datetime(self.df_day['date'])
        self.df_day.set_index('date', inplace=True)
        self.df_day['correction'] = pd.to_numeric(
            self.df_day['correction'])


    def get_week_data(self, wk=None):
        # filter for current week
        if wk is None:
            curweek = pd.Timestamp.today().week
        else:
            curweek = wk
        filter = self.df_timer['date'].apply(lambda x: x.week) == curweek
        df_timer_filtered = self.df_timer[filter]
        filter = self.df_day.index.to_series().apply(lambda x: x.week) == curweek
        df_day_filtered = self.df_day[filter]

        # create pivot day-wise
        pivot = pd.pivot_table(data=df_timer_filtered,
                               index='date', values='duration', aggfunc='sum')
        
        # add day of week
        list_days = []
        for (idx, row) in pivot.iterrows():
            day_name = ['Monday', 'Tuesday', 'Wednesday',
                        'Thursday', 'Friday', 'Saturday', 'Sunday']
            list_days.append(day_name[idx.dayofweek])
        pivot['day'] = list_days

        # add workday status
        pivot = pd.concat([pivot, df_day_filtered['workday']], axis=1)

        # calculate duration
        s_duration = pivot['duration'].add(df_day_filtered['correction'])
        pivot.drop('duration', axis=1, inplace=True)
        s_duration.rename('duration', inplace=True)
        pivot = pd.concat([pivot, s_duration], axis=1)

        return pivot
