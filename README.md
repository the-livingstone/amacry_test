# amacry-test

Тестовое приложение для Amacry: загрузка сырых котировок из CSV, построение свечей (OHLCV) на нескольких таймфреймах и интерактивный график с экспоненциальной скользящей средней (EMA).

## Что делает приложение

1. **Читает CSV** с полями `TS` (Unix timestamp в секундах), `PRICE`, `VOLUME`.
2. **Агрегирует котировки в свечи** для интервалов: 1 мин, 5 мин, 1 час, 1 день (OHLC по цене, суммарный объём по интервалу).
3. **Считает EMA** по закрытиям свечей **выбранного таймфрейма**: первое значение опирается на SMA за `n` баров, дальше формула с коэффициентом `2 / (n + 1)`. Если баров меньше, чем `n`, линия EMA не рисуется.
4. **Показывает Dash-дашборд** (Plotly): свечи, переключение таймфрейма, окно EMA (1-100 баров).

Цены и объёмы: `Decimal`, время: `pandas` / `datetime`.

## Структура репозитория

```
app/
  config.py      # настройки из .env (Pydantic Settings)
  get_data.py    # чтение CSV
  candles.py     # свечи, SMA, EMA
  dash_app.py    # веб-UI и callbacks
env.example
docker-compose.yml
Dockerfile
pyproject.toml
```

## Требования

- **Docker** и **Docker Compose**, либо локально: Python 3.11+, Poetry.
- CSV с рыночными данными (по умолчанию `SOLUSD.csv` в корне проекта), путь в `.env`.

### Формат CSV

| Колонка | Описание |
|--------|----------|
| `TS` | Unix time (секунды) |
| `PRICE` | Цена |
| `VOLUME` | Объём (суммируется в свече) |

## Быстрый старт (Docker)

```bash
git clone https://github.com/the-livingstone/amacry_test.git
cd amacry_test
cp env.example .env
docker compose up --build
```

Откройте http://127.0.0.1:8000 (порт из `APP_PORT`).

Compose монтирует `./app`, `.env` и файл данных. Точка входа: `python -m app.dash_app` или `amacry-dash` после `poetry install`.

## Локальный запуск (Poetry)

```bash
cp env.example .env
poetry install
poetry run python -m app.dash_app
```

| Переменная | Пример | Назначение |
|------------|--------|------------|
| `DEBUG` | `true` | Отладка Dash (`true` / `false`) |
| `APP_HOST` | `0.0.0.0` | Хост |
| `APP_PORT` | `8000` | Порт |
| `DATA_FILE` | `SOLUSD.csv` | Путь к CSV |

## Интерфейс

- **1min / 5min / 1hour / 1day**: таймфрейм свечей и EMA.
- **EMA window (bars)**: длина окна в барах текущего таймфрейма.

## Зависимости

Runtime: Dash, Plotly, pandas, dash-daq, pydantic-settings. Dev: black, flake8 (`poetry install --with dev`).
