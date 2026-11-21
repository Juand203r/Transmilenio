from .cola import Cola
from .ordenar import merge_sort


def _esta_ordenada(llegadas):
    """Devuelve True si las llegadas vienen en orden no decreciente."""
    for i in range(1, len(llegadas)):
        if llegadas[i - 1] > llegadas[i]:
            return False
    return True


def simular_fila(llegadas, frecuencia, capacidad):
    """Devuelve, en el orden de llegadas, el segundo en que salió el bus de cada persona."""
    total = len(llegadas)
    if capacidad < 1 or frecuencia < 1:
        return [None] * total
    if _esta_ordenada(llegadas):
        orden = list(range(total))
    else:
        orden = merge_sort(list(range(total)), lambda i: llegadas[i])
    salidas = [None] * total
    cola = Cola()
    siguiente = 0
    salida = frecuencia
    while siguiente < total or not cola.esta_vacia():
        if cola.esta_vacia():
            primera = llegadas[orden[siguiente]]
            if primera > salida:
                salida = ((primera + frecuencia - 1) // frecuencia) * frecuencia
        while siguiente < total and llegadas[orden[siguiente]] <= salida:
            cola.enqueue(orden[siguiente])
            siguiente += 1
        subieron = 0
        while subieron < capacidad and not cola.esta_vacia():
            salidas[cola.dequeue()] = salida
            subieron += 1
        salida += frecuencia
    return salidas
