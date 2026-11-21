def simular_fila_pop0(llegadas, frecuencia, capacidad):
    total = len(llegadas)
    if capacidad < 1 or frecuencia < 1:
        return [None] * total
    orden = sorted(range(total), key=lambda i: llegadas[i])
    salidas = [None] * total
    fila = []
    siguiente = 0
    salida = frecuencia
    while siguiente < total or fila:
        if not fila:
            primera = llegadas[orden[siguiente]]
            if primera > salida:
                salida = ((primera + frecuencia - 1) // frecuencia) * frecuencia
        while siguiente < total and llegadas[orden[siguiente]] <= salida:
            fila.append(orden[siguiente])
            siguiente += 1
        subieron = 0
        while subieron < capacidad and fila:
            salidas[fila.pop(0)] = salida
            subieron += 1
        salida += frecuencia
    return salidas
