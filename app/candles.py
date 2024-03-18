from dataclasses import dataclass, field
from decimal import Decimal, getcontext
from datetime import datetime
from typing import Literal
import pandas as pd
from pydantic import BaseModel, Field


PERIOD = Literal["1min", "5min", "1hour", "1day"]

class Timeframe(BaseModel):
    code: str
    td: pd.Timedelta
    start_date: datetime | None = None
    quotes: list = Field(default_factory=list)

    model_config=dict(arbitrary_types_allowed=True)
@dataclass
class Candle:
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    ts: datetime
    period: PERIOD

    @classmethod
    def from_prices(cls, name: str, timeframe: Timeframe):
        if not timeframe:
            return None
        open_ts: pd.Timestamp = timeframe.quotes[0]["TS"].floor(timeframe.code)
        close_ts: pd.Timestamp = open_ts + timeframe.td
        quotes = [x for x in timeframe.quotes if x["TS"] < close_ts and x["TS"] >= open_ts]
        open_price: Decimal = quotes[0]["PRICE"]
        high_price: Decimal = max([x["PRICE"] for x in quotes])
        low_price: Decimal = min([x["PRICE"] for x in quotes])
        close_price: Decimal = quotes[-1]["PRICE"]
        return cls(
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            ts=open_ts.to_pydatetime(),
            period=name,
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
        self.quotes.sort_values(by="TS", inplace=True)
        candles = self.mk_candles_iterrows()
        self.candles_1min = candles["1min"]
        self.candles_5min = candles["5min"]
        self.candles_1hour = candles["1hour"]
        self.candles_1day = candles["1day"]

    def mk_candles_iterrows(self) -> dict[PERIOD, Candle]:
        timeframe = {
            "1min": Timeframe(code="T", td=pd.Timedelta(1, "T")),
            "5min": Timeframe(code="5T", td=pd.Timedelta(5, "T")),
            "1hour": Timeframe(code="H", td=pd.Timedelta(1, "H")),
            "1day": Timeframe(code="D", td=pd.Timedelta(1, "D"))
        }
        candles = {}
        for i, row in self.quotes.iterrows():
            for name, tf in timeframe.items():
                if not tf.start_date:
                    tf.start_date = row["TS"].floor(tf.code)
                current_ts = row["TS"]
                if current_ts < tf.start_date + tf.td:
                    tf.quotes.append(row)
                    continue
                candles.setdefault(name, []).append(
                    Candle.from_prices(name, tf)
                )
                tf.quotes = [row]
                tf.start_date = row["TS"].floor(tf.code)
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
