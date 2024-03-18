The app calculates candlesticks from raw marketdata (csv file containing timestamp, quote price and volume) for four standard timeframes (1 min, 5 min, 1 hour, 1 day), calculates 5 day EMA indicator line and draws it on plot. The timeframe could be swithed by user in interactive fashion

# Quick Start

### Clone the repo

```
git clone https://github.com/the-livingstone/amacry_test.git
```

### Install [docker](https://docs.docker.com/engine/install/) and [docker-compose](https://docs.docker.com/compose/install/)
### Run docker-compose

```
docker-compose up --build
```
### open [@localhost:8000](http://127.0.0.1:8000) to see the interactive visualization
