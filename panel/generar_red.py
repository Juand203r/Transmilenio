"""Generador de redes sintéticas para pruebas de escalabilidad y rendimiento (R11).

Genera carpetas con estaciones.csv, rutas.csv y horarios.csv en el mismo
formato que la red real de TransMilenio, asegurando que el número de rutas
por estación y paradas por ruta se mantengan acotados (O(1) local) para que
la red crezca proporcionalmente en número de estaciones N.
"""

import argparse
import csv
import os
import random


def generar_red(n, carpeta, orden="aleatorio", semilla=42, salidas_por_dia=8, paradas_por_ruta=20):
    """Genera una red sintética con n estaciones y la guarda en la carpeta especificada.

    Args:
        n (int): Cantidad total de estaciones.
        carpeta (str): Ruta de la carpeta donde se guardarán los tres CSVs.
        orden (str): 'alfabetico' o 'aleatorio' para el orden de estaciones.csv.
        semilla (int): Semilla para generación reproducible.
        salidas_por_dia (int): Cantidad de horarios por día por cada parada.
        paradas_por_ruta (int): Longitud aproximada de cada ruta.

    Returns:
        dict: Estadísticas de la red generada (estaciones, rutas, filas_rutas, filas_horarios).
    """
    random.seed(semilla)
    os.makedirs(carpeta, exist_ok=True)

    # 1. Generar nombres de estaciones
    # Usamos prefijos variados para que autocompletar y rango tengan variedad
    prefijos = ["AVENIDA", "CALLE", "CRA", "PORTAL", "ESTACION", "TRANSVERSAL", "DIAGONAL", "PARQUE"]
    estaciones = []
    ancho = len(str(n)) + 1
    for i in range(1, n + 1):
        pref = prefijos[i % len(prefijos)]
        num_str = str(i).zfill(ancho)
        nombre = f"{pref} {num_str}"
        estaciones.append(nombre)

    # Orden para estaciones.csv
    estaciones_archivo = list(estaciones)
    if orden == "alfabetico":
        estaciones_archivo.sort()
    elif orden == "aleatorio":
        random.shuffle(estaciones_archivo)

    # Guardar estaciones.csv
    ruta_estaciones = os.path.join(carpeta, "estaciones.csv")
    with open(ruta_estaciones, mode="w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["nombre"])
        for est in estaciones_archivo:
            escritor.writerow([est])

    # 2. Generar rutas
    # Para que cada estación tenga entre 2 y 4 rutas y las paradas por ruta sean ~paradas_por_ruta,
    # armamos rutas conectando estaciones consecutivas y rutas transversales.
    rutas = {}
    filas_rutas = []

    # Corredores principales continuos
    tam_ruta = max(5, paradas_por_ruta)
    id_ruta = 1
    paso = max(1, tam_ruta // 2)

    for inicio in range(0, n, paso):
        fin = min(inicio + tam_ruta, n)
        if fin - inicio >= 3:
            nombre_ruta = f"R{id_ruta}-1"
            secuencia = [estaciones[idx] for idx in range(inicio, fin)]
            rutas[nombre_ruta] = secuencia
            for orden_idx, est in enumerate(secuencia, start=1):
                filas_rutas.append((nombre_ruta, orden_idx, est))
            id_ruta += 1

            # Sentido inverso (ruta de regreso)
            nombre_regreso = f"R{id_ruta}-2"
            secuencia_regreso = list(reversed(secuencia))
            rutas[nombre_regreso] = secuencia_regreso
            for orden_idx, est in enumerate(secuencia_regreso, start=1):
                filas_rutas.append((nombre_regreso, orden_idx, est))
            id_ruta += 1

    # Agregar algunas rutas expresas que salten de 2 en 2 o 3 en 3 para interconectar
    salto = 3
    for inicio in range(0, min(n, 1000), tam_ruta):
        indices = list(range(inicio, min(inicio + tam_ruta * salto, n), salto))
        if len(indices) >= 4:
            nombre_expreso = f"E{id_ruta}"
            secuencia_exp = [estaciones[idx] for idx in indices]
            rutas[nombre_expreso] = secuencia_exp
            for orden_idx, est in enumerate(secuencia_exp, start=1):
                filas_rutas.append((nombre_expreso, orden_idx, est))
            id_ruta += 1

    # Guardar rutas.csv
    ruta_rutas = os.path.join(carpeta, "rutas.csv")
    with open(ruta_rutas, mode="w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["ruta", "orden", "estacion"])
        for r, o, e in filas_rutas:
            escritor.writerow([r, o, e])

    # 3. Generar horarios
    # Cada ruta tiene salidas_por_dia despachos distribuidos entre las 05:00 y las 22:00
    # Cada parada incrementa el tiempo en 2 o 3 minutos
    filas_horarios = []
    minuto_inicio_dia = 5 * 60  # 05:00
    intervalo = max(10, (17 * 60) // max(1, salidas_por_dia))

    for nom_ruta, parada_lista in rutas.items():
        for d in range(salidas_por_dia):
            hora_salida_base = minuto_inicio_dia + d * intervalo
            # Para cada parada en la ruta
            for p_idx, est in enumerate(parada_lista):
                minutos_parada = hora_salida_base + p_idx * 3
                hh = (minutos_parada // 60) % 24
                mm = minutos_parada % 60
                hora_str = f"{hh:02d}:{mm:02d}"
                filas_horarios.append((nom_ruta, est, hora_str))

    # Guardar horarios.csv
    ruta_horarios = os.path.join(carpeta, "horarios.csv")
    with open(ruta_horarios, mode="w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["ruta", "estacion", "hora"])
        for r, e, h in filas_horarios:
            escritor.writerow([r, e, h])

    stats = {
        "n": n,
        "carpeta": carpeta,
        "estaciones": len(estaciones),
        "rutas": len(rutas),
        "filas_rutas": len(filas_rutas),
        "filas_horarios": len(filas_horarios),
    }
    return stats


def main():
    parser = argparse.ArgumentParser(description="Generador de redes sintéticas para TransMilenio")
    parser.add_argument("--n", type=int, default=10000, help="Número de estaciones a generar")
    parser.add_argument("--carpeta", type=str, default="", help="Carpeta de destino")
    parser.add_argument("--orden", choices=["alfabetico", "aleatorio"], default="aleatorio",
                        help="Orden de estaciones en estaciones.csv")
    parser.add_argument("--semilla", type=int, default=42, help="Semilla aleatoria")
    parser.add_argument("--salidas", type=int, default=8, help="Horarios por parada al día")
    args = parser.parse_args()

    carpeta = args.carpeta
    if not carpeta:
        carpeta = os.path.join("panel", f"red_{args.n}")

    print(f"Generando red sintética de {args.n} estaciones en '{carpeta}' (orden={args.orden})...")
    stats = generar_red(args.n, carpeta, orden=args.orden, semilla=args.semilla, salidas_por_dia=args.salidas)
    print(f"Completado exitosamente:")
    print(f" - Estaciones: {stats['estaciones']}")
    print(f" - Rutas únicas: {stats['rutas']}")
    print(f" - Filas rutas.csv: {stats['filas_rutas']}")
    print(f" - Filas horarios.csv: {stats['filas_horarios']}")


if __name__ == "__main__":
    main()
