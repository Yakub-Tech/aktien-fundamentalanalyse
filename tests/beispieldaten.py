import pandas as pd


class BeispielTicker:
    """Fiktive Daten an der externen Schnittstelle, keine historischen Börsendaten."""

    def __init__(self, ticker):
        self.ticker = ticker

    def history(self, start=None, end=None, period=None):
        dates = pd.date_range('2022-01-03', '2026-10-12', freq='B', tz='America/New_York')
        values = pd.Series(range(len(dates)), index=dates) * 0.025 + 75
        frame = pd.DataFrame({'Open': values - 0.5, 'High': values + 1,
                              'Low': values - 1, 'Close': values,
                              'Volume': 100000}, index=dates)
        if start is not None:
            frame = frame.loc[str(start):]
        if end is not None:
            frame = frame.loc[frame.index.date < end]
        if period == '5d':
            frame = frame.tail(5)
        return frame

    @property
    def info(self):
        eps, book, dividend, forward = {
            'AAPL': (5., 40., 2., 18.),
            'MSFT': (4., 30., 1.5, 22.),
            'GOOGL': (3., 25., 0., 25.),
        }.get(self.ticker, (5., 40., 2., 18.))
        return {'marketCap': 1000000000, 'trailingEps': eps,
                'bookValue': book, 'dividendRate': dividend, 'forwardPE': forward}

    @property
    def income_stmt(self):
        return pd.DataFrame({pd.Timestamp(f'{year}-12-31'): [eps]
                             for year, eps in [(2022, 3.5), (2023, 4.), (2024, 4.5), (2025, 5.)]},
                            index=['Diluted EPS'])


