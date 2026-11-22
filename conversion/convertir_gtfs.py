"""Convierte el GTFS de TransMilenio (zip) a los tres CSV que lee el motor.

Autor: Gabriel Matiz. Fuera de motor/ se puede usar cualquier librería;
aquí usamos pandas.

Uso:
    python conversion/convertir_gtfs.py ruta/al/gtfs.zip datos/

Escribe datos/estaciones.csv (nombre), datos/rutas.csv (ruta, orden, estacion)
y datos/horarios.csv (ruta, estacion, hora). Con --coordenadas escribe además
datos/coordenadas.csv (nombre, lat, lon) para el mapa del front; el motor no
lee ese archivo.

Decisiones (ver README, "Decisiones Generales del Proyecto"):
- Nombres: stop_name en mayúsculas, sin tildes y sin espacios de más. Las
  paradas seguidas con el mismo nombre (vagones de una estación) cuentan una vez.
- Rutas: cada ruta va en un solo sentido. Para cada route_short_name, cada
  secuencia distinta de paradas es una ruta llamada <route_short_name>-<n>.
- Horas: el GTFS escribe los viajes que pasan de medianoche como 24:xx, 25:xx...
  Se dejan así, en HH:MM continuo (25:10), sin restar 24: el motor las pasa a
  minutos (25*60+10 = 1510) y las compara sin saltos.
- Horarios repetidos (misma ruta, estación y minuto) se guardan una sola vez.
"""
import sys
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd


def limpiar(nombre):
    """Mayúsculas, sin tildes y sin espacios de más."""
    nombre = unicodedata.normalize("NFKD", str(nombre))
    nombre = "".join(c for c in nombre if not unicodedata.combining(c))
    return " ".join(nombre.upper().split())


def hora_hhmm(texto):
    """'5:07:00' -> '05:07' ; '25:10:00' -> '25:10' (sin restar 24)."""
    partes = str(texto).strip().split(":")
    return f"{int(partes[0]):02d}:{int(partes[1]):02d}"


def convertir(zip_gtfs, salida, coordenadas=False):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_gtfs) as z:
        leer = lambda n: pd.read_csv(z.open(n), dtype=str)
        stops = leer("stops.txt")
        routes = leer("routes.txt")
        trips = leer("trips.txt")
        stop_times = leer("stop_times.txt")

    stops["estacion"] = stops["stop_name"].map(limpiar)
    st = stop_times.merge(stops[["stop_id", "estacion"]], on="stop_id")
    st["stop_sequence"] = st["stop_sequence"].astype(int)
    st = st.sort_values(["trip_id", "stop_sequence"])
    # dos paradas seguidas con el mismo nombre (vagones) cuentan como una
    st = st[st["estacion"] != st.groupby("trip_id")["estacion"].shift()]

    trips = trips.merge(routes[["route_id", "route_short_name"]], on="route_id")
    secuencias = st.groupby("trip_id")["estacion"].agg(tuple).rename("secuencia")
    trips = trips.merge(secuencias, left_on="trip_id", right_index=True)

    nombres_ruta = {}
    for corto, grupo in trips.groupby("route_short_name"):
        for i, sec in enumerate(sorted(grupo["secuencia"].unique()), 1):
            nombres_ruta[(corto, sec)] = f"{corto}-{i}"
    trips["ruta"] = [nombres_ruta[(c, s)] for c, s in zip(trips["route_short_name"], trips["secuencia"])]

    # rutas.csv: una fila por parada, en orden (sin repetir estación dentro de la ruta)
    filas = []
    for (corto, sec), ruta in nombres_ruta.items():
        vistos = set()
        orden = 0
        for estacion in sec:
            if estacion in vistos:
                continue
            vistos.add(estacion)
            orden += 1
            filas.append((ruta, orden, estacion))
    rutas = pd.DataFrame(filas, columns=["ruta", "orden", "estacion"]).sort_values(["ruta", "orden"])

    # horarios.csv: cada vez que un viaje de esa ruta pasa por la estación
    hor = st.merge(trips[["trip_id", "ruta"]], on="trip_id")
    hor["hora"] = hor["departure_time"].fillna(hor["arrival_time"]).map(hora_hhmm)
    hor = hor[["ruta", "estacion", "hora"]].drop_duplicates()

    estaciones = pd.DataFrame({"nombre": sorted(rutas["estacion"].unique())})
    estaciones.to_csv(salida / "estaciones.csv", index=False)
    rutas.to_csv(salida / "rutas.csv", index=False)
    hor.to_csv(salida / "horarios.csv", index=False)
    print(len(estaciones), "estaciones,", rutas["ruta"].nunique(), "rutas,", len(hor), "horarios")

    if coordenadas:
        # mediana de las paradas de cada estación: una parada homónima lejana no la mueve
        stops["lat"] = stops["stop_lat"].astype(float)
        stops["lon"] = stops["stop_lon"].astype(float)
        centro = stops.groupby("estacion")[["lat", "lon"]].median().round(6)
        coords = centro.reindex(estaciones["nombre"]).reset_index().dropna()
        coords.columns = ["nombre", "lat", "lon"]
        coords.to_csv(salida / "coordenadas.csv", index=False)
        print(len(coords), "estaciones con coordenadas")


if __name__ == "__main__":
    convertir(sys.argv[1], sys.argv[2], "--coordenadas" in sys.argv)
