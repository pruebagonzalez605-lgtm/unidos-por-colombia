# Cómo mantener el panel "en vivo"

Este sitio (`index.html`, `data.js`, `geo.js`) es estático: no tiene
servidor propio. `scrape_personas.py` sí necesita correr en algún lado
con Python — tu computador, un servidor, o un job programado — porque
un navegador no puede ejecutar Python.

El flujo es:

```
scrape_personas.py  →  personas.json  →  index.html lo lee con fetch()
     (Python)             (archivo)         (mismo origen, sin CORS)
```

Mientras `personas.json` esté junto a `index.html` y se actualice
periódicamente, el mapa se ve "en vivo". Si el archivo no existe o está
vacío, el panel cae automáticamente a la vista agregada por municipio
(sin nombres), así que nunca se rompe.

## Opción 1 — Cron en tu propio servidor

```bash
pip install -r requirements.txt

# corre cada 5 minutos, por ejemplo con crontab -e:
*/5 * * * * cd /ruta/al/sitio && /usr/bin/python3 scrape_personas.py >> scraper.log 2>&1
```

Sirve la carpeta completa (index.html + data.js + geo.js + personas.json)
con cualquier servidor estático (nginx, `python -m http.server`, etc).

## Opción 2 — GitHub Actions (sin servidor propio)

Si el sitio se publica con GitHub Pages, puedes programar el scraper
como Action y hacer commit del `personas.json` actualizado:

```yaml
# .github/workflows/scrape.yml
name: Actualizar personas.json
on:
  schedule:
    - cron: "*/10 * * * *"   # cada 10 minutos
  workflow_dispatch: {}

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: python3 scrape_personas.py
      - run: |
          git config user.name "scraper-bot"
          git config user.email "actions@users.noreply.github.com"
          git add personas.json
          git diff --cached --quiet || git commit -m "Actualiza personas.json"
          git push
```

GitHub Pages sirve el `personas.json` más reciente cada vez que el job
hace commit, sin necesidad de un servidor propio corriendo 24/7.

## Notas importantes

- El scraper solo lee la página 1 (más recientes primero) de
  `colombiatebusca.com/?tab=persons` — no descarga fotos ni datos de
  contacto del reportante, solo lo que ya es público en la tarjeta.
- El parseo usa heurísticas tolerantes (busca los enlaces `?person=ID`
  y los símbolos `⌖ ▦ ▣` que usa el sitio), pero si `colombiatebusca.com`
  cambia su HTML, el script puede dejar de encontrar personas. En ese
  caso imprime una advertencia y **no sobrescribe** el `personas.json`
  anterior, para no dejar el sitio sin datos.
- Corre este script con una frecuencia razonable (5–10 min) para no
  sobrecargar el sitio de origen — es una plataforma ciudadana, no una
  API pensada para scraping intensivo.
