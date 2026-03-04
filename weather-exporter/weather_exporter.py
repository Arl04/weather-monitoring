import time
import os
import json
import requests
from prometheus_client import start_http_server, Gauge
from kafka import KafkaProducer
from kafka.errors import KafkaError

# ─── Configuration ────────────────────────────────────────────
API_KEY        = os.getenv("OWM_API_KEY", "VOTRE_CLE_ICI")
CITY           = os.getenv("CITY", "Cotonou")
INTERVAL       = int(os.getenv("SCRAPE_INTERVAL", "30"))
KAFKA_BROKER   = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC    = os.getenv("KAFKA_TOPIC", "wind-data")

# ─── Métrique Prometheus (inchangée) ──────────────────────────
wind_speed_gauge = Gauge(
    "wind_speed_mps",
    "Vitesse du vent en mètres par seconde",
    ["city"]
)

# ─── Initialisation du Producteur Kafka ───────────────────────
def create_kafka_producer() -> KafkaProducer | None:
    """
    Crée un producteur Kafka.
    Retourne None si Kafka n'est pas disponible
    (le script continue à exposer les métriques Prometheus)
    """
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            # Sérialise le dict Python en JSON puis en bytes
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            # Attend confirmation d'écriture du broker
            acks="all",
            retries=3
        )
        print(f"[KAFKA] Connecté → {KAFKA_BROKER}")
        return producer
    except KafkaError as e:
        print(f"[KAFKA] Connexion impossible : {e}")
        print("[KAFKA] Mode dégradé : uniquement Prometheus")
        return None

# ─── Collecte + Publication ───────────────────────────────────
def fetch_wind_speed(city: str) -> float | None:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": API_KEY, "units": "metric"}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        wind_speed = data["wind"]["speed"]
        print(f"[OK] {city} → Vent : {wind_speed} m/s")
        return wind_speed
    except requests.exceptions.HTTPError as e:
        print(f"[ERREUR HTTP] {e}")
    except requests.exceptions.ConnectionError:
        print("[ERREUR] Impossible de joindre l'API OpenWeatherMap")
    except KeyError:
        print("[ERREUR] Format de réponse inattendu")
    return None


def publish_to_kafka(producer: KafkaProducer, city: str, speed: float):
    """
    Publie la donnée dans le topic Kafka sous forme de JSON.
    """
    message = {
        "city": city,
        "wind_speed_mps": speed,
        "timestamp": int(time.time())   # Unix timestamp
    }
    try:
        # Envoi asynchrone → on attend la confirmation avec .get()
        future = producer.send(KAFKA_TOPIC, value=message)
        future.get(timeout=10)          # bloque jusqu'à confirmation
        print(f"[KAFKA] Publié → {message}")
    except KafkaError as e:
        print(f"[KAFKA] Échec publication : {e}")


# ─── Point d'entrée ───────────────────────────────────────────
if __name__ == "__main__":
    start_http_server(8000)
    print(f"[DÉMARRAGE] Métriques → http://localhost:8000/metrics")

    kafka_producer = create_kafka_producer()

    while True:
        speed = fetch_wind_speed(CITY)

        if speed is not None:
            # 1. Mise à jour Prometheus (comme avant)
            wind_speed_gauge.labels(city=CITY).set(speed)

            # 2. Publication Kafka (nouveau !)
            if kafka_producer:
                publish_to_kafka(kafka_producer, CITY, speed)

        time.sleep(INTERVAL)