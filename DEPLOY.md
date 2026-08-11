# Despliegue: GitHub Pages + Render

Este proyecto tiene **dos partes**:

1. **Sitio estático** (`index.html`, `data.js`, `geo.js`, …) → se publica en **GitHub Pages**
2. **Servicio de agregados** (`render-service/`) → se publica en **Render** (plan free)

El mapa funciona solo con los datos estáticos. Render es opcional y sirve para refrescar totales y puntos cada 5 minutos.

---

## 1. Subir a GitHub

```bash
# En tu máquina, dentro de la carpeta del proyecto:
git init
git add .
git commit -m "Mapa de emergencia Sismo Chocó — Colombia te busca"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/mapa-choco.git
git push -u origin main
```

### Activar GitHub Pages

1. Ve a tu repo → **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` / folder: `/ (root)`
4. Save

Tu mapa quedará en:
`https://TU_USUARIO.github.io/mapa-choco/`

---

## 2. Desplegar el servicio en Render

### Opción A — Con `render.yaml` (recomendada)

1. Entra a [https://dashboard.render.com](https://dashboard.render.com) y crea una cuenta (o inicia sesión).
2. **New +** → **Blueprint**
3. Conecta el repositorio de GitHub que acabas de subir.
4. Render detectará `render-service/render.yaml` (o el de la raíz si lo moviste).
5. Confirma el servicio `mapa-choco-agregados` (plan **Free**).
6. Deploy.

### Opción B — Manual (Web Service)

1. **New +** → **Web Service**
2. Conecta el mismo repo de GitHub.
3. Configura:
   - **Name:** `mapa-choco-agregados` (o el que prefieras)
   - **Root Directory:** `render-service`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn server:app --workers 1 --threads 4 --timeout 180 --bind 0.0.0.0:$PORT`
   - **Plan:** Free
4. Environment variable (opcional):
   - `REFRESH_SECONDS` = `300`
5. Create Web Service.

Cuando termine el deploy, copia la URL pública, por ejemplo:

```
https://mapa-choco-agregados.onrender.com
```

### Verificar que funciona

Abre en el navegador:

- `https://TU-SERVICIO.onrender.com/` → debe devolver JSON con `"service": "mapa-choco-agregados"`
- `https://TU-SERVICIO.onrender.com/totales.json` → contadores
- `https://TU-SERVICIO.onrender.com/agregado.json` → lista de municipios

> **Nota plan Free:** el servicio se “duerme” tras ~15 min sin tráfico. La primera petición después del sleep puede tardar 30–60 s (y a veces devolver 503 un momento). El mapa ya contempla ese caso y cae a los datos estáticos de `data.js`.

---

## 3. Conectar el mapa con Render

Edita `index.html` y busca esta línea:

```js
const RENDER_API_BASE = "https://unidos-por-colombia.onrender.com";
```

Cámbiala por la URL de **tu** servicio (sin `/` al final):

```js
const RENDER_API_BASE = "https://mapa-choco-agregados.onrender.com";
```

Haz commit y push:

```bash
git add index.html
git commit -m "Conecta mapa con servicio Render"
git push
```

GitHub Pages se actualizará en 1–2 minutos.

---

## 4. Estructura final del repo

```
mapa-choco/
├── index.html              # Mapa interactivo
├── data.js                 # Fallback estático (conteos agregados)
├── geo.js                  # Contorno de Colombia
├── personas.json           # Opcional (scraper de personas individuales)
├── scrape_personas.py      # Scraper de personas (uso local / Actions)
├── requirements.txt        # deps del scraper de personas
├── embed-example.html
├── README.md
├── README_SCRAPER.md
├── DEPLOY.md               # este archivo
├── .gitignore
└── render-service/         # ← lo que corre en Render
    ├── server.py
    ├── scrape_agregado.py
    ├── municipios_co.py
    ├── requirements.txt
    └── render.yaml
```

---

## 5. (Opcional) Actualizar personas.json con GitHub Actions

Si quieres el panel de actividad con nombres (solo datos públicos), crea
`.github/workflows/scrape.yml` según `README_SCRAPER.md`.

Recuerda: el diseño del proyecto **prioriza agregados** por privacidad.
El servicio de Render **nunca** expone nombres individuales.

---

## Solución de problemas

| Problema | Qué revisar |
|----------|-------------|
| Render devuelve 503 | Espera 30–60 s (cold start) y recarga. Revisa logs en el dashboard. |
| Mapa no actualiza totales | Confirma `RENDER_API_BASE` y que `/totales.json` responde 200. |
| Puntos no se mueven | Confirma `/agregado.json` y mira la consola del navegador (F12). |
| CORS | El servicio ya envía `Access-Control-Allow-Origin: *`. |
| Build falla en Render | Root Directory debe ser `render-service` y `requirements.txt` el de esa carpeta. |
