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
// Última muestra tomada: 10 Ago 2026, ~14:09 (página 1 de resultados).
// Total plataforma en ese momento: 756 registradas · 755 por localizar · 1 localizada
// ─────────────────────────────────────────────────────────────────────────

const SITE_BASE = "https://colombiatebusca.com/";

const SITE_TOTALS = {
  registradas: 756,
  porLocalizar: 755,
  localizadas: 1,
  muestraTomada: "10 Ago 2026, 02:09 pm",
};

// Epicentro reportado del sismo (Chocó) — referencia geográfica del mapa.
const EPICENTRO = {
  nombre: "Epicentro reportado · Chocó",
  lat: 5.2,
  lng: -76.9,
};

// locations: conteos agregados por municipio a partir de los reportes
// visibles en colombiatebusca.com (muestra de la página 1, 60 reportes).
// "query" es el texto usado para armar el enlace de búsqueda al sitio real.
const locations = [
  {
    municipio: "Pereira",
    departamento: "Risaralda",
    lat: 4.8133, lng: -75.6961,
    porLocalizar: 37,
    localizadas: 0,
    query: "Pereira",
  },
  {
    municipio: "Cali",
    departamento: "Valle del Cauca",
    lat: 3.4516, lng: -76.5320,
    porLocalizar: 10,
    localizadas: 0,
    query: "Cali",
  },
  {
    municipio: "Dosquebradas",
    departamento: "Risaralda",
    lat: 4.8390, lng: -75.6710,
    porLocalizar: 6,
    localizadas: 0,
    query: "Dosquebradas",
  },
  {
    municipio: "La Virginia",
    departamento: "Risaralda",
    lat: 4.9019, lng: -75.8814,
    porLocalizar: 1,
    localizadas: 0,
    query: "Virginia",
  },
  {
    municipio: "Armenia",
    departamento: "Quindío",
    lat: 4.5339, lng: -75.6811,
    porLocalizar: 1,
    localizadas: 0,
    query: "Armenia",
  },
  {
    municipio: "La Tebaida",
    departamento: "Quindío",
    lat: 4.4547, lng: -75.7972,
    porLocalizar: 1,
    localizadas: 0,
    query: "Tebaida",
  },
  {
    municipio: "San José",
    departamento: "Caldas",
    lat: 5.0972, lng: -75.7908,
    porLocalizar: 1,
    localizadas: 0,
    query: "San Jos%C3%A9",
  },
  {
    municipio: "Anserma Nuevo",
    departamento: "Valle del Cauca",
    lat: 4.7961, lng: -76.0250,
    porLocalizar: 1,
    localizadas: 0,
    query: "Anserma",
  },
  {
    municipio: "Santa Rosa de Cabal",
    departamento: "Risaralda",
    lat: 4.8694, lng: -75.6222,
    porLocalizar: 1,
    localizadas: 0,
    query: "Santa+Rosa",
  },
  {
    municipio: "Chocó (ubicación sin precisar)",
    departamento: "Chocó",
    lat: 5.2, lng: -76.9,
    porLocalizar: 1,
    localizadas: 0,
    query: "Choco",
    esEpicentro: true,
  },
];
