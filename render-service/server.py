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

import json
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

# Cache en disco: el plan free de Render reinicia el contenedor y borra la
# memoria del proceso. Persistimos solo conteos agregados (nunca datos
# individuales) para servir algo útil tras un cold start.
CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache_estado.json")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

_state_lock = threading.Lock()
_state = {
    "agregado": None,
    "agregado_error": None,
    "totales": None,
    "totales_error": None,
}

_thread_started = False
_thread_lock = threading.Lock()


def _load_cache():
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cached = json.load(f)
        with _state_lock:
            if cached.get("agregado") is not None:
                _state["agregado"] = cached["agregado"]
            if cached.get("totales") is not None:
                _state["totales"] = cached["totales"]
        log.info("Estado recuperado de %s", CACHE_PATH)
    except FileNotFoundError:
        pass
    except Exception as e:
        log.warning("No se pudo leer el cache en disco (%s): %s", CACHE_PATH, e)


def _save_cache():
    try:
        with _state_lock:
            snapshot = {"agregado": _state["agregado"], "totales": _state["totales"]}
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False)
    except Exception as e:
        log.warning("No se pudo guardar el cache en disco (%s): %s", CACHE_PATH, e)


def _fetch_totales():
    """Lee solo los 3 contadores de resumen de la portada."""
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
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _refresh_once():
    ok = False
    try:
        log.info("Iniciando scrape de agregado…")
        data = scrape_agregado()
        with _state_lock:
            _state["agregado"] = data
            _state["agregado_error"] = None
        log.info(
            "agregado.json actualizado: %d municipios, muestra=%d",
            len(data["locations"]),
            data["sample_size"],
        )
        _save_cache()
        ok = True
    except Exception as e:
        with _state_lock:
            _state["agregado_error"] = str(e)
        log.exception("Fallo actualizando agregado: %s", e)

    try:
        log.info("Iniciando fetch de totales…")
        totales = _fetch_totales()
        with _state_lock:
            _state["totales"] = totales
            _state["totales_error"] = None
        log.info("totales.json actualizado: %s", totales)
        _save_cache()
        ok = True
    except Exception as e:
        with _state_lock:
            _state["totales_error"] = str(e)
        log.exception("Fallo actualizando totales: %s", e)

    return ok


def _refresh_loop():
    attempt = 0
    while True:
        attempt += 1
        log.info("Ciclo de actualización #%d (pid=%s)", attempt, os.getpid())
        ok = _refresh_once()
        sleep_for = REFRESH_SECONDS if ok else min(30, REFRESH_SECONDS)
        log.info("Próxima actualización en %ds (ok=%s)", sleep_for, ok)
        time.sleep(sleep_for)


def _ensure_background_thread():
    """Arranca el hilo de scrape UNA sola vez, dentro del worker que
    atiende HTTP. Evita el problema de Gunicorn donde el master importa
    el módulo, corre el hilo en otro proceso y los workers quedan sin datos.
    """
    global _thread_started
    with _thread_lock:
        if _thread_started:
            return
        _thread_started = True
        t = threading.Thread(target=_refresh_loop, daemon=True, name="scrape-loop")
        t.start()
        log.info("Hilo de scrape arrancado en pid=%s", os.getpid())


@app.before_request
def _before_request():
    _ensure_background_thread()


@app.get("/")
def root():
    _ensure_background_thread()
    with _state_lock:
        ok_agregado = _state["agregado"] is not None
        ok_totales = _state["totales"] is not None
        err_a = _state["agregado_error"]
        err_t = _state["totales_error"]
        gen = None
        if _state["agregado"]:
            gen = _state["agregado"].get("generated_at")
    return jsonify({
        "service": "mapa-choco-agregados",
        "agregado_disponible": ok_agregado,
        "totales_disponible": ok_totales,
        "refresh_seconds": REFRESH_SECONDS,
        "generated_at": gen,
        "agregado_error": err_a,
        "totales_error": err_t,
        "pid": os.getpid(),
    })


@app.get("/agregado.json")
def agregado():
    _ensure_background_thread()
    with _state_lock:
        data = _state["agregado"]
        err = _state["agregado_error"]
    if data is None:
        return jsonify({"error": err or "Aún sin datos, reintenta en unos segundos"}), 503
    return jsonify(data)


@app.get("/totales.json")
def totales():
    _ensure_background_thread()
    with _state_lock:
        data = _state["totales"]
        err = _state["totales_error"]
    if data is None:
        return jsonify({"error": err or "Aún sin datos, reintenta en unos segundos"}), 503
    return jsonify(data)


# Cargar cache al importar (mismo proceso del worker cuando atienda).
_load_cache()


if __name__ == "__main__":
    # Modo local: arrancar hilo ya y servir con Flask
    _ensure_background_thread()
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
