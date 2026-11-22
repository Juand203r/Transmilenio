"""Ordenamiento y búsqueda propios del motor (Gabriel Matiz).

sorted, .sort() y bisect están prohibidos dentro de motor/, así que aquí
están las dos piezas que usan los demás módulos:

- merge_sort(lista, clave=None): ordena de forma estable en O(n log n).
- primer_mayor_o_igual(lista, objetivo): búsqueda binaria en O(log n).
"""


def _valor(x, clave):
    if clave is None:
        return x
    return clave(x)


def esta_ordenada(lista, clave=None):
    """True si la lista ya viene en orden no decreciente. O(n), un solo recorrido."""
    i = 1
    n = len(lista)
    while i < n:
        if _valor(lista[i], clave) < _valor(lista[i - 1], clave):
            return False
        i += 1
    return True


def merge_sort(lista, clave=None):
    """Devuelve una lista NUEVA ordenada por clave(x) (o por x si clave es None).

    Merge sort de abajo hacia arriba: mezcla bloques de 1, luego de 2, de 4...
    sin recursión y sin rebanar la lista, usando dos arreglos que se alternan.
    Es estable: si dos elementos empatan, queda primero el que venía primero
    (esto lo necesitan el ranking y la fila).

    Si la lista ya viene ordenada se devuelve una copia en O(n); es lo normal
    con los CSV del GTFS. Si no, cuesta O(n log n) en cualquier caso.
    """
    n = len(lista)
    a = lista[:]
    if n < 2 or esta_ordenada(a, clave):
        return a
    # se calcula la clave una sola vez por elemento
    if clave is None:
        claves = a[:]
    else:
        claves = [None] * n
        for i in range(n):
            claves[i] = clave(a[i])
    b = [None] * n
    kb = [None] * n
    ancho = 1
    while ancho < n:
        inicio = 0
        while inicio < n:
            medio = inicio + ancho
            if medio > n:
                medio = n
            fin = inicio + 2 * ancho
            if fin > n:
                fin = n
            i = inicio
            j = medio
            k = inicio
            while i < medio and j < fin:
                if claves[j] < claves[i]:
                    b[k] = a[j]
                    kb[k] = claves[j]
                    j += 1
                else:
                    # empate: pasa primero el de la izquierda (estable)
                    b[k] = a[i]
                    kb[k] = claves[i]
                    i += 1
                k += 1
            while i < medio:
                b[k] = a[i]
                kb[k] = claves[i]
                i += 1
                k += 1
            while j < fin:
                b[k] = a[j]
                kb[k] = claves[j]
                j += 1
                k += 1
            inicio = fin
        a, b = b, a
        claves, kb = kb, claves
        ancho = ancho * 2
    return a


def primer_mayor_o_igual(lista, objetivo):
    """Búsqueda binaria sobre una lista ordenada.

    Devuelve la posición del primer elemento >= objetivo, o len(lista) si
    todos son menores. O(log n): cada paso descarta la mitad.
    """
    izquierda = 0
    derecha = len(lista)
    while izquierda < derecha:
        medio = (izquierda + derecha) // 2
        if lista[medio] < objetivo:
            izquierda = medio + 1
        else:
            derecha = medio
    return izquierda
