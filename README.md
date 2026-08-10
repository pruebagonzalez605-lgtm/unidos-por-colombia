# Mapa de emergencia · Sismo Chocó — Colombia te busca

Mapa interactivo que muestra la **concentración geográfica** de reportes
ciudadanos de personas por localizar / localizadas, asociados a la emergencia
sísmica con epicentro reportado en Chocó, a partir de los datos públicos de
[colombiatebusca.com](https://colombiatebusca.com/).

## ⚠️ Decisión de diseño importante

Este proyecto **no replica los registros individuales** (nombres, fotos,
edades, fragmentos de número de documento, dirección exacta) de las personas
reportadas. En su lugar, muestra **conteos agregados por municipio**.

¿Por qué?

1. **Son personas reales y vulnerables** (varias menores de edad, adultos
   mayores desorientados, personas con discapacidad). Duplicar sus datos
   personales en un sitio estático que nadie actualiza puede causar daño real
   — por ejemplo, si alguien ya fue localizado pero la copia sigue
   mostrándolo como desaparecido.
2. El propio sitio advierte explícitamente: *"la información debe
   verificarse antes de difundirse"* y no reemplaza a las autoridades.
3. Un mapa de puntos agregados sigue cumpliendo el objetivo — ver **dónde**
   está concentrada la emergencia — sin los riesgos de privacidad de
   replicar identidades.

Cada punto del mapa enlaza directamente a la búsqueda filtrada en
colombiatebusca.com, para que el detalle individual siempre se consulte
**en la fuente, actualizado en tiempo real**.

## Archivos

- `index.html` — mapa interactivo (Leaflet + tiles oscuros de CARTO).
- `data.js` — conteos agregados por municipio + metadatos del sismo.
- `geo.js` — contorno geográfico de los departamentos de Colombia (para
  acotar el mapa solo a Colombia y dar referencia visual).
- `README.md` — este archivo.

## Mapa acotado solo a Colombia

El mapa usa el contorno real de los departamentos (`geo.js`) para:

- Ajustar la vista inicial (`fitBounds`) al territorio colombiano.
- Oscurecer todo lo que queda fuera del país (máscara con recorte tipo
  "evenodd"), así países vecinos no distraen visualmente.
- Quitar la capa de etiquetas de mapa (que mostraba nombres de países como
  Panamá) — el contexto ahora lo da el propio contorno de departamentos.
- Limitar cuánto se puede desplazar/alejar el mapa (`maxBounds`) para que
  no se salga del área de Colombia.

## Actualización periódica de las cifras totales

El mapa intenta refrescar automáticamente **solo los 3 contadores totales**
(personas registradas / por localizar / localizadas) cada 5 minutos,
haciendo una petición a `https://colombiatebusca.com/` y leyendo esas
cifras de resumen que el propio sitio muestra en su portada. También hay
un botón de actualización manual (↻) junto a las estadísticas.

**Importante — limitación técnica real:** este archivo se abre directo en
el navegador, sin un servidor propio. La petición depende de que
colombiatebusca.com permita solicitudes desde otros orígenes (CORS). Si el
sitio no lo permite (lo más probable, ya que no está pensado para ser
consumido así), el navegador bloqueará la respuesta. En ese caso el mapa
**no se rompe ni inventa datos**: conserva la última cifra conocida y lo
indica claramente en pantalla ("Sin conexión al sitio · último dato: …").

Este refresco automático **solo trae los 3 números agregados de la
portada**, nunca registros individuales — se mantiene el mismo criterio de
privacidad explicado arriba. Si en algún momento quieres que también se
actualicen los conteos por municipio automáticamente, la forma correcta
sería que colombiatebusca.com ofreciera un endpoint/API pública para eso;
replicar el listado completo de personas mediante scraping periódico no es
algo que este proyecto vaya a hacer.

## Origen de los datos

Muestra tomada manualmente de la página 1 de resultados de
`colombiatebusca.com` (60 reportes visibles), filtrados por categorías
relacionadas con el sismo: *Terremoto*, *Desastre natural* y
*Persona extraviada*. Fecha de la muestra: **10 de agosto de 2026, ~14:09**.

Totales de la plataforma en ese momento:

| Registradas | Por localizar | Localizadas |
|---|---|---|
| 756 | 755 | 1 |

> El sitio tiene 13 páginas de resultados (~756 registros en total). Esta
> muestra cubre solo la primera página, ordenada por "más recientes". Los
> conteos por municipio en `data.js` **son un corte parcial**, no el total
> real de cada ciudad.

## El panel "Actividad reciente" nunca muestra registros individuales

`index.html` intencionalmente **no** intenta leer `personas.json` ni hacer
fetch directo a colombiatebusca.com para reconstruir tarjetas individuales
en el navegador de cada visitante. Aunque esos datos no queden guardados en
ningún lado, mostrarlos a cada visitante tiene el mismo riesgo de privacidad
que archivarlos — son personas reales y vulnerables. El panel siempre
muestra la vista agregada por municipio (`renderActivityPanelAggregated`),
sin excepción.

`scrape_personas.py` y `personas.json` se mantienen en el repo solo como
referencia histórica de cómo se armó la muestra inicial — no se ejecutan ni
se sirven en el sitio publicado.

## Actualización automática con Render (solo agregados)

`render-service/` es un servicio Python (Flask) pensado para desplegar en
[Render](https://render.com) como **Web Service**. Corre un scheduler
interno que cada `REFRESH_SECONDS` (5 min por defecto):

1. Recorre `colombiatebusca.com` y cuenta reportes **por municipio**
   (por localizar / localizadas) — nunca guarda ni expone nombre, edad,
   género, id ni el enlace a la ficha de ninguna persona. La garantía está
   en el código: `_parse_cards()` en `scrape_agregado.py` solo devuelve
   `{municipio, departamento, localizado}` por cada tarjeta, y el resto del
   pipeline (`aggregate()`, `/agregado.json`) trabaja únicamente con esos
   tres campos agrupados en conteos.
2. Lee los 3 contadores totales de la portada.

Expone dos endpoints JSON, con CORS abierto porque son datos agregados sin
información personal:

- `GET /agregado.json` → `{ generated_at, locations: [{municipio, departamento, lat, lng, porLocalizar, localizadas, ubicacionAproximada, query}, ...] }`
- `GET /totales.json` → `{ registradas, porLocalizar, localizadas }`

### Desplegar

1. En Render: **New → Web Service**, conecta este repo, y como *Root
   Directory* pon `render-service` (o usa el `render.yaml` incluido con
   **New → Blueprint**, que ya trae el root dir y el `startCommand`
   configurados).
2. Runtime: Python 3. Build command: `pip install -r requirements.txt`.
   Start command: `gunicorn server:app --workers 1 --threads 4 --bind 0.0.0.0:$PORT`.
3. Plan gratuito: el servicio "duerme" tras 15 min sin tráfico y tarda unos
   segundos en despertar con la primera visita — normal en el plan free,
   no es un error. El scheduler solo corre mientras el servicio está
   despierto.
4. Cuando Render te dé la URL pública (ej.
   `https://mapa-choco-agregados.onrender.com`), pégala en `index.html` en
   la constante `RENDER_API_BASE` (buscá `RENDER_API_BASE = ""` cerca de
   la sección de actualización de totales) y vuelve a subir el archivo a
   GitHub Pages.

Con `RENDER_API_BASE` configurado, el mapa hace fetch a estos dos
endpoints cada 5 minutos y redibuja los puntos y contadores. Si el
servicio de Render no responde (dormido, caído, o `RENDER_API_BASE` vacío),
el mapa cae automáticamente a los datos estáticos de `data.js` — nunca se
rompe ni queda en blanco.

### Límite de páginas y frecuencia

`scrape_agregado.py` recorre como máximo `MAX_PAGES = 3` páginas de
resultados por corrida, para no sobrecargar colombiatebusca.com. Igual que
recomienda `README_SCRAPER.md`, mantené `REFRESH_SECONDS` en un valor
razonable (300s o más) — es una plataforma ciudadana, no una API pensada
para scraping intensivo.

## Cómo actualizar los datos honestamente

Si vas a mantener este mapa vivo, la forma correcta de hacerlo es:

1. **No** copiar nombres/fotos/documentos de personas individuales al
   `data.js`.
2. Actualizar solo los **conteos agregados** por municipio y departamento,
   revisando periódicamente `colombiatebusca.com`.
3. Mantener siempre el enlace de cada punto apuntando a la búsqueda en vivo
   del sitio, para que cualquiera que necesite el detalle de una persona
   vea la información más reciente y verificada.
4. Si el sitio ofrece en el futuro una API pública o un feed de datos
   agregados, usarlo en vez de un conteo manual.

## Usarlo como iframe en otro sitio

El mapa se puede incrustar directamente con un `<iframe>` — es un sitio
estático, así que no hay servidor propio que pueda bloquear el embebido con
cabeceras tipo `X-Frame-Options` o `Content-Security-Policy: frame-ancestors`.
Tanto GitHub Pages como Render (sitio estático o Web Service simple) sirven
estos archivos sin esas restricciones por defecto.

Para incrustarlo, agrega `?embed=1` a la URL. Eso activa un modo compacto
pensado para iframes chicos: topbar más angosto, sin subtítulo de marca, sin
leyenda ni panel "sobre estos datos" (para no saturar un espacio reducido), y
agrega un botón "⤢ Ver mapa completo" que abre la versión sin recortar en una
pestaña nueva.

```html
<div style="position:relative;width:100%;padding-bottom:75%;">
  <iframe
    src="https://TU-DOMINIO/index.html?embed=1"
    style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
    loading="lazy"
    referrerpolicy="no-referrer-when-downgrade"
    title="Mapa de emergencia · Sismo Chocó">
  </iframe>
</div>
```

Ver `embed-example.html` para una página de ejemplo completa y funcional
(ábrela directo en el navegador, no necesita servidor). El `padding-bottom`
del contenedor controla la proporción del mapa — `75%` da 4:3, `56.25%`
daría 16:9; ajústalo según el espacio del sitio anfitrión.

El mapa también trae un `ResizeObserver` interno para que, si el iframe
cambia de tamaño (layout responsive del sitio anfitrión, rotación de
pantalla), Leaflet vuelva a medir el contenedor y no se quede con partes
cortadas o en gris.

## Limitaciones conocidas

- Los conteos son aproximados: algunos registros del sitio traen errores de
  digitación en el municipio/departamento (por ejemplo "Pereira, Antioquia"
  cuando Pereira es de Risaralda); se agruparon por el nombre del municipio
  más probable.
- El punto de "Chocó" no tiene ubicación precisa porque el reporte original
  indicaba "No se" como lugar — se ubicó en el centroide aproximado del
  departamento.
- Este mapa **no reemplaza** a las autoridades ni a los organismos de
  emergencia (123, 112, 132, 144, 119).
