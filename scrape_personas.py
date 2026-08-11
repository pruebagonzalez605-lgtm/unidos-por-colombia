#!/usr/bin/env python3
"""
scrape_personas.py — Colombia te busca → personas.json
────────────────────────────────────────────────────────────────────────────
Descarga las páginas de listado de colombiatebusca.com y extrae, por cada
persona publicada, SOLO los campos que ya son públicos en la propia página:

  - id, nombre, estado (por localizar / localizada)
  - categoría, ubicación, fecha/hora del reporte
  - edad, género, código CTB (si están visibles)

NO descarga ni guarda fotos, documentos de identidad ni datos de contacto
del reportante.

Genera `personas.json` junto a este script.

USO
────
  pip install -r requirements.txt
  python3 scrape_personas.py

  # Opciones útiles:
  python3 scrape_personas.py --pages 5          # hasta 5 páginas (100 registros)
  python3 scrape_personas.py --pages 0          # todas las páginas disponibles
  python3 scrape_personas.py --max 50           # máximo de personas a guardar
  python3 scrape_personas.py --out otra.json    # archivo de salida distinto

Para mantener el mapa "en vivo", programa este script (cron, GitHub Actions,
etc.) y deja personas.json accesible junto a index.html.
Ver README_SCRAPER.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

SITE_BASE = "https://colombiatebusca.com/"
LIST_URL = f"{SITE_BASE}?tab=persons"
DEFAULT_OUTPUT = Path(__file__).parent / "personas.json"
DEFAULT_MAX_PAGES = 3          # ~60 registros; evita sobrecargar el sitio
REQUEST_TIMEOUT = 25
PAUSE_BETWEEN_PAGES = 1.2      # segundos de cortesía entre páginas

USER_AGENT = (
    "Mozilla/5.0 (compatible; MapaEmergenciaChoco/1.1; "
    "+https://colombiatebusca.com/ referencia informativa, sin fines comerciales)"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
}


# ── helpers ────────────────────────────────────────────────────────────────

def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def extract_person_id(href: str | None) -> str | None:
    if not href:
        return None
    m = re.search(r"[?&]person=([0-9a-fA-F-]{8,})", href)
    return m.group(1) if m else None


def parse_meta_age_gender(text: str) -> tuple[str, str]:
    """
    Ejemplos de texto en .meta:
      '▣ Sin documento público  - 12 años - femenino'
      '▣ CC 123456  - 45 años - masculino'
      '▣ Sin documento público  - sin edad - sin especificar'
    """
    age = ""
    gender = ""
    # edad
    m_age = re.search(r"(\d+\s*años?)", text, re.I)
    if m_age:
        age = m_age.group(1).strip()
    # género (última parte después del último " - ")
    parts = [p.strip() for p in text.split(" - ") if p.strip()]
    if parts:
        last = parts[-1].lower()
        if any(g in last for g in ("femenino", "masculino", "mujer", "hombre", "sin especificar")):
            gender = parts[-1].strip()
    return age, gender


def parse_card(article) -> dict | None:
    """Extrae un registro limpio a partir de un <article class="card">."""
    # Enlace / id
    name_link = article.select_one("h2 a[href*='person=']") or article.select_one("a[href*='person=']")
    if not name_link:
        return None

    href = name_link.get("href", "")
    pid = extract_person_id(href)
    if not pid:
        return None

    name = name_link.get_text(strip=True)
    if not name:
        return None

    # URL absoluta
    full_href = urljoin(SITE_BASE, href)

    # Badges: estado + categoría
    found = False
    category = "Reporte"
    for badge in article.select(".card-badges .badge"):
        txt = badge.get_text(strip=True)
        classes = " ".join(badge.get("class", [])).lower()
        if "missing" in classes or re.search(r"por\s*localizar", txt, re.I):
            found = False
        elif "found" in classes or re.search(r"^localizad", txt, re.I):
            found = True
        if "category" in classes:
            category = txt or category

    # Metadatos (ubicación, fecha, edad/género)
    location = ""
    date = ""
    age = ""
    gender = ""
    code = ""

    code_el = article.select_one("p.card-code")
    if code_el:
        code = code_el.get_text(strip=True)

    for meta in article.select("p.meta"):
        txt = meta.get_text(" ", strip=True)
        if "⌖" in txt or txt.startswith("⌖"):
            location = re.sub(r"^⌖\s*", "", txt).strip()
        elif "▦" in txt or txt.startswith("▦"):
            date = re.sub(r"^▦\s*", "", txt).strip()
        elif "▣" in txt or txt.startswith("▣"):
            age, gender = parse_meta_age_gender(txt)

    return {
        "id": pid,
        "name": name,
        "found": found,
        "category": category,
        "location": location,
        "date": date,
        "age": age,
        "gender": gender,
        "code": code,
        "href": full_href,
    }


def extract_persons_from_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("article.card")
    records = []
    seen_ids: set[str] = set()

    for card in cards:
        rec = parse_card(card)
        if not rec or rec["id"] in seen_ids:
            continue
        seen_ids.add(rec["id"])
        records.append(rec)

    return records


def has_next_page(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    # Enlace "Siguiente" o cualquier link con page=N+1
    for a in soup.select("a[href*='page=']"):
        txt = a.get_text(strip=True).lower()
        if "siguiente" in txt or "next" in txt or "›" in txt or "»" in txt:
            return True
    return False


def scrape(
    max_pages: int = DEFAULT_MAX_PAGES,
    max_items: int | None = None,
) -> list[dict]:
    """
    Recorre páginas del listado y devuelve la lista de personas.
    max_pages=0 significa 'todas las que existan' (con límite de seguridad).
    """
    all_records: list[dict] = []
    seen_ids: set[str] = set()
    page = 1
    hard_limit = 50 if max_pages == 0 else max_pages  # seguridad

    while page <= hard_limit:
        url = LIST_URL if page == 1 else f"{LIST_URL}&page={page}"
        print(f"  → página {page}: {url}", flush=True)

        try:
            html = fetch_html(url)
        except requests.RequestException as exc:
            print(f"  ERROR descargando página {page}: {exc}", file=sys.stderr)
            break

        records = extract_persons_from_html(html)
        if not records:
            print(f"  (sin tarjetas en página {page}, fin)")
            break

        nuevos = 0
        for rec in records:
            if rec["id"] in seen_ids:
                continue
            seen_ids.add(rec["id"])
            all_records.append(rec)
            nuevos += 1
            if max_items and len(all_records) >= max_items:
                print(f"  alcanzado --max={max_items}")
                return all_records

        print(f"  +{nuevos} personas (total acumulado: {len(all_records)})")

        if max_pages != 0 and page >= max_pages:
            break
        if not has_next_page(html):
            break

        page += 1
        time.sleep(PAUSE_BETWEEN_PAGES)

    return all_records


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scraper de personas publicadas en colombiatebusca.com"
    )
    parser.add_argument(
        "--pages", type=int, default=DEFAULT_MAX_PAGES,
        help=f"Máximo de páginas a recorrer (0 = todas). Default: {DEFAULT_MAX_PAGES}",
    )
    parser.add_argument(
        "--max", type=int, default=None,
        help="Máximo de personas a guardar (opcional)",
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUTPUT,
        help=f"Ruta del JSON de salida. Default: {DEFAULT_OUTPUT}",
    )
    args = parser.parse_args()

    print(f"Scrapeando {LIST_URL} …")
    persons = scrape(max_pages=args.pages, max_items=args.max)

    if not persons:
        print(
            "ADVERTENCIA: no se extrajo ninguna persona. "
            "Es posible que el sitio haya cambiado de estructura. "
            "No se sobrescribe el archivo anterior.",
            file=sys.stderr,
        )
        sys.exit(2)

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": LIST_URL,
        "count": len(persons),
        "persons": persons,
    }

    args.out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"OK: {len(persons)} personas escritas en {args.out}")


if __name__ == "__main__":
    main()
