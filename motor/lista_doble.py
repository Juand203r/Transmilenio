from .tabla_hash import TablaHash


class Node:
    __slots__ = ("nombre", "siguiente", "anterior")

    def __init__(self, nombre):
        self.nombre = nombre
        self.siguiente = None
        self.anterior = None


class ListaDoble:
    """Lista doblemente enlazada de nombres con cabeza, cola y tabla nombre -> nodo."""

    def __init__(self):
        self.cabeza = None
        self.cola = None
        self.indice = TablaHash()

    def nodo(self, nombre):
        """Devuelve el nodo del nombre, o None si no está."""
        return self.indice.get(nombre)

    def contiene(self, nombre):
        """Devuelve True si el nombre está en la lista."""
        return self.indice.get(nombre) is not None

    def agregar_al_final(self, nombre):
        """Agrega al final. Devuelve False si el nombre ya estaba."""
        if self.indice.get(nombre) is not None:
            return False
        nuevo = Node(nombre)
        if self.cola is None:
            self.cabeza = nuevo
        else:
            nuevo.anterior = self.cola
            self.cola.siguiente = nuevo
        self.cola = nuevo
        self.indice.set(nombre, nuevo)
        return True

    def insertar_al_inicio(self, nombre):
        """Agrega al inicio. Devuelve False si el nombre ya estaba."""
        if self.indice.get(nombre) is not None:
            return False
        nuevo = Node(nombre)
        if self.cabeza is None:
            self.cola = nuevo
        else:
            nuevo.siguiente = self.cabeza
            self.cabeza.anterior = nuevo
        self.cabeza = nuevo
        self.indice.set(nombre, nuevo)
        return True

    def insertar_despues(self, despues_de, nombre):
        """Inserta justo después de despues_de. Devuelve False si despues_de no está o nombre ya estaba."""
        referencia = self.indice.get(despues_de)
        if referencia is None or self.indice.get(nombre) is not None:
            return False
        nuevo = Node(nombre)
        nuevo.anterior = referencia
        nuevo.siguiente = referencia.siguiente
        if referencia.siguiente is None:
            self.cola = nuevo
        else:
            referencia.siguiente.anterior = nuevo
        referencia.siguiente = nuevo
        self.indice.set(nombre, nuevo)
        return True

    def quitar(self, nombre):
        """Quita el nombre. Devuelve True si estaba, False si no."""
        nodo = self.indice.get(nombre)
        if nodo is None:
            return False
        if nodo.anterior is None:
            self.cabeza = nodo.siguiente
        else:
            nodo.anterior.siguiente = nodo.siguiente
        if nodo.siguiente is None:
            self.cola = nodo.anterior
        else:
            nodo.siguiente.anterior = nodo.anterior
        nodo.siguiente = None
        nodo.anterior = None
        self.indice.delete(nombre)
        return True

    def nombres(self, al_reves=False):
        """Devuelve la lista de nombres de cabeza a cola, o de cola a cabeza si al_reves."""
        resultado = []
        if al_reves:
            nodo = self.cola
            while nodo is not None:
                resultado.append(nodo.nombre)
                nodo = nodo.anterior
        else:
            nodo = self.cabeza
            while nodo is not None:
                resultado.append(nodo.nombre)
                nodo = nodo.siguiente
        return resultado

    def __len__(self):
        return len(self.indice)
