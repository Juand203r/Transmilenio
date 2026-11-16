class Node:
    __slots__ = ("clave", "valor", "hash", "siguiente")

    def __init__(self, clave, valor, hash_clave, siguiente=None):
        self.clave = clave
        self.valor = valor
        self.hash = hash_clave
        self.siguiente = siguiente


class TablaHash:
    """Tabla hash con encadenamiento: arreglo de listas enlazadas de nodos clave-valor."""

    FACTOR_MAXIMO_NUM = 3
    FACTOR_MAXIMO_DEN = 4

    def __init__(self, capacidad=16):
        if capacidad < 1:
            capacidad = 16
        self.tamano = capacidad
        self.tabla = [None] * capacidad
        self.cantidad = 0

    def _buscar_nodo(self, clave):
        """Devuelve el nodo de la clave, o None si no está."""
        h = hash(clave)
        nodo = self.tabla[h % self.tamano]
        while nodo is not None:
            if nodo.hash == h and nodo.clave == clave:
                return nodo
            nodo = nodo.siguiente
        return None

    def set(self, clave, valor):
        """Guarda el valor; si la clave ya estaba, lo reemplaza."""
        h = hash(clave)
        i = h % self.tamano
        nodo = self.tabla[i]
        while nodo is not None:
            if nodo.hash == h and nodo.clave == clave:
                nodo.valor = valor
                return
            nodo = nodo.siguiente
        self.tabla[i] = Node(clave, valor, h, self.tabla[i])
        self.cantidad += 1
        if self.cantidad * self.FACTOR_MAXIMO_DEN > self.tamano * self.FACTOR_MAXIMO_NUM:
            self._redimensionar()

    def get(self, clave):
        """Devuelve el valor de la clave, o None si no está."""
        h = hash(clave)
        nodo = self.tabla[h % self.tamano]
        while nodo is not None:
            if nodo.hash == h and nodo.clave == clave:
                return nodo.valor
            nodo = nodo.siguiente
        return None

    def contiene(self, clave):
        """Devuelve True si la clave está en la tabla."""
        return self._buscar_nodo(clave) is not None

    def delete(self, clave):
        """Quita la clave. Devuelve True si estaba, False si no."""
        h = hash(clave)
        i = h % self.tamano
        anterior = None
        nodo = self.tabla[i]
        while nodo is not None:
            if nodo.hash == h and nodo.clave == clave:
                if anterior is None:
                    self.tabla[i] = nodo.siguiente
                else:
                    anterior.siguiente = nodo.siguiente
                self.cantidad -= 1
                return True
            anterior = nodo
            nodo = nodo.siguiente
        return False

    def claves(self):
        """Devuelve una lista con todas las claves, en orden no garantizado."""
        resultado = []
        for cadena in self.tabla:
            nodo = cadena
            while nodo is not None:
                resultado.append(nodo.clave)
                nodo = nodo.siguiente
        return resultado

    def valores(self):
        """Devuelve una lista con todos los valores, en orden no garantizado."""
        resultado = []
        for cadena in self.tabla:
            nodo = cadena
            while nodo is not None:
                resultado.append(nodo.valor)
                nodo = nodo.siguiente
        return resultado

    def _redimensionar(self):
        """Duplica el arreglo y reenlaza los nodos existentes sin recalcular hash()."""
        nuevo_tamano = self.tamano * 2
        nueva = [None] * nuevo_tamano
        for cadena in self.tabla:
            nodo = cadena
            while nodo is not None:
                siguiente = nodo.siguiente
                i = nodo.hash % nuevo_tamano
                nodo.siguiente = nueva[i]
                nueva[i] = nodo
                nodo = siguiente
        self.tabla = nueva
        self.tamano = nuevo_tamano

    def __len__(self):
        return self.cantidad
