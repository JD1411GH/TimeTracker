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
        self.df_timer['start_time'] = pd.to_datetime(self.df_timer['start_time'])
        self.df_timer['end_time'] = pd.to_datetime(self.df_timer['end_time'])

        # format the received data for day
        self.df_day['date'] = pd.to_datetime(self.df_day['date']).apply(lambda d: d.date())
        self.df_day.set_index('date', inplace=True)
        self.df_day['correction'] = pd.to_numeric(
            self.df_day['correction'])

    def get_week_data(self, wk=None):
        # filter for current week
        if wk is None:
            curweek = pd.Timestamp.today().week
        else:
            curweek = wk
        filter = self.df_timer['start_time'].apply(lambda x: x.week) == curweek
        df_timer_filtered = self.df_timer[filter]
        filter = self.df_day.index.to_series().apply(lambda x: x.isocalendar()[1]) == curweek
        df_day_filtered = self.df_day[filter]

        # create date and duration column
        s_date = df_timer_filtered['start_time'].apply(lambda t: t.date())
        s_date.rename('date', inplace=True)
        df_timer_filtered = pd.concat([df_timer_filtered, s_date], axis=1)
        s_duration = df_timer_filtered['end_time'] - df_timer_filtered['start_time']
        s_duration.rename('duration', inplace=True)
        df_timer_filtered = pd.concat([df_timer_filtered, s_duration], axis=1)        

        # create pivot day-wise
        pivot = pd.pivot_table(data=df_timer_filtered,
                               index='date', values='duration', aggfunc='sum')
        
        # add day of week
        list_days = []
        for (idx, row) in pivot.iterrows():
            day_name = ['Monday', 'Tuesday', 'Wednesday',
                        'Thursday', 'Friday', 'Saturday', 'Sunday']
            list_days.append(day_name[idx.weekday()])
        pivot['day'] = list_days

        # add workday
        pivot = pd.concat([pivot, df_day_filtered['workday']], axis=1)

        # append correction to duration
        s_duration_s = pivot['duration'].apply(lambda t: t.total_seconds())
        s_duration_s = s_duration_s.add(df_day_filtered['correction'], fill_value=0)
        s_duration_h = s_duration_s.div(3600).apply(lambda h: round(h,2))
        pivot.drop('duration', axis=1, inplace=True)
        s_duration_h.rename('duration', inplace=True)
        pivot = pd.concat([pivot, s_duration_h], axis=1)

        print(self.df_timer)
        return pivot
