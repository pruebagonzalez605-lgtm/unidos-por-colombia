# -*- coding: utf-8 -*-
"""
Scraper de agregados — Mapa de emergencia Sismo Chocó

A propósito, este script NUNCA guarda ni devuelve nombre, edad, género, id
ni href de ninguna persona individual. Solo cuenta reportes por municipio y
categoría (por localizar / localizadas), que es la única información que el
mapa público necesita para mostrar la concentración geográfica.

Si en algún momento modificas este archivo, mantené esa regla: cualquier
campo que identifique a una persona específica no debe salir de esta
función hacia el JSON expuesto.
"""

import re
import unicodedata
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from municipios_co import geocode

SITE_BASE = "https://colombiatebusca.com/"
LIST_URL = f"{SITE_BASE}?tab=persons"

# Categorías asociadas a la emergencia sísmica, igual que en la muestra
# manual original (ver README.md del proyecto).
RELEVANT_CATEGORIES = {"terremoto", "desastre natural", "persona extraviada"}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MapaEmergenciaChocoBot/1.0; "
                  "+https://colombiatebusca.com/)"
}

MAX_PAGES = 3  # límite de páginas a recorrer por corrida, para no sobrecargar el sitio origen


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.strip().lower()


def _split_location(raw: str):
    """'Pereira, Risaralda' -> ('Pereira', 'Risaralda'). Si no hay coma,
    devuelve el texto completo como municipio y departamento vacío."""
    raw = (raw or "").strip()
    if "," in raw:
        muni, dept = raw.split(",", 1)
        return muni.strip(), dept.strip()
    return raw, ""


def _ancestors(tag):
    """Lista de ancestros de tag, del más cercano al más lejano."""
    out = []
    p = tag.parent
    while p is not None:
        out.append(p)
        p = p.parent
    return out


def _lowest_common_ancestor(tags):
    """Ancestro común más específico de una lista de tags (cada tarjeta
    suele repetir el mismo enlace ?person=ID 2-3 veces: foto, nombre,
    'ver detalles'; necesitamos el contenedor que los agrupa a todos sin
    llegar hasta el <body> entero)."""
    chains = [_ancestors(t) for t in tags]
    common = set(chains[0])
    for c in chains[1:]:
        common &= set(c)
    if not common:
        return tags[0].parent
    # El más específico es el que aparece primero en la cadena del primer tag
    for anc in chains[0]:
        if anc in common:
            return anc
    return tags[0].parent


def _parse_cards(html: str):
    """Devuelve una lista de dicts SOLO con lo necesario para agregar:
    {municipio, departamento, categoria, localizado (bool)}.
    No conserva nombre, edad, id ni enlace de ficha individual."""
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('a[href*="?person="]')

    by_id = {}
    for a in links:
        href = a.get("href", "")
        m = re.search(r"[?&]person=([0-9a-f-]{6,})", href, re.I)
        if not m:
            continue
        by_id.setdefault(m.group(1), []).append(a)

    records = []
    for pid, tags in by_id.items():
        card = _lowest_common_ancestor(tags)
        text = card.get_text("\n", strip=True)

        status_m = re.search(r"(Por localizar|Localizad[ao]s?)", text, re.I)
        loc_m = re.search(r"⌖\s*([^\n]+)", text)
        cat_m = re.search(r"▣\s*([^\n\-]+)", text)  # categoría suele ir tras este símbolo

        if not status_m or not loc_m:
            continue

        category = _norm(cat_m.group(1)) if cat_m else ""
        # Si no reconocemos la categoría como relacionada al sismo, la
        # descartamos (igual que hizo la muestra manual original).
        if category and not any(c in category for c in RELEVANT_CATEGORIES):
            continue

        municipio, departamento = _split_location(loc_m.group(1))
        records.append({
            "municipio": municipio or "Sin precisar",
            "departamento": departamento,
            "localizado": bool(re.match(r"localizad", status_m.group(1), re.I)),
        })

    return records


def fetch_all_cards(max_pages=MAX_PAGES, timeout=20):
    all_records = []
    for page in range(1, max_pages + 1):
        url = LIST_URL if page == 1 else f"{LIST_URL}&page={page}"
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        records = _parse_cards(resp.text)
        if not records:
            break
        all_records.extend(records)
    return all_records


def aggregate(records):
    """Agrupa por (municipio normalizado, departamento normalizado) y
    devuelve la lista en el mismo formato que ya usa data.js del sitio."""
    groups = {}
    for r in records:
        key = (_norm(r["municipio"]), _norm(r["departamento"]))
        g = groups.setdefault(key, {
            "municipio": r["municipio"],
            "departamento": r["departamento"],
            "porLocalizar": 0,
            "localizadas": 0,
        })
        if r["localizado"]:
            g["localizadas"] += 1
        else:
            g["porLocalizar"] += 1

    out = []
    for g in groups.values():
        lat, lng, exact = geocode(g["municipio"], g["departamento"])
        out.append({
            "municipio": g["municipio"],
            "departamento": g["departamento"] or "Colombia",
            "lat": lat,
            "lng": lng,
            "ubicacionAproximada": not exact,
            "porLocalizar": g["porLocalizar"],
            "localizadas": g["localizadas"],
            "query": g["municipio"],
        })
    out.sort(key=lambda x: x["porLocalizar"], reverse=True)
    return out


def scrape_agregado():
    """Punto de entrada: devuelve el dict listo para servir como JSON.
    Nunca incluye campos que identifiquen a una persona."""
    records = fetch_all_cards()
    locations = aggregate(records)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": LIST_URL,
        "sample_size": len(records),
        "locations": locations,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(scrape_agregado(), ensure_ascii=False, indent=2))
