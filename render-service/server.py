# -*- coding: utf-8 -*-
"""
Servicio para Render — expone conteos agregados (nunca registros
individuales) para que el mapa estático (GitHub Pages) los consuma vía
fetch() desde el navegador.

Endpoints:
  GET /                -> estado del servicio (para healthcheck de Render)
  GET /agregado.json   -> {generated_at, locations: [...]}  (conteos por municipio)
  GET /totales.json    -> {generated_at, registradas, porLocalizar, localizadas}

CORS: abierto (*) porque estos son datos agregados, públicos y sin
información personal — no hay motivo para restringir el origen.
"""

import logging
import os
import re
import threading
import time

import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from flask_cors import CORS

from scrape_agregado import scrape_agregado, SITE_BASE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("mapa-choco")

REFRESH_SECONDS = int(os.environ.get("REFRESH_SECONDS", "300"))  # 5 min por defecto

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

_state_lock = threading.Lock()
_state = {
    "agregado": None,      # último resultado bueno de scrape_agregado()
    "agregado_error": None,
    "totales": None,       # {"registradas": int, "porLocalizar": int, "localizadas": int}
    "totales_error": None,
}


def _fetch_totales():
    """Lee solo los 3 contadores de resumen de la portada — ningún dato
    individual. Heurística tolerante: busca 3 números junto a las palabras
    clave que ya usa el propio sitio en su portada."""
    resp = requests.get(
        SITE_BASE,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
        },
        timeout=35,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    def find_near(label):
        # Entre el número y la etiqueta puede haber una palabra pegada
        # (ej. "756Personas registradas"), no solo espacios.
        m = re.search(r"([\d.,]{1,7})\s*(?:\w+\s*)?" + label, text, re.I) or \
            re.search(label + r"\s*(?:\w+\s*)?([\d.,]{1,7})", text, re.I)
        if not m:
            return None
        return int(re.sub(r"[.,]", "", m.group(1)))

    registradas = find_near("Registrad")
    por_localizar = find_near("[Pp]or [Ll]ocalizar")
    localizadas = find_near("Localizad")
    if registradas is None or por_localizar is None:
        raise ValueError("No se pudieron leer los contadores de la portada")
    return {
        "registradas": registradas,
        "porLocalizar": por_localizar,
        "localizadas": localizadas or 0,
    }


def _refresh_loop():
    while True:
        try:
            data = scrape_agregado()
            with _state_lock:
                _state["agregado"] = data
                _state["agregado_error"] = None
            log.info("agregado.json actualizado: %d municipios, muestra=%d",
                      len(data["locations"]), data["sample_size"])
        except Exception as e:
            with _state_lock:
                _state["agregado_error"] = str(e)
            log.warning("Fallo actualizando agregado: %s", e)

        try:
            totales = _fetch_totales()
            with _state_lock:
                _state["totales"] = totales
                _state["totales_error"] = None
            log.info("totales.json actualizado: %s", totales)
        except Exception as e:
            with _state_lock:
                _state["totales_error"] = str(e)
            log.warning("Fallo actualizando totales: %s", e)

        time.sleep(REFRESH_SECONDS)


@app.get("/")
def root():
    with _state_lock:
        ok_agregado = _state["agregado"] is not None
        ok_totales = _state["totales"] is not None
    return jsonify({
        "service": "mapa-choco-agregados",
        "agregado_disponible": ok_agregado,
        "totales_disponible": ok_totales,
        "refresh_seconds": REFRESH_SECONDS,
    })


@app.get("/agregado.json")
def agregado():
    with _state_lock:
        data = _state["agregado"]
        err = _state["agregado_error"]
    if data is None:
        return jsonify({"error": err or "Aún sin datos, reintenta en unos segundos"}), 503
    return jsonify(data)


@app.get("/totales.json")
def totales():
    with _state_lock:
        data = _state["totales"]
        err = _state["totales_error"]
    if data is None:
        return jsonify({"error": err or "Aún sin datos, reintenta en unos segundos"}), 503
    return jsonify(data)


# Arranca el scheduler en un hilo de fondo apenas se importa el módulo,
# para que funcione tanto con `python server.py` como bajo gunicorn.
_thread = threading.Thread(target=_refresh_loop, daemon=True)
_thread.start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
