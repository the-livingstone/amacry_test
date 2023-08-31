FROM python:3.10

ENV PRICES_URL=https://perp-analysis.s3.amazonaws.com/interview/prices.csv.zip
ENV HOST=0.0.0.0

WORKDIR /opt

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

EXPOSE 8050

COPY . .

# CMD ["pwd"]

CMD ["python3", "app/app.py"]