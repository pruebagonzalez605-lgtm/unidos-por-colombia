// ─────────────────────────────────────────────────────────────────────────
// Datos AGREGADOS por ubicación — Colombia te busca (colombiatebusca.com)
// Fuente: colombiatebusca.com — categorías "Terremoto", "Desastre natural"
//         y "Persona extraviada" asociadas a la emergencia sísmica.
//
// IMPORTANTE: Estos son CONTEOS por municipio, NO un listado de personas.
// No se almacenan nombres, fotos ni números de documento individuales:
// esa información cambia en tiempo real (personas que son localizadas,
// correcciones, nuevos reportes) y solo debe consultarse en la fuente
// oficial para evitar difundir datos desactualizados o incorrectos sobre
// personas reales y vulnerables.
//
// Última muestra tomada: 11 Ago 2026, 12:42 am
// Total plataforma en ese momento: 2455 registradas · 2398 por localizar · 55 localizadas
// ─────────────────────────────────────────────────────────────────────────

const SITE_BASE = "https://colombiatebusca.com/";

const SITE_TOTALS = {
  registradas: 2455,
  porLocalizar: 2398,
  localizadas: 55,
  muestraTomada: "11 Ago 2026, 12:42 am",
};

// Epicentro reportado del sismo (Chocó) — referencia geográfica del mapa.
const EPICENTRO = {
  nombre: "Epicentro reportado · Chocó",
  lat: 5.2,
  lng: -76.9,
};

// locations: conteos agregados por municipio a partir de los reportes
// visibles en colombiatebusca.com (muestra de las primeras páginas).
// "query" es el texto usado para armar el enlace de búsqueda al sitio real.
const locations = [
  {
    "municipio": "Pereira",
    "departamento": "Risaralda",
    "lat": 4.8133,
    "lng": -75.6961,
    "ubicacionAproximada": false,
    "porLocalizar": 28,
    "localizadas": 0,
    "query": "Pereira"
  },
  {
    "municipio": "Cali",
    "departamento": "Valle del Cauca",
    "lat": 3.4516,
    "lng": -76.532,
    "ubicacionAproximada": false,
    "porLocalizar": 18,
    "localizadas": 0,
    "query": "Cali"
  },
  {
    "municipio": "Sin precisar",
    "departamento": "Quindío",
    "lat": 4.4975,
    "lng": -75.7018,
    "ubicacionAproximada": true,
    "porLocalizar": 3,
    "localizadas": 0,
    "query": "Sin precisar"
  },
  {
    "municipio": "Quibdó",
    "departamento": "Chocó",
    "lat": 5.6947,
    "lng": -76.6583,
    "ubicacionAproximada": false,
    "porLocalizar": 2,
    "localizadas": 0,
    "query": "Quibdó"
  },
  {
    "municipio": "Dosquebradas",
    "departamento": "Risaralda",
    "lat": 4.839,
    "lng": -75.671,
    "ubicacionAproximada": false,
    "porLocalizar": 2,
    "localizadas": 0,
    "query": "Dosquebradas"
  },
  {
    "municipio": "El águila",
    "departamento": "Valle del Cauca",
    "lat": 3.9802,
    "lng": -76.5664,
    "ubicacionAproximada": true,
    "porLocalizar": 1,
    "localizadas": 0,
    "query": "El águila"
  },
  {
    "municipio": "Cajamarca",
    "departamento": "Tolima",
    "lat": 4.4422,
    "lng": -75.3128,
    "ubicacionAproximada": false,
    "porLocalizar": 1,
    "localizadas": 0,
    "query": "Cajamarca"
  },
  {
    "municipio": "Sevilla",
    "departamento": "Valle del Cauca",
    "lat": 3.9802,
    "lng": -76.5664,
    "ubicacionAproximada": true,
    "porLocalizar": 1,
    "localizadas": 0,
    "query": "Sevilla"
  },
  {
    "municipio": "Manizales",
    "departamento": "Caldas",
    "lat": 5.0689,
    "lng": -75.5174,
    "ubicacionAproximada": false,
    "porLocalizar": 1,
    "localizadas": 0,
    "query": "Manizales"
  },
  {
    "municipio": "Bogotá",
    "departamento": "Cundinamarca",
    "lat": 4.711,
    "lng": -74.0721,
    "ubicacionAproximada": false,
    "porLocalizar": 1,
    "localizadas": 0,
    "query": "Bogotá"
  }
];
