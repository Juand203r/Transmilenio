class Node:
    __slots__ = ("dato", "siguiente")

    def __init__(self, dato):
        self.dato = dato
        self.siguiente = None


class Cola:
    """Cola FIFO con lista enlazada y puntero al último nodo: enqueue y dequeue son O(1)."""

    def __init__(self):
        self.frente = None
        self.final = None
        self.cantidad = 0

    def enqueue(self, dato):
        """Agrega el dato al final de la cola."""
        nuevo = Node(dato)
        if self.final is None:
            self.frente = nuevo
        else:
            self.final.siguiente = nuevo
        self.final = nuevo
        self.cantidad += 1

    def dequeue(self):
        """Quita y devuelve el dato del frente, o None si está vacía."""
        nodo = self.frente
        if nodo is None:
            return None
        self.frente = nodo.siguiente
        if self.frente is None:
            self.final = None
        self.cantidad -= 1
        return nodo.dato

    def esta_vacia(self):
        """Devuelve True si no hay datos."""
        return self.cantidad == 0

    def __len__(self):
        return self.cantidad
