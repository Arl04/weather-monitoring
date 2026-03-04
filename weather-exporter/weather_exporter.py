import time
import os
import requests
from prometheus_client import start_http_server, Gauge

# ─── Configuration ───────────────────────────────────────────────
API_KEY  = os.getenv("OWM_API_KEY", "VOTRE_CLE_ICI")
CITY     = os.getenv("CITY", "Cotonou")
INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "30"))  # secondes entre chaque appel API

# ─── Déclaration de la métrique Prometheus ───────────────────────
# Gauge : valeur instantanée qui peut monter ou descendre
# labels : permettent de filtrer par ville dans Grafana
wind_speed_gauge = Gauge(
    "wind_speed_mps",                        # Nom de la métrique
    "Vitesse du vent en mètres par seconde",  # Description
    ["city"]                                  # Labels
)

# ─── Fonction de collecte ────────────────────────────────────────
def fetch_wind_speed(city: str) -> float | None:
    """
    Interroge l'API OpenWeatherMap et retourne la vitesse du vent (m/s).
    Retourne None en cas d'erreur pour ne pas crasher la boucle principale.
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q":     city,
        "appid": API_KEY,
        "units": "metric"  # m/s pour le vent, °C pour la temp
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Lève une exception si HTTP 4xx/5xx

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


# ─── Point d'entrée principal ────────────────────────────────────
if __name__ == "__main__":

    # Démarre le serveur HTTP sur le port 8000
    # Prometheus scrape http://localhost:8000/metrics
    start_http_server(8000)
    print(f"[DÉMARRAGE] Serveur métriques actif → http://localhost:8000/metrics")
    print(f"[CONFIG] Ville : {CITY} | Intervalle : {INTERVAL}s")

    # Boucle infinie : collecte + exposition toutes les N secondes
    while True:
        speed = fetch_wind_speed(CITY)

        if speed is not None:
            # Met à jour la gauge avec le label "city"
            wind_speed_gauge.labels(city=CITY).set(speed)

        time.sleep(INTERVAL)