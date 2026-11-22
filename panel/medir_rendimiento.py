"""Panel de rendimiento y benchmark de operaciones (R11).

Mide cada operación del contrato con redes sintéticas de tamaño creciente
(10.000, 20.000, 40.000 y 80.000 estaciones), calcula la mediana de repeticiones
con time.perf_counter, obtiene la pendiente log-log (log(tiempo) vs log(n)),
compara contra la complejidad esperada y guarda los resultados para la app.
"""

import json
import math
import os
import random
import sys
import time

# Asegurar importación de motor y panel
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor import Red, simular_fila
from panel.fila_pop0 import simular_fila_pop0
from panel.generar_red import generar_red

TABLA_ESPERADA = {
    "Carga Red": {
        "responsable": "Juandi / Todos",
        "n_def": "N = Total de estaciones en la red",
        "o_grande": "O(N log N)",
        "pendiente_esperada": 1.0,
        "categoria": "Carga y Estructuras",
        "explicacion": "Lectura de archivos CSV e inserción en tablas hash O(N) y construcción de estructuras O(N log N). Pendiente cercana a 1.0.",
    },
    "estado (R1)": {
        "responsable": "Sebas",
        "n_def": "N = Total de estaciones",
        "o_grande": "O(1) / O(log N)",
        "pendiente_esperada": 0.0,
        "categoria": "Consultas",
        "explicacion": "Búsqueda directa por clave. En tabla hash O(1) y en ABB balanceado O(log N). Pendiente plana (~0).",
    },
    "autocompletar (R2)": {
        "responsable": "Sebas",
        "n_def": "N = Estaciones abiertas, k = cupo",
        "o_grande": "O(log N + k)",
        "pendiente_esperada": 0.1,
        "categoria": "Consultas",
        "explicacion": "Búsqueda del prefijo en árbol O(log N) y recorrido in-order acotado a k elementos. Crecimiento sublineal.",
    },
    "rango (R3)": {
        "responsable": "Sebas",
        "n_def": "N = Estaciones abiertas, m = elementos en rango",
        "o_grande": "O(log N + m)",
        "pendiente_esperada": 0.1,
        "categoria": "Consultas",
        "explicacion": "Búsqueda del límite inferior O(log N) y recorrido in-order hasta límite superior. Pendiente cercana a 0 para rangos pequeños.",
    },
    "proximo_bus (R4)": {
        "responsable": "Gabito",
        "n_def": "H = Horarios de la ruta en la estación",
        "o_grande": "O(log H) ≈ O(1) resp. a N",
        "pendiente_esperada": 0.0,
        "categoria": "Viajes y Horarios",
        "explicacion": "Consulta en tabla hash O(1) y búsqueda binaria sobre los horarios del día. No depende de N (estaciones de la ciudad).",
    },
    "ranking (R6)": {
        "responsable": "Gabito",
        "n_def": "k = cupo pedido, N = estaciones abiertas",
        "o_grande": "O(k log N) o O(k)",
        "pendiente_esperada": 0.0,
        "categoria": "Consultas",
        "explicacion": "Extracción de las k estaciones con más buses desde la estructura de ranking. Independiente o sublineal respecto a N.",
    },
    "agregar_parada (R7)": {
        "responsable": "Juandi",
        "n_def": "N = Total de estaciones",
        "o_grande": "O(1)",
        "pendiente_esperada": 0.0,
        "categoria": "Operación de Red",
        "explicacion": "Inserción en ListaDoble mediante nodo indexado en hash O(1). Pendiente plana (~0).",
    },
    "quitar_parada (R7)": {
        "responsable": "Juandi",
        "n_def": "N = Total de estaciones",
        "o_grande": "O(1)",
        "pendiente_esperada": 0.0,
        "categoria": "Operación de Red",
        "explicacion": "Desenlace de punteros en ListaDoble y eliminación de hash en O(1). Pendiente plana (~0).",
    },
    "recorrido (R7)": {
        "responsable": "Juandi",
        "n_def": "L = Cantidad de paradas en la ruta",
        "o_grande": "O(L) ≈ O(1) resp. a N",
        "pendiente_esperada": 0.0,
        "categoria": "Operación de Red",
        "explicacion": "Recorrido secuencial de la lista doblemente enlazada de la ruta. Como L está acotado, no depende de N.",
    },
    "cerrar (R8)": {
        "responsable": "Sebas",
        "n_def": "N = Total de estaciones",
        "o_grande": "O(log N) / O(1)",
        "pendiente_esperada": 0.1,
        "categoria": "Operación de Red",
        "explicacion": "Modificación de estado en O(1) y actualización en estructuras auxiliares O(log N). Pendiente plana (~0).",
    },
    "reabrir (R8)": {
        "responsable": "Sebas",
        "n_def": "N = Total de estaciones",
        "o_grande": "O(log N) / O(1)",
        "pendiente_esperada": 0.1,
        "categoria": "Operación de Red",
        "explicacion": "Reactivación de estación y reinserción en árbol/ranking en O(log N).",
    },
    "deshacer (R9)": {
        "responsable": "Juandi",
        "n_def": "N = Total de estaciones",
        "o_grande": "O(1) / O(log N)",
        "pendiente_esperada": 0.0,
        "categoria": "Historial",
        "explicacion": "Pop de la pila de deshacer en O(1) y ejecución de la acción inversa. Pendiente plana (~0).",
    },
    "rehacer (R9)": {
        "responsable": "Juandi",
        "n_def": "N = Total de estaciones",
        "o_grande": "O(1) / O(log N)",
        "pendiente_esperada": 0.0,
        "categoria": "Historial",
        "explicacion": "Pop de la pila de rehacer en O(1) y reaplicación de la acción. Pendiente plana (~0).",
    },
    "simular_fila (R10)": {
        "responsable": "Juandi",
        "n_def": "P = Cantidad de pasajeros",
        "o_grande": "O(P log P) o O(P)",
        "pendiente_esperada": 1.0,
        "categoria": "Simulación",
        "explicacion": "Uso de Cola FIFO basada en lista enlazada: enqueue y dequeue en O(1). Ordenamiento inicial O(P log P). Pendiente ~1.0.",
    },
    "simular_fila_pop0 (Extra)": {
        "responsable": "Juandi",
        "n_def": "P = Cantidad de pasajeros",
        "o_grande": "O(P^2)",
        "pendiente_esperada": 2.0,
        "categoria": "Simulación",
        "explicacion": "Uso de list.pop(0) prohibido: cada extracción desplaza todos los elementos O(P), totalizando O(P^2). Pendiente ~2.0.",
    },
}


