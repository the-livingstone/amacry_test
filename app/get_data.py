from datetime import datetime
from decimal import Decimal
import os
from urllib import request
from zipfile import ZipFile
import pandas as pd

def get_data(url: str) -> pd.DataFrame:
    filename, response = request.urlretrieve(url, 'prices.zip')
    with ZipFile(filename) as unzip:
        unzip.extractall()
    df = pd.read_csv('prices.csv', converters={'PRICE': Decimal}, parse_dates=[0])
    os.remove('prices.csv')
    os.remove('prices.zip')
    for i in os.listdir('__MACOSX'):
        os.remove(f'__MACOSX/{i}')
    os.rmdir('__MACOSX')
    return df