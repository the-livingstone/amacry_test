from datetime import datetime
from decimal import Decimal
import os
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, callback, Input, Output, ctx
import dash_daq as daq
from candles import MarketData, Candle
from get_data import get_data
import pandas as pd

df = get_data(os.getenv('PRICES_URL'))
md = MarketData(df)
ema = md.calc_EMA(5)
app = Dash()

candles = go.Candlestick(
    x=[y.ts for y in md.candles_1day],
    open=[y.open_price for y in md.candles_1day],
    high=[y.high_price for y in md.candles_1day],
    low=[y.low_price for y in md.candles_1day],
    close=[y.close_price for y in md.candles_1day],
    name='1day'
)

ema_line = go.Line(
    x=[e[0] for e in ema],
    y=[e[1] for e in ema],
    name='EMA'
)

chart = html.Div(
    children=dcc.Graph(
        figure=go.Figure(
            data=[
                candles,
                ema_line
            ]
        ),
        id='chart'
    ),
    id='chart_container'
)

controls = [
    html.Div([
        html.Button('1min', id='candles_1min', n_clicks=0),
        html.Button('5min', id='candles_5min', n_clicks=0),
        html.Button('1hour', id='candles_1hour', n_clicks=0),
        html.Button('1day', id='candles_1day', n_clicks=0)
    ]),
    html.Div([
        daq.NumericInput(
                id='ema_days',
                value=5,
                min=1,
                max=100,
                label='EMA window (days)',
                labelPosition='bottom'
            )
    ])
]


table = html.Table(
    children=html.Tbody(
        children=html.Tr(
            children=[
                html.Td(
                    children=chart
                ),
                html.Td(
                    children=controls
                )
            ]
        )
    ),
    style={
        'width': '100%'
    }
)

app.layout = html.Div(children=[table])

@callback(
    Output('chart_container', 'children'),
    Input('candles_1min', 'n_clicks'),
    Input('candles_5min', 'n_clicks'),
    Input('candles_1hour', 'n_clicks'),
    Input('candles_1day', 'n_clicks'),
    Input('ema_days', 'value'),
    Input('chart', 'figure')
)
def display_candles(
        candles_1min,
        candles_5min,
        candles_1hour,
        candles_1day,
        ema_days,
        figure: go.Figure
    ):
    data = figure['data']
    period = {
        "candles_1min": md.candles_1min, 
        "candles_5min": md.candles_5min,
        "candles_1hour": md.candles_1hour,
        "candles_1day": md.candles_1day
    }
    if ctx.triggered_id in period:
        candles = {
            'x': [x.ts for x in period[ctx.triggered_id]],
            'open': [x.open_price for x in period[ctx.triggered_id]],
            'high': [x.high_price for x in period[ctx.triggered_id]],
            'low': [x.low_price for x in period[ctx.triggered_id]],
            'close': [x.close_price for x in period[ctx.triggered_id]],
            'name': ctx.triggered_id.split('_')[1]
        }
        data[0] = go.Candlestick(**candles)
    ema = md.calc_EMA(ema_days)
    data[1] = go.Line(
        x=[e[0] for e in ema],
        y=[e[1] for e in ema],
        name=f'EMA {ema_days} days'
    )
    return dcc.Graph(figure=go.Figure(data=data), id='chart')


app.run(debug=True, use_reloader=False)