def calcular_mediana(valores):
    """Calcula la mediana de una lista de números sin usar librerías externas."""
    if not valores:
        return 0.0
    arr = list(valores)
    arr.sort()
    m = len(arr) // 2
    if len(arr) % 2 == 1:
        return arr[m]
    return (arr[m - 1] + arr[m]) / 2.0


def calcular_pendiente_log_log(tamanos, tiempos):
    """Calcula la pendiente de regresión lineal en escala logarítmica: log(T) vs log(N).

    Pendiente = Cov(log N, log T) / Var(log N)
    0.0 -> O(1)
    1.0 -> O(N)
    2.0 -> O(N^2)
    """
    puntos = []
    for n, t in zip(tamanos, tiempos):
        if n > 0 and t > 0:
            puntos.append((math.log(n), math.log(t)))

    if len(puntos) < 2:
        return 0.0

    sum_x = sum(p[0] for p in puntos)
    sum_y = sum(p[1] for p in puntos)
    k = len(puntos)
    mean_x = sum_x / k
    mean_y = sum_y / k

    num = sum((p[0] - mean_x) * (p[1] - mean_y) for p in puntos)
    den = sum((p[0] - mean_x) ** 2 for p in puntos)

    if den == 0:
        return 0.0
    return round(num / den, 3)


