# 🌤️ Weather Monitoring — Cotonou

> Système de surveillance météorologique en temps réel avec pipeline de données complet : collecte, streaming, stockage et visualisation.

![CI](https://github.com/Arl04/weather-monitoring/actions/workflows/ci.yml/badge.svg)
![Docker](https://img.shields.io/badge/Docker-arl04%2Fweather--exporter-blue?logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Minikube-326CE5?logo=kubernetes)
![Prometheus](https://img.shields.io/badge/Prometheus-metrics-E6522C?logo=prometheus)
![Grafana](https://img.shields.io/badge/Grafana-dashboard-F46800?logo=grafana)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)

---

## 📋 Table des matières

- [Architecture](#-architecture)
- [Stack technique](#-stack-technique)
- [Métriques disponibles](#-métriques-disponibles)
- [Structure du projet](#-structure-du-projet)
- [Démarrage rapide](#-démarrage-rapide)
- [Déploiement Kubernetes](#-déploiement-kubernetes)
- [CI/CD](#-cicd)
- [Dashboard Grafana](#-dashboard-grafana)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      WEATHER MONITORING                     │
│                                                             │
│  🌍 OpenWeatherMap API                                      │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────┐     ┌──────────────┐                  │
│  │ weather-exporter│────▶│    Kafka     │                  │
│  │   (port 8000)   │     │  wind-data   │                  │
│  └─────────────────┘     └──────┬───────┘                  │
│         │                       │                           │
│         │ /metrics              ▼                           │
│         │              ┌─────────────────┐                  │
│         │              │  kafka-consumer  │                 │
│         │              │   (port 8001)   │                  │
│         │              └────────┬────────┘                  │
│         │                       │ /metrics                  │
│         ▼                       ▼                           │
│  ┌─────────────────────────────────────┐                   │
│  │            Prometheus               │                   │
│  │         (scrape toutes les 15s)     │                   │
│  └──────────────────┬──────────────────┘                   │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────────────────────┐                   │
│  │         Grafana Dashboard           │                   │
│  │   Vent │ Temp │ Humidité │ Alertes  │                   │
│  └─────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack technique

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| **Collecte** | Python 3.11 + OpenWeatherMap API | Récupère les données météo toutes les 30s |
| **Streaming** | Apache Kafka + Zookeeper | Pipeline de données temps réel |
| **Métriques** | Prometheus | Scrape et stockage des métriques |
| **Visualisation** | Grafana | Dashboard interactif |
| **Containerisation** | Docker + Docker Compose | Environnement local |
| **Orchestration** | Kubernetes (Minikube) | Déploiement production |
| **CI/CD** | GitHub Actions | Build & Push automatique sur Docker Hub |

---

## 📊 Métriques disponibles

### Weather Exporter (`localhost:8000/metrics`)

| Métrique | Type | Description |
|----------|------|-------------|
| `wind_speed_mps` | Gauge | Vitesse du vent en m/s |
| `temperature_celsius` | Gauge | Température en °C |
| `humidity_percent` | Gauge | Humidité relative en % |

### Kafka Consumer (`localhost:8001/metrics`)

| Métrique | Type | Description |
|----------|------|-------------|
| `kafka_wind_speed_mps` | Gauge | Vitesse du vent lue depuis Kafka |
| `kafka_temperature_celsius` | Gauge | Température lue depuis Kafka |
| `kafka_humidity_percent` | Gauge | Humidité lue depuis Kafka |
| `wind_alert_active` | Gauge | Alerte vent fort (1=danger si > 15 m/s) |
| `heat_alert_active` | Gauge | Alerte chaleur (1=danger si > 35°C) |

---

## 📁 Structure du projet

```
weather-monitoring/
├── .github/
│   └── workflows/
│       └── ci.yml                  # Pipeline CI/CD GitHub Actions
├── weather-exporter/
│   ├── weather_exporter.py         # Collecte météo + export Prometheus
│   ├── Dockerfile
│   └── requirements.txt
├── kafka-consumer/
│   ├── consumer.py                 # Consomme Kafka + métriques + alertes
│   ├── Dockerfile
│   └── requirements.txt
├── kafka/
│   └── ...                         # Configuration Kafka
├── k8s/
│   ├── namespace.yaml              # Namespace Kubernetes
│   ├── configmap.yaml              # Configuration centralisée
│   ├── weather-exporter.yaml       # Deployment + Service
│   ├── kafka-consumer.yaml         # Deployment + Service (avec initContainer)
│   └── kafka.yaml                  # Kafka + Zookeeper
├── helm/                           # Helm charts
├── docker-compose.yml              # Stack locale complète
└── prometheus.yml                  # Configuration Prometheus
```

---

## 🚀 Démarrage rapide

### Prérequis

- Docker Desktop
- Python 3.11+
- Une clé API [OpenWeatherMap](https://openweathermap.org/api) (gratuite)

### 1. Clone le projet

```bash
git clone https://github.com/Arl04/weather-monitoring.git
cd weather-monitoring
```

### 2. Configure la clé API

```bash
export OWM_API_KEY=ta_cle_api_openweathermap
```

### 3. Lance la stack complète

```bash
docker-compose up -d
```

### 4. Accède aux services

| Service | URL |
|---------|-----|
| Métriques Weather Exporter | http://localhost:8000/metrics |
| Métriques Kafka Consumer | http://localhost:8001/metrics |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

> 💡 Grafana : login `admin` / `admin`

---

## ☸️ Déploiement Kubernetes

### Prérequis

```bash
brew install minikube kubectl
minikube start --driver=docker
```

### Déploiement

```bash
# Crée le namespace et la configuration
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml

# Crée le secret pour l'API key
kubectl create secret generic weather-secrets \
  --from-literal=OWM_API_KEY=ta_cle_api \
  --namespace=weather-monitoring

# Déploie Kafka + Zookeeper
kubectl apply -f k8s/kafka.yaml

# Déploie les services météo
kubectl apply -f k8s/weather-exporter.yaml
kubectl apply -f k8s/kafka-consumer.yaml
```

### Vérification

```bash
kubectl get pods -n weather-monitoring
# NAME                                READY   STATUS    RESTARTS   AGE
# kafka-xxxx                          1/1     Running   0          5m
# kafka-consumer-xxxx                 1/1     Running   0          5m
# weather-exporter-xxxx               1/1     Running   0          5m
# zookeeper-xxxx                      1/1     Running   0          5m
```

### Accès aux métriques depuis Kubernetes

```bash
kubectl port-forward svc/weather-exporter 8000:8000 -n weather-monitoring &
kubectl port-forward svc/kafka-consumer 8001:8001 -n weather-monitoring &

curl http://localhost:8000/metrics | grep wind_speed
curl http://localhost:8001/metrics | grep kafka_temperature
```

---

## ⚙️ CI/CD

Le pipeline GitHub Actions se déclenche automatiquement à chaque `git push` sur `main` :

```
git push origin main
       │
       ▼
🧪 Tests Python (syntaxe + imports)
       │
  ✅ OK ?
       │
  ┌────┴────┐
  ▼         ▼
🐳 Build   🐳 Build       ← en parallèle
weather-   kafka-
exporter   consumer
  │         │
  └────┬────┘
       ▼
📦 Push sur Docker Hub
   arl04/weather-exporter:latest
   arl04/weather-exporter:<sha>
   arl04/kafka-consumer:latest
   arl04/kafka-consumer:<sha>
```

**Images Docker Hub :**
- [`arl04/weather-exporter`](https://hub.docker.com/r/arl04/weather-exporter)
- [`arl04/kafka-consumer`](https://hub.docker.com/r/arl04/kafka-consumer)

---

## 📈 Dashboard Grafana

Le dashboard **"Surveillance Météo Cotonou"** contient 5 panels :

| Panel | Type | Métrique |
|-------|------|---------|
| 🚨 Alerte Vent | Stat | `wind_alert_active` |
| 🔥 Alerte Chaleur | Stat | `heat_alert_active` |
| 🌬️ Vitesse du vent | Time series | `kafka_wind_speed_mps` |
| 🌡️ Température | Time series | `kafka_temperature_celsius` |
| 💧 Humidité | Gauge | `kafka_humidity_percent` |

### Seuils d'alerte

```
Vent fort  : > 15.0 m/s  → 🚨 DANGER
Chaleur    : > 35.0°C    → 🔥 DANGER
```

---

## 🌍 Données en temps réel — Cotonou, Bénin

```
Ville     : Cotonou, Bénin 🇧🇯
Latitude  : 6.3654° N
Longitude : 2.4183° E
Climat    : Tropical humide
Humidité  : ~79-83% (normale pour une ville côtière)
```

---

## 👤 Auteur

**Arl04** — Projet DevOps / Data Engineering

[![GitHub](https://img.shields.io/badge/GitHub-Arl04-181717?logo=github)](https://github.com/Arl04)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-arl04-2496ED?logo=docker)](https://hub.docker.com/u/arl04)