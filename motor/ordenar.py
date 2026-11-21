def merge_sort(lista, clave=None):
    """STUB de Gabito (no subir): devuelve una lista nueva ordenada, estable."""
    n = len(lista)
    if n <= 1:
        return lista[:]
    medio = n // 2
    izquierda = merge_sort(lista[:medio], clave)
    derecha = merge_sort(lista[medio:], clave)
    resultado = []
    i = 0
    j = 0
    while i < len(izquierda) and j < len(derecha):
        a = izquierda[i]
        b = derecha[j]
        if clave is None:
            va = a
            vb = b
        else:
            va = clave(a)
            vb = clave(b)
        if vb < va:
            resultado.append(b)
            j += 1
        else:
            resultado.append(a)
            i += 1
    while i < len(izquierda):
        resultado.append(izquierda[i])
        i += 1
    while j < len(derecha):
        resultado.append(derecha[j])
        j += 1
    return resultado