def ejecutar_benchmarks(tamanos=(10000, 20000, 40000, 80000), repeticiones=3, carpeta_base="panel/redes_benchmark"):
    """Ejecuta las mediciones para cada tamaño y devuelve el resumen completo."""
    os.makedirs(carpeta_base, exist_ok=True)
    resultados = {
        "tamanos": list(tamanos),
        "repeticiones": repeticiones,
        "operaciones": {},
    }

    print(f"=== INICIANDO BENCHMARK PANEL DE RENDIMIENTO ===")
    print(f"Tamaños de red: {tamanos}")
    print(f"Repeticiones por operación: {repeticiones}")

    # Estructura para registrar tiempos por operación: op -> lista de medianas por cada tamaño
    tiempos_por_op = {op: [] for op in TABLA_ESPERADA.keys() if "simular_fila" not in op}

    for n in tamanos:
        carpeta_red = os.path.join(carpeta_base, f"red_{n}")
        if not os.path.exists(os.path.join(carpeta_red, "estaciones.csv")):
            print(f"Generando red sintética para n={n}...")
            generar_red(n, carpeta_red, orden="aleatorio", semilla=42)

        print(f"\n--- Probando con n={n} estaciones ---")

        # 1. Medir Carga Red
        tiempos_carga = []
        red_instancia = None
        for r in range(repeticiones):
            t0 = time.perf_counter()
            red_instancia = Red(carpeta_red)
            t1 = time.perf_counter()
            tiempos_carga.append(t1 - t0)
        tiempos_por_op["Carga Red"].append(calcular_mediana(tiempos_carga))

        # Estaciones de muestra para pruebas
        estaciones_claves = red_instancia.estaciones.claves()
        est_muestra = estaciones_claves[0] if estaciones_claves else "ESTACION 0001"
        est_otra = estaciones_claves[len(estaciones_claves) // 2] if estaciones_claves else "ESTACION 0002"

        rutas_claves = red_instancia.rutas.claves()
        ruta_muestra = rutas_claves[0] if rutas_claves else "R1-1"

        # 2. Medir estado (R1)
        tiempos_op = []
        for _ in range(repeticiones):
            t0 = time.perf_counter()
            red_instancia.estado(est_muestra)
            t1 = time.perf_counter()
            tiempos_op.append(t1 - t0)
        tiempos_por_op["estado (R1)"].append(calcular_mediana(tiempos_op))

        # 3. Medir autocompletar (R2)
        tiempos_op = []
        for _ in range(repeticiones):
            t0 = time.perf_counter()
            red_instancia.autocompletar("CALLE", 10)
            t1 = time.perf_counter()
            tiempos_op.append(t1 - t0)
        tiempos_por_op["autocompletar (R2)"].append(calcular_mediana(tiempos_op))

        # 4. Medir rango (R3)
        tiempos_op = []
        for _ in range(repeticiones):
            t0 = time.perf_counter()
            red_instancia.rango("CALLE 001", "CALLE 020")
            t1 = time.perf_counter()
            tiempos_op.append(t1 - t0)
        tiempos_por_op["rango (R3)"].append(calcular_mediana(tiempos_op))

        # 5. Medir proximo_bus (R4)
        tiempos_op = []
        for _ in range(repeticiones):
            t0 = time.perf_counter()
            red_instancia.proximo_bus(est_muestra, ruta_muestra, "10:00")
            t1 = time.perf_counter()
            tiempos_op.append(t1 - t0)
        tiempos_por_op["proximo_bus (R4)"].append(calcular_mediana(tiempos_op))

        # 6. Medir ranking (R6)
        tiempos_op = []
        for _ in range(repeticiones):
            t0 = time.perf_counter()
            red_instancia.ranking(10)
            t1 = time.perf_counter()
            tiempos_op.append(t1 - t0)
        tiempos_por_op["ranking (R6)"].append(calcular_mediana(tiempos_op))

        # 7. Medir recorrido (R7)
        tiempos_op = []
        for _ in range(repeticiones):
            t0 = time.perf_counter()
            red_instancia.recorrido(ruta_muestra)
            t1 = time.perf_counter()
            tiempos_op.append(t1 - t0)
        tiempos_por_op["recorrido (R7)"].append(calcular_mediana(tiempos_op))

        # 8. Medir agregar_parada (R7)
        tiempos_op = []
        for rep in range(repeticiones):
            nom_nueva = f"TEST_ADD_{n}_{rep}"
            # Asegurar que la estación exista en red.estaciones
            red_instancia._cargar_estaciones_extra = getattr(red_instancia, "_cargar_estaciones_extra", None)
            from motor.red import Estacion
            red_instancia.estaciones.set(nom_nueva, Estacion(nom_nueva))
            red_instancia.rutas_por_estacion.set(nom_nueva, [])
            rec = red_instancia.recorrido(ruta_muestra)
            despues_de = rec[0] if rec else est_muestra
            t0 = time.perf_counter()
            red_instancia.agregar_parada(ruta_muestra, nom_nueva, despues_de)
            t1 = time.perf_counter()
            tiempos_op.append(t1 - t0)
        tiempos_por_op["agregar_parada (R7)"].append(calcular_mediana(tiempos_op))

        # 9. Medir quitar_parada (R7)
        tiempos_op = []
        for rep in range(repeticiones):
            rec = red_instancia.recorrido(ruta_muestra)
            est_a_quitar = rec[-1] if len(rec) > 2 else est_muestra
            t0 = time.perf_counter()
            red_instancia.quitar_parada(ruta_muestra, est_a_quitar)
            t1 = time.perf_counter()
            tiempos_op.append(t1 - t0)
        tiempos_por_op["quitar_parada (R7)"].append(calcular_mediana(tiempos_op))

        # 10. Medir deshacer (R9)
        tiempos_op = []
        for _ in range(repeticiones):
            t0 = time.perf_counter()
            red_instancia.deshacer()
            t1 = time.perf_counter()
            tiempos_op.append(t1 - t0)
        tiempos_por_op["deshacer (R9)"].append(calcular_mediana(tiempos_op))

        # 11. Medir rehacer (R9)
        tiempos_op = []
        for _ in range(repeticiones):
            t0 = time.perf_counter()
            red_instancia.rehacer()
            t1 = time.perf_counter()
            tiempos_op.append(t1 - t0)
        tiempos_por_op["rehacer (R9)"].append(calcular_mediana(tiempos_op))

        # 12. Medir cerrar (R8)
        tiempos_op = []
        for _ in range(repeticiones):
            t0 = time.perf_counter()
            red_instancia.cerrar(est_otra)
            t1 = time.perf_counter()
            tiempos_op.append(t1 - t0)
        tiempos_por_op["cerrar (R8)"].append(calcular_mediana(tiempos_op))

        # 13. Medir reabrir (R8)
        tiempos_op = []
        for _ in range(repeticiones):
            t0 = time.perf_counter()
            red_instancia.reabrir(est_otra)
            t1 = time.perf_counter()
            tiempos_op.append(t1 - t0)
        tiempos_por_op["reabrir (R8)"].append(calcular_mediana(tiempos_op))

    # 14. Medir simular_fila vs simular_fila_pop0 (R10)
    print("\n--- Midiendo simulación de fila (Cola vs pop(0)) ---")
    tamanos_fila = (1000, 2000, 4000, 8000)
    tiempos_fila_cola = []
    tiempos_fila_pop0 = []

    for p in tamanos_fila:
        random.seed(42)
        llegadas = [random.randint(0, 3600) for _ in range(p)]
        # Medir simular_fila (Cola)
        t_cola_reps = []
        for _ in range(repeticiones):
            t0 = time.perf_counter()
            simular_fila(llegadas, 60, 50)
            t1 = time.perf_counter()
            t_cola_reps.append(t1 - t0)
        tiempos_fila_cola.append(calcular_mediana(t_cola_reps))

        # Medir simular_fila_pop0
        t_pop0_reps = []
        for _ in range(repeticiones):
            t0 = time.perf_counter()
            simular_fila_pop0(llegadas, 60, 50)
            t1 = time.perf_counter()
            t_pop0_reps.append(t1 - t0)
        tiempos_fila_pop0.append(calcular_mediana(t_pop0_reps))

    # Consolidar resultados
    for op, data_meta in TABLA_ESPERADA.items():
        if op == "simular_fila (R10)":
            t_medidos = tiempos_fila_cola
            ns = list(tamanos_fila)
        elif op == "simular_fila_pop0 (Extra)":
            t_medidos = tiempos_fila_pop0
            ns = list(tamanos_fila)
        else:
            t_medidos = tiempos_por_op.get(op, [0.0] * len(tamanos))
            ns = list(tamanos)

        pendiente_calc = calcular_pendiente_log_log(ns, t_medidos)
        resultados["operaciones"][op] = {
            "responsable": data_meta["responsable"],
            "n_def": data_meta["n_def"],
            "o_grande": data_meta["o_grande"],
            "pendiente_esperada": data_meta["pendiente_esperada"],
            "pendiente_medida": pendiente_calc,
            "tamanos_n": ns,
            "tiempos_segundos": [round(t, 6) for t in t_medidos],
            "categoria": data_meta["categoria"],
            "explicacion": data_meta["explicacion"],
        }

    # Guardar en JSON para la app
    ruta_json = os.path.join("panel", "resultados_rendimiento.json")
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"\nResultados guardados exitosamente en: {ruta_json}")
    imprimir_tabla_resumen(resultados)
    return resultados


