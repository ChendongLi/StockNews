FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY main.py .

RUN useradd --create-home app && mkdir -p /app/logs && chown app:app /app/logs
USER app
ENV LOG_FILE=/app/logs/stock_news.log

CMD ["python", "main.py"]
