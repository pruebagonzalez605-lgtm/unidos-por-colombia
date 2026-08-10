#!/usr/bin/env python3
"""
scrape_personas.py — Colombia te busca → personas.json
────────────────────────────────────────────────────────────────────────────
Descarga la página 1 (más recientes primero) de colombiatebusca.com y
extrae, por cada persona publicada, SOLO los campos que ya son públicos
en la propia página: nombre, estado (por localizar / localizada),
categoría, ubicación, fecha/hora del reporte y edad/género si están
visibles. NO descarga ni guarda fotos, documentos, ni el detalle de
contacto del reportante.

Genera `personas.json` junto a este script, con esta forma:

{
  "generated_at": "2026-08-10T20:15:03Z",
  "source": "https://colombiatebusca.com/?tab=persons",
  "persons": [
    {
      "id": "6b6f39d3-...",
      "name": "Ana Forero Forero",
      "found": false,
      "category": "Terremoto",
      "location": "Pereira, Risaralda",
      "date": "10 Aug. 2026, 02:09 pm",
      "age": "50 años",
      "gender": "sin especificar",
      "href": "https://colombiatebusca.com/?person=6b6f39d3-..."
    },
    ...
  ]
}

index.html hace fetch a "personas.json" (mismo origen, sin problemas de
CORS) y si no lo encuentra o está vacío, cae de forma automática a la
vista agregada por municipio.

USO
────
  pip install requests beautifulsoup4
  python3 scrape_personas.py

Para que el mapa se vea realmente "en vivo", este script debe correr
periódicamente en algún lado (cron, GitHub Actions, tu propio servidor)
y el personas.json resultante debe quedar accesible en la misma carpeta
donde sirves index.html. Ver README_SCRAPER.md para dos formas de
programarlo sin necesidad de un servidor propio.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://colombiatebusca.com/?tab=persons"
OUTPUT_PATH = Path(__file__).parent / "personas.json"
MAX_ITEMS = 40
TIMEOUT_SECONDS = 15
USER_AGENT = (
    "Mozilla/5.0 (compatible; MapaEmergenciaChoco/1.0; "
    "+https://colombiatebusca.com/ referencia informativa, sin fines comerciales)"
)


def fetch_html(url: str) -> str:
    resp = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "es-CO,es;q=0.9"},
        timeout=TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.text


def find_person_id(href: str) -> str | None:
    if not href:
        return None
    m = re.search(r"[?&]person=([0-9a-fA-F-]{6,})", href)
    return m.group(1) if m else None


def card_for(tag):
    """Sube por los padres hasta encontrar un contenedor 'razonable' de
    tarjeta (no toda la página, no un simple <a>/<span> suelto)."""
    node = tag
    for _ in range(8):
        if node.parent is None:
            break
        node = node.parent
        text_len = len(node.get_text(strip=True))
        # Heurística: una tarjeta de persona normalmente tiene entre ~40
        # y ~600 caracteres de texto visible (nombre + estado + ubicación
        # + fecha + botones). Si nos pasamos de ahí, ya es un contenedor
        # que agrupa varias tarjetas -> nos quedamos con el nivel anterior.
        if text_len > 700:
            return node.parent if node.parent is not None else node
    return node


def extract_persons(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # Agrupa todos los <a href="...?person=ID"> por id.
    by_id: dict[str, list] = {}
    for a in soup.find_all("a", href=True):
        pid = find_person_id(a["href"])
        if pid:
            by_id.setdefault(pid, []).append(a)

    records = []
    seen_cards = set()

    for pid, links in by_id.items():
        # El enlace "con nombre" es el que tiene texto visible real y no
        # envuelve solo una imagen ni dice "Ver detalles".
        name_link = None
        for a in links:
            txt = a.get_text(strip=True)
            if txt and txt.lower() != "ver detalles" and not a.find("img"):
                name_link = a
                break
        if not name_link:
            continue

        name = name_link.get_text(strip=True)
        card = card_for(name_link)
        card_key = id(card)
        if card_key in seen_cards:
            continue
        seen_cards.add(card_key)

        card_text = card.get_text("\n", strip=True)

        status_match = re.search(r"(Por localizar|Localizad[ao]s?)", card_text, re.I)
        found = bool(status_match) and "localizad" in status_match.group(1).lower() and "por" not in status_match.group(1).lower()

        # La categoría suele quedar pegada justo después del estado en la
        # misma línea (p. ej. "Por localizarTerremoto").
        category = ""
        if status_match:
            line = next((l for l in card_text.split("\n") if status_match.group(0) in l), "")
            category = line.replace(status_match.group(0), "").strip()

        loc_match = re.search(r"⌖\s*([^\n]+)", card_text)
        date_match = re.search(r"▦\s*([^\n]+)", card_text)
        age_match = re.search(r"▣[^-\n]*-\s*(\d+\s*años)\s*-\s*([a-záéíóúñ]+)", card_text, re.I)

        href = name_link.get("href", "")
        if href.startswith("?") or href.startswith("/"):
            href = "https://colombiatebusca.com/" + href.lstrip("/")
        elif not href.startswith("http"):
            href = "https://colombiatebusca.com/" + href

        records.append({
            "id": pid,
            "name": name,
            "found": found,
            "category": category or "Reporte",
            "location": loc_match.group(1).strip() if loc_match else "",
            "date": date_match.group(1).strip() if date_match else "",
            "age": age_match.group(1).strip() if age_match else "",
            "gender": age_match.group(2).strip() if age_match else "",
            "href": href,
        })

        if len(records) >= MAX_ITEMS:
            break

    return records


def main():
    try:
        html = fetch_html(SOURCE_URL)
    except requests.RequestException as exc:
        print(f"ERROR al descargar {SOURCE_URL}: {exc}", file=sys.stderr)
        sys.exit(1)

    persons = extract_persons(html)
    if not persons:
        print(
            "ADVERTENCIA: no se extrajo ninguna persona. "
            "Es posible que el sitio haya cambiado de estructura; "
            "revisa extract_persons(). No se sobrescribe personas.json.",
            file=sys.stderr,
        )
        sys.exit(2)

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": SOURCE_URL,
        "persons": persons,
    }

    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"OK: {len(persons)} personas escritas en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
