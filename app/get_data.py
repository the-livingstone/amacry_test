from datetime import datetime
from decimal import Decimal
from pathlib import Path
import pandas as pd

def convert_ts(ts: str) -> datetime:
    return datetime.fromtimestamp(int(ts))

def get_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, converters={'TS': convert_ts, 'PRICE': Decimal, 'VOLUME': Decimal})
    return df
