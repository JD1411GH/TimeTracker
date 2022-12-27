import pandas


class Db:
    def __init__(self) -> None:
        pass

    def get_week_data(self, wk=None):
        df = pandas.DataFrame({
            'date': ['2022-12-26', '2022-12-27'],
            'day': ['Mon', 'Tue'],
            'workday': [1, 1],
            'duration': [7.18, 3.17]
        })
        df.set_index('date', inplace=True)
        return df
