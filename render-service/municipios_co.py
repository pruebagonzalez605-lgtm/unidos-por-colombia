# -*- coding: utf-8 -*-
"""
Coordenadas aproximadas para ubicar puntos en el mapa.

1) MUNICIPIOS: lat/lng de cabecera municipal para los municipios más
   comunes en los reportes (capitales de departamento + municipios que ya
   aparecían en la muestra inicial). Está pensado para crecer con el
   tiempo, no para ser exhaustivo.

2) DEPARTAMENTOS: centroide aproximado de cada departamento (calculado a
   partir del contorno geográfico en geo.js), usado como respaldo cuando un
   municipio reportado no está en la lista de arriba. Es una aproximación
   razonable para "el punto cae dentro del departamento correcto", no una
   ubicación precisa del municipio.
"""

MUNICIPIOS = {
    "pereira": (4.8133, -75.6961),
    "cali": (3.4516, -76.5320),
    "dosquebradas": (4.8390, -75.6710),
    "la virginia": (4.8967, -75.8797),
    "armenia": (4.5339, -75.6811),
    "la tebaida": (4.4547, -75.7972),
    "san jose": (5.4058, -75.5983),         # San José del Palmar / genérico Caldas
    "anserma nuevo": (4.7822, -75.9803),
    "santa rosa de cabal": (4.8694, -75.6217),
    "bogota": (4.7110, -74.0721),
    "santafe de bogota": (4.7110, -74.0721),
    "medellin": (6.2442, -75.5812),
    "barranquilla": (10.9639, -74.7964),
    "cartagena": (10.3910, -75.4794),
    "quibdo": (5.6947, -76.6583),
    "manizales": (5.0689, -75.5174),
    "ibague": (4.4389, -75.2322),
    "neiva": (2.9273, -75.2819),
    "villavicencio": (4.1420, -73.6266),
    "cucuta": (7.8939, -72.5078),
    "bucaramanga": (7.1193, -73.1227),
    "pasto": (1.2136, -77.2811),
    "popayan": (2.4448, -76.6147),
    "monteria": (8.7479, -75.8814),
    "sincelejo": (9.3047, -75.3978),
    "riohacha": (11.5444, -72.9072),
    "valledupar": (10.4631, -73.2532),
    "tunja": (5.5353, -73.3678),
    "florencia": (1.6144, -75.6062),
    "yopal": (5.3378, -72.3959),
    "mocoa": (1.1517, -76.6478),
    "san andres": (12.5847, -81.7006),
    "leticia": (-4.2153, -69.9406),
    "inirida": (3.8653, -67.9239),
    "san jose del guaviare": (2.5679, -72.6413),
    "mitu": (1.1983, -70.1733),
    "puerto carreno": (6.1892, -67.4859),
    "arauca": (7.0847, -70.7591),
    "cajamarca": (4.4422, -75.3128),
    "cartago": (4.7464, -75.9117),
    "buenaventura": (3.8801, -77.0312),
    "tulua": (4.0847, -76.1954),
    "palmira": (3.5394, -76.3036),
    "bumangues": (7.1193, -73.1227),
    "soacha": (4.5794, -74.2168),
    "bello": (6.3373, -75.5580),
    "envigado": (6.1719, -75.5915),
    "itagui": (6.1846, -75.5991),
    "riohacha": (11.5444, -72.9072),
}

DEPARTAMENTOS = {
    "antioquia": (7.0012, -75.8355),
    "atlantico": (10.6748, -74.9734),
    "santafe de bogota d.c": (4.2860, -74.2111),
    "bogota": (4.2860, -74.2111),
    "bogota d.c": (4.2860, -74.2111),
    "bolivar": (9.1246, -74.7638),
    "boyaca": (5.8486, -73.2948),
    "caldas": (5.3511, -75.3802),
    "caqueta": (0.6667, -73.8099),
    "cauca": (2.3152, -76.8175),
    "cesar": (9.2903, -73.5237),
    "cordoba": (8.5312, -75.6966),
    "cundinamarca": (4.7551, -74.1739),
    "choco": (6.0161, -77.0042),
    "huila": (2.6651, -75.6018),
    "la guajira": (11.4516, -72.4932),
    "magdalena": (10.1893, -74.2650),
    "meta": (3.2176, -73.1112),
    "narino": (1.5739, -77.8222),
    "norte de santander": (7.8711, -72.9494),
    "quindio": (4.4975, -75.7018),
    "risaralda": (5.0608, -75.8931),
    "santander": (6.6108, -73.4283),
    "sucre": (9.1351, -75.2059),
    "tolima": (4.0760, -75.2121),
    "valle del cauca": (3.9802, -76.5664),
    "arauca": (6.4810, -71.1802),
    "casanare": (5.4455, -71.7366),
    "putumayo": (0.3383, -75.6180),
    "amazonas": (-1.4415, -71.7339),
    "guainia": (2.8315, -68.8597),
    "guaviare": (1.9144, -71.8680),
    "vaupes": (0.3209, -70.5725),
    "vichada": (4.2525, -69.2609),
    "san andres y providencia": (13.3601, -81.3756),
    "archipielago de san andres providencia y santa catalina": (13.3601, -81.3756),
}


def _strip_accents(s: str) -> str:
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def normalize(name: str) -> str:
    return _strip_accents((name or "").strip().lower())


def geocode(municipio: str, departamento: str):
    """Devuelve (lat, lng, exacto: bool) — exacto=False si se usó el
    centroide del departamento como respaldo en vez del municipio real."""
    m = normalize(municipio)
    if m in MUNICIPIOS:
        return (*MUNICIPIOS[m], True)
    d = normalize(departamento)
    if d in DEPARTAMENTOS:
        return (*DEPARTAMENTOS[d], False)
    return (4.5709, -74.2973, False)  # centro aproximado de Colombia, último recurso
