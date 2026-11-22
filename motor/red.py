import csv

from .historial import AccionAgregarParada, AccionCerrar, AccionQuitarParada, AccionReabrir
from .lista_doble import ListaDoble
from .ordenar import merge_sort, primer_mayor_o_igual
from .pila import Pila
from .ranking import Ranking
from .tabla_hash import TablaHash
from .abb import AVL
from .viaje import planear_viaje


def _unir(carpeta, archivo):
    """Devuelve la ruta del archivo dentro de la carpeta."""
    if carpeta.endswith("/") or carpeta.endswith("\\"):
        return carpeta + archivo
    return carpeta + "/" + archivo


def _a_minutos(hora):
    """'HH:MM' -> minutos desde las 00:00. Las horas del GTFS mayores a 24
    (25:10) quedan continuas: 25*60+10 = 1510. None si el texto no es una hora."""
    try:
        partes = str(hora).strip().split(":")
        return int(partes[0]) * 60 + int(partes[1])
    except (ValueError, IndexError):
        return None


def _a_texto(minutos):
    """Minutos -> 'HH:MM' (1510 -> '25:10')."""
    return str(minutos // 60).zfill(2) + ":" + str(minutos % 60).zfill(2)


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
        """Lee horarios.csv (Gabriel Matiz).

        Agrupa las horas en la TablaHash horarios con clave "ruta|estacion",
        como lista de minutos ordenada de menor a mayor (merge_sort, que en
        O(m) detecta si ya viene ordenada). Suma a buses_dia de cada estación
        los horarios de las rutas que de verdad paran en ella.
        Costo: O(F) para leer las F filas + O(m log m) por cada lista.
        """
        grupos = []  # (lista, ruta, estacion) en el orden en que aparecen
        with open(_unir(carpeta, "horarios.csv"), newline="", encoding="utf-8") as archivo:
            lector = csv.reader(archivo)
            next(lector, None)
            for fila in lector:
                if len(fila) < 3:
                    continue
                minutos = _a_minutos(fila[2])
                if minutos is None:
                    continue
                clave = fila[0] + "|" + fila[1]
                lista = self.horarios.get(clave)
                if lista is None:
                    lista = []
                    self.horarios.set(clave, lista)
                    grupos.append((lista, fila[0], fila[1]))
                lista.append(minutos)
        for grupo in grupos:
            lista = grupo[0]
            ordenada = merge_sort(lista)
            lista[:] = ordenada
            recorrido = self.rutas.get(grupo[1])
            estacion = self.estaciones.get(grupo[2])
            if recorrido is not None and estacion is not None and recorrido.contiene(grupo[2]):
                estacion.buses_dia += len(lista)

    def _construir_abiertas(self):
        """Arma el ABB balanceado (AVL) con los nombres de las estaciones abiertas,
        ordenados con merge_sort y tomando el del medio como raiz. O(N log N)."""
        nombres = []
        for estacion in self.estaciones.valores():
            if estacion.abierta:
                nombres.append(estacion.nombre)
        self.abiertas = AVL()
        self.abiertas.construir(merge_sort(nombres))

    def _construir_ranking(self):
        """Arma el ranking (R6) con las estaciones abiertas: ordena las claves
        (-buses_dia, nombre) con merge_sort y construye el AVL desde la mitad. O(N log N)."""
        claves = []
        for estacion in self.estaciones.valores():
            if estacion.abierta:
                claves.append((-estacion.buses_dia, estacion.nombre))
        self.ranking_estructura = Ranking()
        self.ranking_estructura.construir(merge_sort(claves))

    def _ranking_quitar(self, nombre):
        """Saca la estación del ranking (al cerrarla). O(log N)."""
        return self.ranking_estructura.quitar(nombre)

    def _ranking_poner(self, nombre):
        """Vuelve a meter la estación con sus buses actuales (al reabrirla). O(log N)."""
        estacion = self.estaciones.get(nombre)
        if estacion is None:
            return False
        return self.ranking_estructura.poner(nombre, estacion.buses_dia)

    def _ranking_actualizar(self, nombre):
        """Reubica la estación si cambiaron sus buses_dia (editar rutas). O(log N).
        Si está cerrada no está en el ranking y no se toca."""
        estacion = self.estaciones.get(nombre)
        if estacion is None:
            return False
        return self.ranking_estructura.actualizar(nombre, estacion.buses_dia)

    def _abiertas_quitar(self, nombre):
        """Saca la estacion del arbol de abiertas (al cerrarla). O(log N)."""
        return self.abiertas.borrar(nombre)

    def _abiertas_poner(self, nombre):
        """Vuelve a meter la estacion en el arbol de abiertas (al reabrirla). O(log N)."""
        return self.abiertas.insertar(nombre)

    def estado(self, nombre):
        """R1: "ABIERTA", "CERRADA" o "NO EXISTE". O(1) promedio (tabla hash)."""
        estacion = self.estaciones.get(nombre)
        if estacion is None:
            return "NO EXISTE"
        if estacion.abierta:
            return "ABIERTA"
        return "CERRADA"

    def autocompletar(self, prefijo, k):
        """R2: hasta k abiertas que empiezan por prefijo, en orden alfabetico.
        Todas quedan entre prefijo y prefijo + un caracter mayor que cualquier
        letra, asi que es un rango del ABB que para al juntar k. O(log N + k)."""
        if k <= 0:
            return []
        return self.abiertas.rango(prefijo, prefijo + "\uffff", k)

    def rango(self, desde, hasta):
        """R3: abiertas entre desde y hasta (inclusive), en orden. O(log N + m)."""
        if hasta < desde:
            return []
        return self.abiertas.rango(desde, hasta)

    def proximo_bus(self, estacion, ruta, hora):
        """R4 (Gabriel Matiz): hora 'HH:MM' del primer bus de esa ruta en esa
        estación a la hora pedida o después; None si no hay más ese día, si la
        estación no existe o está cerrada, o si la ruta no para ahí.
        O(1) para llegar a la lista + O(log H) de búsqueda binaria,
        H = buses de esa ruta en esa estación."""
        est = self.estaciones.get(estacion)
        if est is None or not est.abierta:
            return None
        recorrido = self.rutas.get(ruta)
        if recorrido is None or not recorrido.contiene(estacion):
            return None
        horas = self.horarios.get(ruta + "|" + estacion)
        objetivo = _a_minutos(hora)
        if horas is None or objetivo is None:
            return None
        pos = primer_mayor_o_igual(horas, objetivo)
        if pos == len(horas):
            return None
        return _a_texto(horas[pos])

    def viaje(self, origen, destino):
        return planear_viaje(self, origen, destino)

    def ranking(self, k):
        """R6 (Gabriel Matiz): lista de (nombre, buses_por_dia) de las k estaciones
        abiertas con más buses, de mayor a menor (empates en orden alfabético).
        O(log N + k)."""
        return self.ranking_estructura.primeros(k)

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
        """R8: True si la cerro; False si no existe o ya estaba cerrada.
        El cambio queda en la pila de deshacer (R9). O(log N)."""
        return self._ejecutar(AccionCerrar(self, nombre))

    def reabrir(self, nombre):
        """R8: True si la reabrio; False si no existe o ya estaba abierta. O(log N)."""
        return self._ejecutar(AccionReabrir(self, nombre))

    def _cerrar(self, nombre):
        """Marca la estacion cerrada y la saca del ABB de abiertas y del ranking."""
        estacion = self.estaciones.get(nombre)
        if estacion is None or not estacion.abierta:
            return False
        estacion.abierta = False
        self._abiertas_quitar(nombre)
        self._ranking_quitar(nombre)
        return True

    def _reabrir(self, nombre):
        """Marca la estacion abierta y la vuelve a meter en el ABB y en el ranking."""
        estacion = self.estaciones.get(nombre)
        if estacion is None or estacion.abierta:
            return False
        estacion.abierta = True
        self._abiertas_poner(nombre)
        self._ranking_poner(nombre)
        return True

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
