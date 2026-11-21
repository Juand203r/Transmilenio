class AccionCerrar:
    def __init__(self, red, nombre):
        self.red = red
        self.nombre = nombre

    def hacer(self):
        """Cierra la estación. Devuelve True si cambió algo."""
        return self.red._cerrar(self.nombre)

    def deshacer(self):
        """Reabre la estación. Devuelve True si cambió algo."""
        return self.red._reabrir(self.nombre)


class AccionReabrir:
    def __init__(self, red, nombre):
        self.red = red
        self.nombre = nombre

    def hacer(self):
        """Reabre la estación. Devuelve True si cambió algo."""
        return self.red._reabrir(self.nombre)

    def deshacer(self):
        """Cierra la estación. Devuelve True si cambió algo."""
        return self.red._cerrar(self.nombre)


class AccionAgregarParada:
    def __init__(self, red, ruta, nueva, despues_de):
        self.red = red
        self.ruta = ruta
        self.nueva = nueva
        self.despues_de = despues_de

    def hacer(self):
        """Agrega la parada. Devuelve True si cambió algo."""
        return self.red._agregar_parada(self.ruta, self.nueva, self.despues_de)

    def deshacer(self):
        """Quita la parada agregada. Devuelve True si cambió algo."""
        return self.red._quitar_parada(self.ruta, self.nueva)


class AccionQuitarParada:
    def __init__(self, red, ruta, estacion):
        self.red = red
        self.ruta = ruta
        self.estacion = estacion
        self.anterior = None
        self.horarios = None

    def hacer(self):
        """Quita la parada guardando su vecina anterior y sus horarios. Devuelve True si cambió algo."""
        lista = self.red.rutas.get(self.ruta)
        if lista is None:
            return False
        nodo = lista.nodo(self.estacion)
        if nodo is None:
            return False
        anterior = None
        if nodo.anterior is not None:
            anterior = nodo.anterior.nombre
        horarios = self.red.horarios.get(self.ruta + "|" + self.estacion)
        if not self.red._quitar_parada(self.ruta, self.estacion):
            return False
        self.anterior = anterior
        self.horarios = horarios
        return True

    def deshacer(self):
        """Devuelve la parada a su posición y con sus horarios. Devuelve True si cambió algo."""
        return self.red._restaurar_parada(self.ruta, self.estacion, self.anterior, self.horarios)
