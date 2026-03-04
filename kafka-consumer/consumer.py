import json
import os
import time
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from prometheus_client import start_http_server, Gauge

# ─── Configuration ────────────────────────────────────────────
KAFKA_BROKER  = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC   = os.getenv("KAFKA_TOPIC", "wind-data")
KAFKA_GROUP   = os.getenv("KAFKA_GROUP", "prometheus-consumer-group")
METRICS_PORT  = int(os.getenv("METRICS_PORT", "8001"))  # port différent du producer !

# ─── Métriques Prometheus ─────────────────────────────────────
# Gauge pour la vitesse du vent (lue depuis Kafka)
wind_speed_gauge = Gauge(
    "kafka_wind_speed_mps",
    "Vitesse du vent lue depuis Kafka (m/s)",
    ["city"]
)

# Gauge pour détecter le vent dangereux (0 ou 1)
# C'est ce que Grafana utilisera pour l'alerte !
wind_alert_gauge = Gauge(
    "wind_alert_active",
    "Alerte vent fort actif (1=danger, 0=normal)",
    ["city"]
)

# Seuil d'alerte : vent > 15 m/s = dangereux
# (15 m/s ≈ 54 km/h = vent fort)
WIND_ALERT_THRESHOLD = float(os.getenv("WIND_ALERT_THRESHOLD", "15.0"))


# ─── Logique d'alerte ─────────────────────────────────────────
def process_message(message: dict):
    """
    Traite un message Kafka :
    - Met à jour la métrique de vitesse
    - Active/désactive l'alerte si seuil dépassé
    """
    city  = message.get("city", "unknown")
    speed = message.get("wind_speed_mps", 0.0)

    # 1. Mise à jour de la vitesse
    wind_speed_gauge.labels(city=city).set(speed)

    # 2. Logique d'alerte
    if speed > WIND_ALERT_THRESHOLD:
        wind_alert_gauge.labels(city=city).set(1)   # 🚨 DANGER
        print(f"[ALERTE] {city} → Vent dangereux : {speed} m/s "
              f"(seuil: {WIND_ALERT_THRESHOLD} m/s)")
    else:
        wind_alert_gauge.labels(city=city).set(0)   # ✅ Normal
        print(f"[OK] {city} → Vent normal : {speed} m/s")


# ─── Initialisation du Consumer Kafka ─────────────────────────
def create_kafka_consumer() -> KafkaConsumer:
    """
    Crée un consumer Kafka avec retry automatique.
    Attend que Kafka soit prêt (important au démarrage K8s).
    """
    while True:   # retry infini jusqu'à connexion
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BROKER,
                group_id=KAFKA_GROUP,
                # Désérialise les bytes → dict Python
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                # Si nouveau groupe : lire depuis le début
                auto_offset_reset="earliest",
                # Confirme automatiquement la lecture
                enable_auto_commit=True
            )
            print(f"[KAFKA] Consumer connecté → topic: {KAFKA_TOPIC}")
            return consumer

        except KafkaError as e:
            print(f"[KAFKA] En attente du broker... ({e})")
            time.sleep(5)   # retry toutes les 5 secondes


# ─── Point d'entrée ───────────────────────────────────────────
if __name__ == "__main__":
    # Démarre le serveur de métriques sur port 8001
    start_http_server(METRICS_PORT)
    print(f"[DÉMARRAGE] Métriques consumer → http://localhost:{METRICS_PORT}/metrics")

    consumer = create_kafka_consumer()

    # Boucle de lecture infinie
    for message in consumer:
        try:
            data = message.value   # déjà désérialisé grâce au value_deserializer
            print(f"[MESSAGE] Reçu : {data}")
            process_message(data)
        except (KeyError, TypeError) as e:
            print(f"[ERREUR] Message invalide : {e} → {message.value}")