FROM python:3.11-slim

WORKDIR /app

# Dépendances en premier (cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY consumer.py .

RUN useradd --no-create-home appuser
USER appuser

# Port différent du producer (8001 vs 8000)
EXPOSE 8001

CMD ["python", "-u", "consumer.py"]