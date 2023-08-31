from dataclasses import dataclass, field
from decimal import Decimal, getcontext
from datetime import datetime
from typing import Literal, Union
import pandas as pd


PERIOD = Literal[
    '1min',
    '5min',
    '1hour',
    '1day'
]

@dataclass
class Candle:
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    ts: datetime
    period: PERIOD

    @classmethod
    def from_prices(cls, timeframe: list[dict], period: PERIOD):
        pd_periods = {
            '1min': 'T',
            '5min': '5T',
            '1hour': 'H',
            '1day': 'D'
        }
        td = pd.Timedelta(
            5 if period == '5min' else 1,
            pd_periods[period][-1]
        )
        if not timeframe:
            return None
        open_ts: pd.Timestamp = timeframe[0]['TS'].floor(pd_periods[period])
        close_ts: pd.Timestamp = open_ts + td
        timeframe = [
            x for x
            in timeframe
            if x['TS'] < close_ts
            and x['TS'] >= open_ts
        ]
        open_price: Decimal = timeframe[0]['PRICE']
        high_price: Decimal = max([x['PRICE'] for x in timeframe])
        low_price: Decimal = min([x['PRICE'] for x in timeframe])
        close_price: Decimal = timeframe[-1]['PRICE']
        return cls(
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            ts=open_ts.to_pydatetime(),
            period=period
        )
    
    def __lt__(self, other):
        if self.period == other.period:
            if self.ts < other.ts:
                return True
            return False
        return None

@dataclass
class MarketData:
    quotes: pd.DataFrame = field(default_factory=pd.DataFrame())
    candles_1min: list[Candle] = field(init=False)
    candles_5min: list[Candle] = field(init=False)
    candles_1hour: list[Candle] = field(init=False)
    candles_1day: list[Candle] = field(init=False)

    def __post_init__(self):
        getcontext().prec = 12
        if self.quotes.empty:
            return None
        self.quotes.sort_values(by='TS', inplace=True)
        self.candles_1min = self.mk_candles_iterrows('1min')
        self.candles_5min = self.mk_candles_iterrows('5min')
        self.candles_1hour = self.mk_candles_iterrows('1hour')
        self.candles_1day = self.mk_candles_iterrows('1day')    
    
    def mk_candles_iterrows(self, period: PERIOD) -> list[Candle]:
        pd_periods = {
            '1min': 'T',
            '5min': '5T',
            '1hour': 'H',
            '1day': 'D'
        }
        td = pd.Timedelta(
            5 if period == '5min' else 1,
            pd_periods[period][-1]
        )
        candles = []
        start_date = None
        candle_quotes = []
        for i, row in self.quotes.iterrows():
            if not start_date:
                start_date = row['TS'].floor(pd_periods[period])
            current_ts = row['TS']
            if current_ts < start_date + td:
                candle_quotes.append(row)
                continue
            candles.append(Candle.from_prices(candle_quotes, period))
            candle_quotes = [row]
            start_date = row['TS'].floor(pd_periods[period])
        return candles
    
    def calc_SMA(self, n: int) -> list[tuple[datetime, Decimal]]:
        # Simple moving average is calculated as sum of close prices of candles_1day for <<n>> number of previous days,
        # divided by <<n>> for every day greater than <<n>>th day
        window = []
        result = []
        for c in self.candles_1day:
            window.append((c.ts, c.close_price))
            # keep appending days until window size is equal to n
            if len(window) < n:
                continue
            # calculate sma
            sma = sum(x[1] for x in window) / n
            # append calculated value along with the day timestamp
            result.append((c.ts, sma))
            # remove most right day from the window
            window.pop(0)
        return result

    def calc_EMA(self, n: int) -> list[tuple[datetime, Decimal]]:
        # Exponential moving average is calculated as day close price multiplied by smoothing coefficient
        # plus EMA value of previous day multiplied by 1 - smoothing coefficient.
        # The base value for the first EMA calculation is SMA for the same window size.
        # The smoothing coefficient is dependent of window size and calculated as 2 / (1 + n), where n is the size of the window
        result = []
        smoothing = Decimal(2 / (n + 1))
        # calculate SMA for the first window
        first_sma = self.calc_SMA(n)[0]
        ema = first_sma[1]
        for c in self.candles_1day:
            # don't calculate anything before the left edge of the window reaches SMA timestamp
            if c.ts <= first_sma[0]:
                continue
            # calculate ema
            ema = c.close_price * smoothing + ema * (1 - smoothing)
            result.append((c.ts, ema))
        return result
