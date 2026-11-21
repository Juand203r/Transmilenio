class Pila:
    """Pila LIFO sobre una list: el tope es el final del arreglo."""

    def __init__(self):
        self.elementos = []

    def push(self, elemento):
        """Agrega el elemento en el tope."""
        self.elementos.append(elemento)

    def pop(self):
        """Quita y devuelve el elemento del tope, o None si está vacía."""
        if not self.elementos:
            return None
        return self.elementos.pop()

    def peek(self):
        """Devuelve el elemento del tope sin quitarlo, o None si está vacía."""
        if not self.elementos:
            return None
        return self.elementos[len(self.elementos) - 1]

    def esta_vacia(self):
        """Devuelve True si no hay elementos."""
        return len(self.elementos) == 0

    def __len__(self):
        return len(self.elementos)
