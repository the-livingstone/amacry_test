from dataclasses import dataclass, field
from decimal import Decimal, getcontext
from datetime import datetime
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field

PERIOD = Literal["1min", "5min", "1hour", "1day"]

TIMEFRAME_SPECS: dict[PERIOD, tuple[str, pd.Timedelta]] = {
    "1min": ("min", pd.Timedelta(minutes=1)),
    "5min": ("5min", pd.Timedelta(minutes=5)),
    "1hour": ("h", pd.Timedelta(hours=1)),
    "1day": ("D", pd.Timedelta(days=1)),
}


class Timeframe(BaseModel):
    code: str
    td: pd.Timedelta
    start_date: datetime | None = None
    quotes: list = Field(default_factory=list)

    model_config = dict(arbitrary_types_allowed=True)


@dataclass
class Candle:
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    ts: datetime
    period: PERIOD

    @classmethod
    def from_quotes(cls, name: PERIOD, timeframe: Timeframe) -> "Candle | None":
        if not timeframe.quotes:
            return None
        open_ts: pd.Timestamp = timeframe.quotes[0]["TS"].floor(timeframe.code)
        close_ts: pd.Timestamp = open_ts + timeframe.td
        quotes = [
            x
            for x in timeframe.quotes
            if x["TS"] < close_ts and x["TS"] >= open_ts
        ]
        if not quotes:
            return None
        return cls(
            open_price=quotes[0]["PRICE"],
            high_price=max(x["PRICE"] for x in quotes),
            low_price=min(x["PRICE"] for x in quotes),
            close_price=quotes[-1]["PRICE"],
            volume=sum(x["VOLUME"] for x in quotes),
            ts=open_ts.to_pydatetime(),
            period=name,
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Candle):
            return NotImplemented
        if self.period != other.period:
            return NotImplemented
        return self.ts < other.ts


@dataclass
class MarketData:
    quotes: pd.DataFrame = field(default_factory=pd.DataFrame)

    candles_1min: list[Candle] = field(init=False)
    candles_5min: list[Candle] = field(init=False)
    candles_1hour: list[Candle] = field(init=False)
    candles_1day: list[Candle] = field(init=False)

    def __post_init__(self) -> None:
        getcontext().prec = 12
        self.candles_1min = []
        self.candles_5min = []
        self.candles_1hour = []
        self.candles_1day = []
        if self.quotes.empty:
            return
        self.quotes.sort_values(by="TS", inplace=True)
        candles = self._build_candles_from_quotes()
        self.candles_1min = candles["1min"]
        self.candles_5min = candles["5min"]
        self.candles_1hour = candles["1hour"]
        self.candles_1day = candles["1day"]

    def candles_for_period(self, period: PERIOD) -> list[Candle]:
        return {
            "1min": self.candles_1min,
            "5min": self.candles_5min,
            "1hour": self.candles_1hour,
            "1day": self.candles_1day,
        }[period]

    def _build_candles_from_quotes(self) -> dict[PERIOD, list[Candle]]:
        timeframe = {
            name: Timeframe(code=code, td=td)
            for name, (code, td) in TIMEFRAME_SPECS.items()
        }
        candles: dict[PERIOD, list[Candle]] = {name: [] for name in TIMEFRAME_SPECS}

        for _, row in self.quotes.iterrows():
            for name, tf in timeframe.items():
                if tf.start_date is None:
                    tf.start_date = row["TS"].floor(tf.code)
                current_ts = row["TS"]
                if current_ts < tf.start_date + tf.td:
                    tf.quotes.append(row)
                    continue
                candle = Candle.from_quotes(name, tf)
                if candle is not None:
                    candles[name].append(candle)
                tf.quotes = [row]
                tf.start_date = row["TS"].floor(tf.code)

        for name, tf in timeframe.items():
            if not tf.quotes:
                continue
            candle = Candle.from_quotes(name, tf)
            if candle is not None:
                candles[name].append(candle)

        return candles

    def calc_SMA(
        self, n: int, candles: list[Candle] | None = None
    ) -> list[tuple[datetime, Decimal]]:
        series = candles if candles is not None else self.candles_1day
        window: list[tuple[datetime, Decimal]] = []
        result: list[tuple[datetime, Decimal]] = []
        for c in series:
            window.append((c.ts, c.close_price))
            if len(window) < n:
                continue
            sma = sum(x[1] for x in window) / n
            result.append((c.ts, sma))
            window.pop(0)
        return result

    def calc_EMA(self, n: int, period: PERIOD = "1day") -> list[tuple[datetime, Decimal]]:
        candles = self.candles_for_period(period)
        sma_values = self.calc_SMA(n, candles)
        if not sma_values:
            return []

        smoothing = Decimal(2 / (n + 1))
        first_sma = sma_values[0]
        ema = first_sma[1]
        result: list[tuple[datetime, Decimal]] = []
        for c in candles:
            if c.ts <= first_sma[0]:
                continue
            ema = c.close_price * smoothing + ema * (1 - smoothing)
            result.append((c.ts, ema))
        return result
