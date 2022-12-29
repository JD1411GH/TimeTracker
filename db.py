# import standard packages
import pandas as pd
import configparser
import os
from datetime import *

# Import google apis
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Import local packages
from utils import *

# globals
config = configparser.ConfigParser()
configfile = os.path.join(os.path.dirname(__file__), "config.ini")
config.read(configfile)


class Db:
    def __init__(self) -> None:
        # get google sheet
        self._gspread_read()

        # format the received data for timer
        if self.df_timer.size != 0:
            self.df_timer['start_time'] = pd.to_datetime(self.df_timer['start_time'])
            self.df_timer['end_time'] = pd.to_datetime(self.df_timer['end_time'])

        # format the received data for day
        if self.df_day.size != 0:
            self.df_day['date'] = pd.to_datetime(self.df_day['date']).apply(lambda d: d.date())
            self.df_day.set_index('date', inplace=True)
            self.df_day['correction'] = pd.to_numeric(self.df_day['correction'])

    def _gspread_read(self):
        gc = gspread.oauth(credentials_filename='credentials.json',
                           authorized_user_filename='token.json')
        sheet = gc.open_by_key(config['DEFAULT']['GSHEET_ID'])
        ws = sheet.worksheet('timer')
        self.df_timer = pd.DataFrame(ws.get_all_records())
        ws = sheet.worksheet('day')
        self.df_day = pd.DataFrame(ws.get_all_records())

    def _gspread_write(self):
        # convert timer database from timestamp to string
        def _to_str(timestamp):
            if timestamp is not None and not pd.isnull(timestamp):
                return timestamp.strftime('%Y-%m-%d %X')
            else:
                return ""
        _df_timer = pd.DataFrame()
        _df_timer['start_time'] = self.df_timer['start_time'].apply(_to_str)
        _df_timer['end_time'] = self.df_timer['end_time'].apply(_to_str)

        # write timer to gsheet
        gc = gspread.oauth(credentials_filename='credentials.json',
                        authorized_user_filename='token.json')
        sheet = gc.open_by_key(config['DEFAULT']['GSHEET_ID'])
        ws = sheet.worksheet('timer')
        ws.update([_df_timer.columns.values.tolist()] +
                _df_timer.values.tolist())

        # write day to gsheet
        _df_day = self.df_day.reset_index()
        _df_day['date'] = _df_day['date'].apply(lambda d: d.isoformat())
        ws = sheet.worksheet('day')
        ws.update([_df_day.columns.values.tolist()] +
                _df_day.values.tolist())

    def get_week_data(self, wk=None):
        # check for empty database
        if self.df_timer.size == 0:
            return None

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
            day_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            list_days.append(day_name[idx.weekday()])
        pivot['day'] = list_days

        # add workhours
        pivot = pd.concat([pivot, df_day_filtered['workhours']], axis=1)

        # append correction to duration
        s_duration_s = pivot['duration'].apply(lambda t: t.total_seconds())
        s_duration_s = s_duration_s.add(df_day_filtered['correction'] * 60, fill_value=0)
        s_duration_h = s_duration_s.div(3600).apply(lambda h: round(h,2))
        pivot.drop('duration', axis=1, inplace=True)
        s_duration_h.rename('duration', inplace=True)
        pivot = pd.concat([pivot, s_duration_h], axis=1)

        return pivot

    # return whether start was successful
    def start_timer(self):
        # Check if timer is already started
        if self.df_timer.size == 0:
            # check if empty database
            flgTimerStarted = False
        else :      
            flgTimerStarted = False
            select = self.df_timer['end_time'].isnull()
            rows, _ = self.df_timer[select].shape
            if rows > 1:
                return False
            elif rows == 1:
                flgTimerStarted = True
            else:
                flgTimerStarted = False

        if flgTimerStarted:
            return True
        else:
            # create new timestamp and append to dataframe
            df_start = pd.DataFrame({
                'start_time': [pd.Timestamp.now()],
                'end_time': [None]
            })
            self.df_timer = pd.concat([self.df_timer, df_start], ignore_index=True)
            
            # create entry for day
            _df_day = pd.DataFrame({
                'date': [pd.Timestamp.now().date()],
                'workhours': [config['DEFAULT']['WORKHOURS']],
                'correction': [0]
            })
            _df_day.set_index('date', inplace=True)
            self.df_day = pd.concat([self.df_day, _df_day])

            # write to gsheet
            self._gspread_write()
            return True


    # return whether stop was successful
    def stop_timer(self):
        select = self.df_timer['end_time'].isnull()
        nrows, _ = self.df_timer[select].shape
        if nrows > 1:
            return False
        else:
            idx = self.df_timer[select].index.to_list()[0]
            self.df_timer.iloc[idx]['end_time'] = pd.Timestamp.now()
            self._gspread_write()
            return True
        
