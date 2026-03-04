# ── Étape 1 : Image de base ──────────────────────────────────────
# "slim" = version allégée sans outils inutiles (~50MB vs ~900MB)
# C'est une bonne pratique de sécurité : moins de surface d'attaque
FROM python:3.11-slim

# ── Étape 2 : Répertoire de travail dans le conteneur ───────────
# Tout ce qu'on fait ensuite se passe dans /app
WORKDIR /app

# ── Étape 3 : Copier et installer les dépendances EN PREMIER ────
# POURQUOI avant le script ? → Cache Docker !
# Si tu modifies weather_exporter.py, Docker ne réinstalle PAS pip
# Il réutilise le cache de cette couche. Gain de temps énorme.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Étape 4 : Copier le code source ─────────────────────────────
COPY weather_exporter.py .

# ── Étape 5 : Sécurité — Ne pas tourner en root ─────────────────
# Par défaut Docker tourne en root → risque de sécurité
# On crée un utilisateur dédié sans privilèges
RUN useradd --no-create-home appuser
USER appuser

# ── Étape 6 : Documentation du port exposé ──────────────────────
# EXPOSE n'ouvre pas vraiment le port, c'est de la documentation
# Kubernetes utilisera cette info pour le routing
EXPOSE 8000

# ── Étape 7 : Commande de démarrage ─────────────────────────────
CMD ["python", "-u", "weather_exporter.py"]
# -u = unbuffered : les print() apparaissent immédiatement dans les logs