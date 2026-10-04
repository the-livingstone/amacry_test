from pathlib import Path

import dash_daq as daq
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, callback, ctx, dcc, html

from app.candles import PERIOD, MarketData
from app.config import config
from app.get_data import get_data

PERIOD_BY_BUTTON: dict[str, PERIOD] = {
    "candles_1min": "1min",
    "candles_5min": "5min",
    "candles_1hour": "1hour",
    "candles_1day": "1day",
}

DEFAULT_PERIOD: PERIOD = "1day"
DEFAULT_EMA_WINDOW = 5


def _load_market_data() -> MarketData:
    return MarketData(get_data(Path(config.DATA_FILE)))


def build_figure(md: MarketData, period: PERIOD, ema_window: int) -> go.Figure:
    candles = md.candles_for_period(period)
    traces: list = [
        go.Candlestick(
            x=[c.ts for c in candles],
            open=[c.open_price for c in candles],
            high=[c.high_price for c in candles],
            low=[c.low_price for c in candles],
            close=[c.close_price for c in candles],
            name=period,
        )
    ]
    ema = md.calc_EMA(ema_window, period)
    if ema:
        traces.append(
            go.Scatter(
                x=[e[0] for e in ema],
                y=[e[1] for e in ema],
                mode="lines",
                name=f"EMA {ema_window}",
            )
        )
    figure = go.Figure(data=traces)
    figure.update_layout(xaxis_rangeslider_visible=False)
    return figure


def create_app(md: MarketData | None = None) -> Dash:
    market_data = md if md is not None else _load_market_data()
    app = Dash(__name__)

    app.layout = html.Div(
        children=[
            dcc.Store(id="active_period", data=DEFAULT_PERIOD),
            html.Table(
                children=html.Tbody(
                    children=html.Tr(
                        children=[
                            html.Td(
                                children=dcc.Graph(
                                    id="chart",
                                    figure=build_figure(
                                        market_data, DEFAULT_PERIOD, DEFAULT_EMA_WINDOW
                                    ),
                                )
                            ),
                            html.Td(
                                children=[
                                    html.Div(
                                        [
                                            html.Button(
                                                "1min", id="candles_1min", n_clicks=0
                                            ),
                                            html.Button(
                                                "5min", id="candles_5min", n_clicks=0
                                            ),
                                            html.Button(
                                                "1hour",
                                                id="candles_1hour",
                                                n_clicks=0,
                                            ),
                                            html.Button(
                                                "1day", id="candles_1day", n_clicks=0
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            daq.NumericInput(
                                                id="ema_window",
                                                value=DEFAULT_EMA_WINDOW,
                                                min=1,
                                                max=100,
                                                label="EMA window (bars)",
                                                labelPosition="bottom",
                                            )
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    )
                ),
                style={"width": "100%"},
            ),
        ]
    )

    @callback(
        Output("chart", "figure"),
        Output("active_period", "data"),
        Input("candles_1min", "n_clicks"),
        Input("candles_5min", "n_clicks"),
        Input("candles_1hour", "n_clicks"),
        Input("candles_1day", "n_clicks"),
        Input("ema_window", "value"),
        State("active_period", "data"),
    )
    def update_chart(
        _n1: int,
        _n5: int,
        _n1h: int,
        _n1d: int,
        ema_window: int | None,
        active_period: PERIOD,
    ) -> tuple[go.Figure, PERIOD]:
        period = active_period
        triggered = ctx.triggered_id
        if triggered in PERIOD_BY_BUTTON:
            period = PERIOD_BY_BUTTON[triggered]
        window = ema_window if ema_window is not None else DEFAULT_EMA_WINDOW
        return build_figure(market_data, period, window), period

    return app


def main() -> None:
    app = create_app()
    app.run(
        debug=config.DEBUG,
        host=config.APP_HOST,
        port=config.APP_PORT,
    )


if __name__ == "__main__":
    main()