def imprimir_tabla_resumen(resultados):
    """Imprime una tabla limpia en consola con las pendientes y complejidades."""
    print("\n" + "=" * 90)
    print(f"{'Operación':<26} | {'Responsable':<12} | {'O Grande':<15} | {'Esp.':<5} | {'Med.':<5} | {'Estado':<10}")
    print("-" * 90)
    for op, datos in resultados["operaciones"].items():
        esp = datos["pendiente_esperada"]
        med = datos["pendiente_medida"]
        # Tolerancia razonable para ruido
        ok = abs(esp - med) <= 0.4 or (esp == 0.0 and med <= 0.3)
        estado = "OK" if ok else "DESVÍO"
        print(f"{op:<26} | {datos['responsable']:<12} | {datos['o_grande']:<15} | {esp:<5.1f} | {med:<5.1f} | {estado:<10}")
    print("=" * 90 + "\n")


def cargar_o_ejecutar_resultados(forzar_ejecucion=False):
    """Carga los resultados cacheados o ejecuta una corrida si no existen."""
    ruta_json = os.path.join("panel", "resultados_rendimiento.json")
    if os.path.exists(ruta_json) and not forzar_ejecucion:
        try:
            with open(ruta_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Corrida rápida por defecto para inicializar
    return ejecutar_benchmarks(tamanos=(1000, 2000, 4000, 8000), repeticiones=2)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Medición de rendimiento de operaciones TransMilenio")
    parser.add_argument("--rapido", action="store_true", help="Usa tamaños reducidos para prueba rápida")
    parser.add_argument("--completo", action="store_true", help="Usa tamaños oficiales: 10k, 20k, 40k, 80k")
    args = parser.parse_args()

    if args.completo:
        ejecutar_benchmarks(tamanos=(10000, 20000, 40000, 80000), repeticiones=3)
    elif args.rapido:
        ejecutar_benchmarks(tamanos=(500, 1000, 2000, 4000), repeticiones=2)
    else:
        # Por defecto tamaños estándar representativos
        ejecutar_benchmarks(tamanos=(1000, 2000, 4000, 8000), repeticiones=2)
