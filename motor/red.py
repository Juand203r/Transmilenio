import csv

from .tabla_hash import TablaHash


def _unir(carpeta, archivo):
    """Devuelve la ruta del archivo dentro de la carpeta."""
    if carpeta.endswith("/") or carpeta.endswith("\\"):
        return carpeta + archivo
    return carpeta + "/" + archivo


class Estacion:
    """Estación de la red: nombre, si está abierta y cuántos buses pasan al día."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.abierta = True
        self.buses_dia = 0


class Red:
    def __init__(self, carpeta):
        self.carpeta = carpeta
        self.estaciones = TablaHash()
        self.abiertas = None
        self.rutas = TablaHash()
        self.horarios = TablaHash()
        self.rutas_por_estacion = TablaHash()
        self.ranking_estructura = None
        self._cargar_estaciones(carpeta)
        self._cargar_rutas(carpeta)
        self._cargar_horarios(carpeta)
        self._construir_abiertas()
        self._construir_ranking()

    def _cargar_estaciones(self, carpeta):
        """Lee estaciones.csv y crea cada Estacion abierta con buses_dia = 0."""
        with open(_unir(carpeta, "estaciones.csv"), newline="", encoding="utf-8") as archivo:
            lector = csv.reader(archivo)
            next(lector, None)
            for fila in lector:
                if fila:
                    self.estaciones.set(fila[0], Estacion(fila[0]))

    def _cargar_rutas(self, carpeta):
        pass

    def _cargar_horarios(self, carpeta):
        pass

    def _construir_abiertas(self):
        pass

    def _construir_ranking(self):
        pass

    def _ranking_quitar(self, nombre):
        pass

    def _ranking_poner(self, nombre):
        pass

    def _ranking_actualizar(self, nombre):
        pass

    def _abiertas_quitar(self, nombre):
        pass

    def _abiertas_poner(self, nombre):
        pass

    def estado(self, nombre):
        pass

    def autocompletar(self, prefijo, k):
        pass

    def rango(self, desde, hasta):
        pass

    def proximo_bus(self, estacion, ruta, hora):
        pass

    def viaje(self, origen, destino):
        pass

    def ranking(self, k):
        pass

    def agregar_parada(self, ruta, nueva, despues_de):
        pass

    def quitar_parada(self, ruta, estacion):
        pass

    def recorrido(self, ruta, al_reves=False):
        pass

    def cerrar(self, nombre):
        pass

    def reabrir(self, nombre):
        pass

    def deshacer(self):
        pass

    def rehacer(self):
        pass
