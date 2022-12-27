# import standard packages
import pandas
import configparser
import os

# Import google apis
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# globals
config = configparser.ConfigParser()
configfile = os.path.join(os.path.dirname(__file__), "config.ini")
config.read(configfile)

class Db:
    def __init__(self) -> None:
        _gc = gspread.oauth(credentials_filename='credentials.json',
                            authorized_user_filename='token.json')
        _sheet = _gc.open_by_key(config['DEFAULT']['GSHEET_ID'])
        _ws = _sheet.get_worksheet(0)
        self.df_timerdb = pandas.DataFrame(_ws.get_all_records())

    def get_week_data(self, wk=None):
        df = pandas.DataFrame({
            'date': ['2022-12-26', '2022-12-27'],
            'day': ['Mon', 'Tue'],
            'workday': [1, 1],
            'duration': [7.18, 3.17]
        })
        df.set_index('date', inplace=True)
        return df
