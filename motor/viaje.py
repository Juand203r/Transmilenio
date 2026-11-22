"""Planificación de viajes en la red de TransMilenio (R5).

Encuentra el viaje con menor número de paradas entre dos estaciones,
sea directo (1 tramo) o con un solo transbordo (2 tramos).
Cumple estrictamente con las reglas del motor:
- Sin dict ni set (usa TablaHash)
- Sin sorted, min, max sobre colecciones
- Sin x in lista ni librerías externas
"""

from .tabla_hash import TablaHash


def planear_viaje(red, origen, destino):
    """Devuelve una lista de tramos (ruta, sube_en, baja_en) con el viaje de menos paradas.

    1 tramo si es directo, 2 si hay un solo transbordo; None si no hay viaje.
    Reglas:
    - Nadie sube, baja ni transborda en una estación cerrada.
    - Las estaciones cerradas por donde pasa la ruta sí cuentan como paradas recorridas.
    - Si origen == destino, o alguno es inexistente o cerrado: devuelve None.
    - Ante un empate en paradas entre viaje directo y transbordo, se prefiere el directo.

    Args:
        red (Red): Instancia de la red.
        origen (str): Nombre de la estación de origen.
        destino (str): Nombre de la estación de destino.

    Returns:
        list of tuple or None: Lista de tramos [(ruta, sube, baja), ...] o None.
    """
    # 1. Validaciones iniciales
    if origen is None or destino is None or origen == destino:
        return None

    est_origen = red.estaciones.get(origen)
    est_destino = red.estaciones.get(destino)

    if est_origen is None or est_destino is None:
        return None

    if not est_origen.abierta or not est_destino.abierta:
        return None

    rutas_origen = red.rutas_por_estacion.get(origen)
    rutas_destino = red.rutas_por_estacion.get(destino)

    if rutas_origen is None or rutas_destino is None:
        return None

    if len(rutas_origen) == 0 or len(rutas_destino) == 0:
        return None

    # 2. Fase hacia atrás desde el destino
    # Guardamos en una TablaHash: estacion_transferencia -> lista de (ruta_destino, paradas_hasta_destino)
    dest_opciones = TablaHash()

    for idx_rd in range(len(rutas_destino)):
        r_dest = rutas_destino[idx_rd]
        lista_dest = red.rutas.get(r_dest)
        if lista_dest is None:
            continue

        nodo_dest = lista_dest.nodo(destino)
        if nodo_dest is None:
            continue

        paradas_hacia_atras = 0
        actual = nodo_dest.anterior
        while actual is not None:
            paradas_hacia_atras += 1
            nombre_parada = actual.nombre

            # Solo consideramos estaciones abiertas para transbordar (y distintas de origen)
            obj_est = red.estaciones.get(nombre_parada)
            if obj_est is not None and obj_est.abierta and nombre_parada != origen:
                candidatos = dest_opciones.get(nombre_parada)
                if candidatos is None:
                    candidatos = [(r_dest, paradas_hacia_atras)]
                    dest_opciones.set(nombre_parada, candidatos)
                else:
                    # Guardamos la opción si aporta menor o igual distancia con otra ruta
                    candidatos.append((r_dest, paradas_hacia_atras))

            actual = actual.anterior

    # 3. Fase hacia adelante desde el origen
    # Exploramos cada ruta que pasa por origen
    mejor_directo = None
    mejor_directo_paradas = None

    mejor_transbordo = None
    mejor_transbordo_paradas = None

    for idx_ro in range(len(rutas_origen)):
        r_orig = rutas_origen[idx_ro]
        lista_orig = red.rutas.get(r_orig)
        if lista_orig is None:
            continue

        nodo_orig = lista_orig.nodo(origen)
        if nodo_orig is None:
            continue

        paradas_hacia_adelante = 0
        actual = nodo_orig.siguiente
        while actual is not None:
            paradas_hacia_adelante += 1
            nombre_parada = actual.nombre

            # Caso A: Llegamos directo al destino
            if nombre_parada == destino:
                if mejor_directo is None or paradas_hacia_adelante < mejor_directo_paradas:
                    mejor_directo = [(r_orig, origen, destino)]
                    mejor_directo_paradas = paradas_hacia_adelante

            # Caso B: Estación intermedia abierta para transbordo
            else:
                obj_est = red.estaciones.get(nombre_parada)
                if obj_est is not None and obj_est.abierta:
                    opciones_transbordo = dest_opciones.get(nombre_parada)
                    if opciones_transbordo is not None:
                        for idx_opc in range(len(opciones_transbordo)):
                            r_dest, paradas_dest = opciones_transbordo[idx_opc]
                            # El transbordo debe ser a una ruta distinta
                            if r_dest != r_orig:
                                total_paradas = paradas_hacia_adelante + paradas_dest
                                if mejor_transbordo is None or total_paradas < mejor_transbordo_paradas:
                                    mejor_transbordo = [
                                        (r_orig, origen, nombre_parada),
                                        (r_dest, nombre_parada, destino),
                                    ]
                                    mejor_transbordo_paradas = total_paradas

            actual = actual.siguiente

    # 4. Decisión final: desempate y selección
    # Decisión 8: ante empate en número de paradas, se prefiere el viaje directo
    if mejor_directo is not None and mejor_transbordo is not None:
        if mejor_directo_paradas <= mejor_transbordo_paradas:
            return mejor_directo
        return mejor_transbordo

    if mejor_directo is not None:
        return mejor_directo

    if mejor_transbordo is not None:
        return mejor_transbordo

    return None
