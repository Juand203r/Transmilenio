"""R6: ranking de las estaciones abiertas con más buses al día (Gabriel Matiz).

El ranking se consulta muy seguido y cambia poco (cerrar, reabrir o editar una
ruta). Por eso no se recalcula en cada consulta: se mantiene ordenado todo el
tiempo en un árbol binario de búsqueda balanceado (AVL).

- Clave de cada nodo: (-buses_dia, nombre). El árbol queda de menor a mayor,
  así que primero salen las estaciones con MÁS buses (por el signo menos) y,
  si empatan, en orden alfabético.
- Una TablaHash nombre -> clave actual recuerda dónde está cada estación.
  Así se puede borrar su clave vieja aunque buses_dia ya haya cambiado.

Costos (N = estaciones abiertas, k = cuántas se piden):
- construir: O(N) a partir de las claves ya ordenadas (el del medio es la raíz).
- poner, quitar, actualizar: O(log N), porque el AVL nunca pasa de altura O(log N).
- primeros(k): O(log N + k), baja hasta la mínima y recorre en orden k nodos.
"""

from .tabla_hash import TablaHash


class _Nodo:
    def __init__(self, clave):
        self.clave = clave
        self.izquierda = None
        self.derecha = None
        self.altura = 1


def _altura(nodo):
    if nodo is None:
        return 0
    return nodo.altura


def _actualizar_altura(nodo):
    a = _altura(nodo.izquierda)
    b = _altura(nodo.derecha)
    if a > b:
        nodo.altura = a + 1
    else:
        nodo.altura = b + 1


def _rotar_derecha(y):
    x = y.izquierda
    y.izquierda = x.derecha
    x.derecha = y
    _actualizar_altura(y)
    _actualizar_altura(x)
    return x


def _rotar_izquierda(x):
    y = x.derecha
    x.derecha = y.izquierda
    y.izquierda = x
    _actualizar_altura(x)
    _actualizar_altura(y)
    return y


def _balancear(nodo):
    """Si un lado quedó más de 1 nivel más alto que el otro, rota."""
    _actualizar_altura(nodo)
    factor = _altura(nodo.izquierda) - _altura(nodo.derecha)
    if factor > 1:
        if _altura(nodo.izquierda.izquierda) < _altura(nodo.izquierda.derecha):
            nodo.izquierda = _rotar_izquierda(nodo.izquierda)
        return _rotar_derecha(nodo)
    if factor < -1:
        if _altura(nodo.derecha.derecha) < _altura(nodo.derecha.izquierda):
            nodo.derecha = _rotar_derecha(nodo.derecha)
        return _rotar_izquierda(nodo)
    return nodo


class Ranking:
    def __init__(self):
        self.raiz = None
        self.cantidad = 0
        self.clave_de = TablaHash()  # nombre -> (-buses, nombre) que está en el árbol

    def __len__(self):
        return self.cantidad

    def contiene(self, nombre):
        return self.clave_de.get(nombre) is not None

    # ---------- construir ----------

    def construir(self, claves_ordenadas):
        """Arma el árbol balanceado desde claves (-buses, nombre) ya ordenadas. O(N)."""
        self.raiz = self._construir(claves_ordenadas, 0, len(claves_ordenadas) - 1)
        self.cantidad = len(claves_ordenadas)
        for clave in claves_ordenadas:
            self.clave_de.set(clave[1], clave)

    def _construir(self, claves, izquierda, derecha):
        if izquierda > derecha:
            return None
        medio = (izquierda + derecha) // 2
        nodo = _Nodo(claves[medio])
        nodo.izquierda = self._construir(claves, izquierda, medio - 1)
        nodo.derecha = self._construir(claves, medio + 1, derecha)
        _actualizar_altura(nodo)
        return nodo

    # ---------- poner, quitar, actualizar ----------

    def poner(self, nombre, buses):
        """Mete la estación con sus buses. False si ya estaba. O(log N)."""
        if self.contiene(nombre):
            return False
        clave = (-buses, nombre)
        self.raiz = self._insertar(self.raiz, clave)
        self.clave_de.set(nombre, clave)
        self.cantidad += 1
        return True

    def quitar(self, nombre):
        """Saca la estación. False si no estaba. O(log N)."""
        clave = self.clave_de.get(nombre)
        if clave is None:
            return False
        self.raiz = self._borrar(self.raiz, clave)
        self.clave_de.delete(nombre)
        self.cantidad -= 1
        return True

    def actualizar(self, nombre, buses):
        """Cambia los buses de una estación que está en el ranking. O(log N).
        Si la estación no está (por ejemplo, está cerrada) no hace nada."""
        clave = self.clave_de.get(nombre)
        if clave is None or clave[0] == -buses:
            return False
        self.quitar(nombre)
        self.poner(nombre, buses)
        return True

    def _insertar(self, nodo, clave):
        if nodo is None:
            return _Nodo(clave)
        if clave < nodo.clave:
            nodo.izquierda = self._insertar(nodo.izquierda, clave)
        else:
            nodo.derecha = self._insertar(nodo.derecha, clave)
        return _balancear(nodo)

    def _borrar(self, nodo, clave):
        if nodo is None:
            return None
        if clave < nodo.clave:
            nodo.izquierda = self._borrar(nodo.izquierda, clave)
        elif nodo.clave < clave:
            nodo.derecha = self._borrar(nodo.derecha, clave)
        else:
            if nodo.izquierda is None:
                return nodo.derecha
            if nodo.derecha is None:
                return nodo.izquierda
            # dos hijos: lo reemplaza el menor del subárbol derecho
            sucesor = nodo.derecha
            while sucesor.izquierda is not None:
                sucesor = sucesor.izquierda
            nodo.clave = sucesor.clave
            nodo.derecha = self._borrar_minimo(nodo.derecha)
        return _balancear(nodo)

    def _borrar_minimo(self, nodo):
        if nodo.izquierda is None:
            return nodo.derecha
        nodo.izquierda = self._borrar_minimo(nodo.izquierda)
        return _balancear(nodo)

    # ---------- consulta ----------

    def primeros(self, k):
        """Lista de (nombre, buses) de las k primeras, de más a menos buses. O(log N + k)."""
        salida = []
        if k <= 0:
            return salida
        # recorrido en orden sin recursión: una pila con el camino hacia la izquierda
        camino = []
        nodo = self.raiz
        while len(salida) < k and (nodo is not None or len(camino) > 0):
            while nodo is not None:
                camino.append(nodo)
                nodo = nodo.izquierda
            nodo = camino.pop()
            salida.append((nodo.clave[1], -nodo.clave[0]))
            nodo = nodo.derecha
        return salida
