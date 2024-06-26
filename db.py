# import standard packages
from select import select
import pandas as pd
import configparser
import os
from datetime import *
import threading

# Import google apis
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Import local packages
from utils import *

# globals
config = configparser.ConfigParser()
configfile = os.path.join(os.path.dirname(__file__), "config.ini")
config.read(configfile)
lock = threading.Lock()


class Db:
    def __init__(self) -> None:
        # get google sheet
        self._gspread_read()

        # format the received data for timer
        if self.df_timer.size != 0:
            self.df_timer['start_time'] = pd.to_datetime(
                self.df_timer['start_time'])
            self.df_timer['end_time'] = pd.to_datetime(
                self.df_timer['end_time'])

        # format the received data for day
        if self.df_day.size != 0:
            self.df_day['date'] = pd.to_datetime(
                self.df_day['date']).apply(lambda d: d.date())
            self.df_day.set_index('date', inplace=True)
            self.df_day['correction'] = pd.to_numeric(
                self.df_day['correction'])
            self.df_day['workhours'] = pd.to_numeric(self.df_day['workhours'])

        # default initilize some instance variables
        self.th_timer = None
        self.th_day = None

    def _gspread_read(self):
        gc = gspread.service_account(filename="service_account.json")
        sheet = gc.open_by_key(config['DEFAULT']['GSHEET_ID'])
        ws = sheet.worksheet('timer')
        self.df_timer = pd.DataFrame(ws.get_all_records())
        ws = sheet.worksheet('day')
        self.df_day = pd.DataFrame(ws.get_all_records())

    def _savedb(self):
        # function to write to gspread
        # scoping it so that it can't be called elsewhere
        def _gspread_write(tab, data):
            global lock
            lock.acquire()
            gc = gspread.service_account(filename="service_account.json")
            sheet = gc.open_by_key(config['DEFAULT']['GSHEET_ID'])
            ws = sheet.worksheet(tab)
            ws.update([data.columns.values.tolist()] + data.values.tolist())
            lock.release()

        # convert timer database from timestamp to string
        def _to_str(timestamp):
            if timestamp is not None and not pd.isnull(timestamp):
                return timestamp.strftime('%Y-%m-%d %X')
            else:
                return ""

        # write timer sheet
        _df_timer = pd.DataFrame()
        _df_timer['start_time'] = self.df_timer['start_time'].apply(_to_str)
        _df_timer['end_time'] = self.df_timer['end_time'].apply(_to_str)
        self.th_timer = threading.Thread(
            target=_gspread_write, args=['timer', _df_timer])
        self.th_timer.start()

        # prepare day for gsheet
        _df_day = self.df_day.reset_index()
        _df_day['date'] = _df_day['date'].apply(lambda d: d.isoformat())
        self.th_day = threading.Thread(
            target=_gspread_write, args=['day', _df_day])
        self.th_day.start()

    def _add_day(self, dat=None, correction=0, workhours=float(config['DEFAULT']['WORKHOURS']), HOP=0):
        if dat is None:
            dat = pd.Timestamp.today().date()
        if dat not in self.df_day.index.to_list():
            _df_day = pd.DataFrame({
                'date': [dat],
                'workhours': [workhours],
                'correction': [correction],
                'HOP': [HOP]
            })
            _df_day.set_index('date', inplace=True)
            self.df_day = pd.concat([self.df_day, _df_day])
        # invoke self._savedb() from the calling function

    def is_save_ongoing(self):
        is_alive = False
        if self.th_timer and self.th_timer.is_alive():
            is_alive = True
        if self.th_day and self.th_day.is_alive():
            is_alive = True
        return is_alive

    def is_valid(self):
        # check for multiple started timer
        select = pd.isnull(self.df_timer['end_time'])
        nrows, _ = self.df_timer[select].shape
        if nrows > 1:
            return False
        else:
            return True

    def is_first_entry_of_day(self):
        today = pd.Timestamp.now().date()
        if today not in self.df_day.index.to_list():
            return True
        else:
            return False

    def get_week_data(self, wk=None):
        # check for empty database
        if self.df_timer.size == 0:
            return (None, None)

        # filter for current week
        if wk is None:
            curweek = pd.Timestamp.today().week
        else:
            curweek = wk
        select = self.df_timer['start_time'].apply(lambda x: x.week) == curweek
        df_timer_filtered = self.df_timer[select]
        select = self.df_day.index.to_series().apply(
            lambda x: x.isocalendar()[1]) == curweek
        df_day_filtered = self.df_day[select]
        if df_timer_filtered.size == 0 or df_day_filtered.size == 0:
            return (None, None)

        # create date and duration column
        s_date = df_timer_filtered['start_time'].apply(lambda t: t.date())
        s_date.rename('date', inplace=True)
        df_timer_filtered = pd.concat([df_timer_filtered, s_date], axis=1)
        s_duration = df_timer_filtered['end_time'] - \
            df_timer_filtered['start_time']
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
        s_duration_s = s_duration_s.add(
            df_day_filtered['correction'] * 60, fill_value=0)
        s_duration_h = s_duration_s.div(3600)
        pivot.drop('duration', axis=1, inplace=True)
        s_duration_h.rename('duration', inplace=True)
        pivot = pd.concat([pivot, s_duration_h], axis=1)

        # add hours since timer start
        if wk is None and self.is_timer_running():
            now = pd.Timestamp.today()
            select = pd.isnull(df_timer_filtered['end_time'])
            start = df_timer_filtered[select]['start_time'].to_list()[0]
            duration_running = (now - start).total_seconds() / 3600
            pivot.at[start.date(), 'duration'] = duration_running + \
                pivot.loc[start.date()]['duration']

        # round off duration to 2 decimal places
        pivot['duration'] = pivot['duration'].apply(lambda x: round(x, 2))

        # HOP data
        pivot['HOP'] = df_day_filtered['HOP']

        # calculate weekly deficit
        required_hours = df_day_filtered['workhours'].sum()
        actual_hours = pivot['duration'].sum()
        deficit_week = round((required_hours - actual_hours), 2)

        return (pivot, deficit_week)

    def get_hop_count(self, month=datetime.today().month):
        select = self.df_day.index.to_series().apply(
            lambda x: x.month) == month
        df_month = self.df_day[select]
        return df_month['HOP'].sum()

    def get_deficit_overall(self):
        # required hours calculation
        required_hours = self.df_day['workhours'].sum()

        # actual hours calculation
        s_delta = (self.df_timer['end_time'] - self.df_timer['start_time'])
        duration_hours = s_delta.sum().total_seconds() / 3600
        correction_hours = self.df_day['correction'].sum() / 60
        deficit_overall = required_hours - (duration_hours + correction_hours)

        # add hours since timer start
        if self.is_timer_running():
            now = pd.Timestamp.today()
            select = pd.isnull(self.df_timer['end_time'])
            start = self.df_timer[select]['start_time'].to_list()[0]
            duration_running = (now - start).total_seconds() / 3600
            deficit_overall -= duration_running

        return (round(deficit_overall, 2))

    def is_timer_running(self):
        if self.df_timer.size == 0:
            # check if empty database
            flgTimerRunning = False
        else:
            flgTimerRunning = False
            select = pd.isnull(self.df_timer['end_time'])
            rows, _ = self.df_timer[select].shape
            if rows > 1:
                return False
            elif rows == 1:
                flgTimerRunning = True
            else:
                flgTimerRunning = False
        return flgTimerRunning

    def set_hop(self, value, dat=None):
        # handle default value
        if dat== None:
            dat = pd.Timestamp.today().date()
        else:
            dat = pd.Timestamp(dat).date()
            
        # if dat is not in the database, add it
        if dat not in self.df_day.index.to_list():
            self._add_day(dat)

        # mark HOP for the date
        self.df_day.at[dat, 'HOP'] = value
        self._savedb()


    # return whether start was successful
    def start_timer(self):
        # Check if timer is already started
        # TODO: violation of single responsibility. db shall not be aware of timer.
        if self.is_timer_running():
            return True
        else:
            # create new timestamp and append to dataframe
            df_start = pd.DataFrame({
                'start_time': [pd.Timestamp.now()],
                'end_time': [None]
            })
            self.df_timer = pd.concat(
                [self.df_timer, df_start], ignore_index=True)

        # create entry for today
        today = pd.Timestamp.now().date()
        if today not in self.df_day.index.to_list():
            self._add_day()

        # write to gsheet
        self._savedb()
        return True

    # return whether stop was successful

    def stop_timer(self):
        select = self.df_timer['end_time'].isnull()
        nrows, _ = self.df_timer[select].shape
        if nrows > 1:
            return False
        else:
            idx = self.df_timer[select].index.to_list()[0]
            col = self.df_timer.columns.to_list().index('end_time')
            self.df_timer.iat[idx,col] = pd.Timestamp.now()
            self._savedb()
            return True

    # cor is in mins and is written as is
    def add_correction(self, cor):
        today = pd.Timestamp.today().date()
        curval = self.df_day.loc[today]['correction']
        new_value = curval + cor
        self.df_day.at[today, 'correction'] = new_value
        self._savedb()

    # update work hours in days sheet
    def update_workhours(self, date, hours):
        self.df_day.at[date, 'workhours'] = hours
        self._savedb()
