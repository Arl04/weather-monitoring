import os
import time
import requests
from prometheus_client import start_http_server, Gauge

# ── Configuration ──────────────────────────────────────────
OWM_API_KEY       = os.getenv("OWM_API_KEY", "")
CITY              = os.getenv("CITY", "Cotonou")
SCRAPE_INTERVAL   = int(os.getenv("SCRAPE_INTERVAL", "30"))
KAFKA_BROKER      = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC       = os.getenv("KAFKA_TOPIC", "wind-data")

# ── Métriques Prometheus ────────────────────────────────────
wind_speed_gauge = Gauge(
    "wind_speed_mps",
    "Vitesse du vent en mètres par seconde",
    ["city"]
)
temperature_gauge = Gauge(
    "temperature_celsius",
    "Température en degrés Celsius",
    ["city"]
)
humidity_gauge = Gauge(
    "humidity_percent",
    "Humidité relative en pourcentage",
    ["city"]
)

# ── Récupération données OpenWeatherMap ─────────────────────
def fetch_weather(city: str) -> dict:
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={OWM_API_KEY}&units=metric"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    return {
        "city":        city,
        "wind_speed":  data["wind"]["speed"],
        "temperature": data["main"]["temp"],
        "humidity":    data["main"]["humidity"],
    }

# ── Kafka Producer ──────────────────────────────────────────
def get_producer():
    try:
        from kafka import KafkaProducer
        import json
        return KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
    except Exception as e:
        print(f"[KAFKA] Connexion impossible : {e}")
        return None

# ── Boucle principale ───────────────────────────────────────
def main():
    print(f"[DÉMARRAGE] Serveur métriques actif → http://localhost:8000/metrics")
    start_http_server(8000)
    producer = get_producer()

    while True:
        try:
            weather = fetch_weather(CITY)

            # Mise à jour métriques Prometheus
            wind_speed_gauge.labels(city=CITY).set(weather["wind_speed"])
            temperature_gauge.labels(city=CITY).set(weather["temperature"])
            humidity_gauge.labels(city=CITY).set(weather["humidity"])

            print(
                f"[OK] {CITY} → "
                f"Vent: {weather['wind_speed']} m/s | "
                f"Temp: {weather['temperature']}°C | "
                f"Humidité: {weather['humidity']}%"
            )

            # Envoi vers Kafka
            if producer:
                producer.send(KAFKA_TOPIC, weather)
                print(f"[KAFKA] Message envoyé → {KAFKA_TOPIC}")

        except Exception as e:
            print(f"[ERREUR] {e}")

        time.sleep(SCRAPE_INTERVAL)

if __name__ == "__main__":
    main()