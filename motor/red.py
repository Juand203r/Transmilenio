import csv

from .historial import AccionAgregarParada, AccionCerrar, AccionQuitarParada, AccionReabrir
from .lista_doble import ListaDoble
from .ordenar import merge_sort
from .pila import Pila
from .tabla_hash import TablaHash


def _unir(carpeta, archivo):
    """Devuelve la ruta del archivo dentro de la carpeta."""
    if carpeta.endswith("/") or carpeta.endswith("\\"):
        return carpeta + archivo
    return carpeta + "/" + archivo


def _esta_ordenada(pares):
    """Devuelve True si los pares vienen con orden no decreciente."""
    for i in range(1, len(pares)):
        if pares[i - 1][0] > pares[i][0]:
            return False
    return True


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
        self.pila_deshacer = Pila()
        self.pila_rehacer = Pila()
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
        """Lee rutas.csv, ordena cada ruta por orden si hace falta y arma rutas y rutas_por_estacion."""
        for nombre in self.estaciones.claves():
            self.rutas_por_estacion.set(nombre, [])
        grupos = TablaHash()
        with open(_unir(carpeta, "rutas.csv"), newline="", encoding="utf-8") as archivo:
            lector = csv.reader(archivo)
            next(lector, None)
            for fila in lector:
                if fila:
                    pares = grupos.get(fila[0])
                    if pares is None:
                        pares = []
                        grupos.set(fila[0], pares)
                    pares.append((int(fila[1]), fila[2]))
        for ruta in grupos.claves():
            pares = grupos.get(ruta)
            if not _esta_ordenada(pares):
                pares = merge_sort(pares, lambda par: par[0])
            lista = ListaDoble()
            for par in pares:
                estacion = par[1]
                if self.estaciones.get(estacion) is not None and lista.agregar_al_final(estacion):
                    self.rutas_por_estacion.get(estacion).append(ruta)
            self.rutas.set(ruta, lista)

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

    def _agregar_parada(self, ruta, nueva, despues_de):
        """Agrega nueva justo después de despues_de. Devuelve True si cambió algo."""
        lista = self.rutas.get(ruta)
        estacion = self.estaciones.get(nueva)
        if lista is None or estacion is None:
            return False
        if not lista.insertar_despues(despues_de, nueva):
            return False
        self.rutas_por_estacion.get(nueva).append(ruta)
        horarios = self.horarios.get(ruta + "|" + despues_de)
        if horarios is not None:
            copia = horarios[:]
            self.horarios.set(ruta + "|" + nueva, copia)
            estacion.buses_dia += len(copia)
            self._ranking_actualizar(nueva)
        return True

    def _quitar_parada(self, ruta, nombre):
        """Quita la estación de la ruta. Devuelve True si cambió algo."""
        lista = self.rutas.get(ruta)
        if lista is None or not lista.quitar(nombre):
            return False
        rutas = self.rutas_por_estacion.get(nombre)
        for i in range(len(rutas)):
            if rutas[i] == ruta:
                rutas[i] = rutas[len(rutas) - 1]
                rutas.pop()
                break
        clave = ruta + "|" + nombre
        horarios = self.horarios.get(clave)
        if horarios is not None:
            self.horarios.delete(clave)
            self.estaciones.get(nombre).buses_dia -= len(horarios)
            self._ranking_actualizar(nombre)
        return True

    def _restaurar_parada(self, ruta, nombre, anterior, horarios):
        """Reinserta la estación después de anterior (o al inicio) con sus horarios. Devuelve True si cambió algo."""
        lista = self.rutas.get(ruta)
        if lista is None:
            return False
        if anterior is None:
            insertada = lista.insertar_al_inicio(nombre)
        else:
            insertada = lista.insertar_despues(anterior, nombre)
        if not insertada:
            return False
        self.rutas_por_estacion.get(nombre).append(ruta)
        if horarios is not None:
            self.horarios.set(ruta + "|" + nombre, horarios)
            self.estaciones.get(nombre).buses_dia += len(horarios)
            self._ranking_actualizar(nombre)
        return True

    def _ejecutar(self, accion):
        """Hace la acción; si cambió algo la apila para deshacer y vacía la pila de rehacer."""
        if accion.hacer():
            self.pila_deshacer.push(accion)
            self.pila_rehacer = Pila()
            return True
        return False

    def agregar_parada(self, ruta, nueva, despues_de):
        return self._ejecutar(AccionAgregarParada(self, ruta, nueva, despues_de))

    def quitar_parada(self, ruta, estacion):
        return self._ejecutar(AccionQuitarParada(self, ruta, estacion))

    def recorrido(self, ruta, al_reves=False):
        lista = self.rutas.get(ruta)
        if lista is None:
            return []
        return lista.nombres(al_reves)

    def cerrar(self, nombre):
        pass

    def reabrir(self, nombre):
        pass

    def deshacer(self):
        if self.pila_deshacer.esta_vacia():
            return False
        accion = self.pila_deshacer.pop()
        accion.deshacer()
        self.pila_rehacer.push(accion)
        return True

    def rehacer(self):
        if self.pila_rehacer.esta_vacia():
            return False
        accion = self.pila_rehacer.pop()
        accion.hacer()
        self.pila_deshacer.push(accion)
        return True
