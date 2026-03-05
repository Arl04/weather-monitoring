import os
import json
from kafka import KafkaConsumer
from prometheus_client import start_http_server, Gauge

# ── Configuration ───────────────────────────────────────────
KAFKA_BROKER          = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC           = os.getenv("KAFKA_TOPIC", "wind-data")
KAFKA_GROUP           = os.getenv("KAFKA_GROUP", "prometheus-consumer-group")
WIND_ALERT_THRESHOLD  = float(os.getenv("WIND_ALERT_THRESHOLD", "15.0"))
HEAT_ALERT_THRESHOLD  = float(os.getenv("HEAT_ALERT_THRESHOLD", "35.0"))

# ── Métriques Prometheus ────────────────────────────────────
kafka_wind_gauge = Gauge(
    "kafka_wind_speed_mps",
    "Vitesse du vent lue depuis Kafka (m/s)",
    ["city"]
)
kafka_temp_gauge = Gauge(
    "kafka_temperature_celsius",
    "Température lue depuis Kafka (°C)",
    ["city"]
)
kafka_humidity_gauge = Gauge(
    "kafka_humidity_percent",
    "Humidité lue depuis Kafka (%)",
    ["city"]
)
wind_alert_gauge = Gauge(
    "wind_alert_active",
    "Alerte vent fort actif (1=danger, 0=normal)",
    ["city"]
)
heat_alert_gauge = Gauge(
    "heat_alert_active",
    "Alerte chaleur active (1=danger, 0=normal)",
    ["city"]
)

# ── Boucle principale ───────────────────────────────────────
def main():
    print(f"[DÉMARRAGE] Serveur métriques actif → http://localhost:8001/metrics")
    start_http_server(8001)

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id=KAFKA_GROUP,
        auto_offset_reset="earliest",
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )

    print(f"[KAFKA] Consumer connecté → topic: {KAFKA_TOPIC}")

    for message in consumer:
        data = message.value
        city = data.get("city", "unknown")

        wind  = data.get("wind_speed", 0)
        temp  = data.get("temperature", 0)
        humid = data.get("humidity", 0)

        # Mise à jour métriques
        kafka_wind_gauge.labels(city=city).set(wind)
        kafka_temp_gauge.labels(city=city).set(temp)
        kafka_humidity_gauge.labels(city=city).set(humid)

        # Alertes
        wind_alert = 1 if wind > WIND_ALERT_THRESHOLD else 0
        heat_alert = 1 if temp > HEAT_ALERT_THRESHOLD else 0
        wind_alert_gauge.labels(city=city).set(wind_alert)
        heat_alert_gauge.labels(city=city).set(heat_alert)

        print(
            f"[MESSAGE] {city} → "
            f"Vent: {wind} m/s {'🚨' if wind_alert else '✅'} | "
            f"Temp: {temp}°C {'🔥' if heat_alert else '✅'} | "
            f"Humidité: {humid}%"
        )

if __name__ == "__main__":
    main()