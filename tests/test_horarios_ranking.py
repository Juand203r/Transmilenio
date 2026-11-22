"""Pruebas de R4 (proximo_bus), R6 (ranking), carga de horarios y ordenar.py.

Fuera de motor/ sí se puede usar sorted, dict, etc. para comparar contra
una versión de fuerza bruta.
"""
import csv
import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from motor import Red
from motor.ordenar import merge_sort, primer_mayor_o_igual
from motor.ranking import Ranking

DATOS = os.path.join(os.path.dirname(__file__), "..", "datos")


def escribir(carpeta, nombre, encabezado, filas):
    with open(os.path.join(carpeta, nombre), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(encabezado)
        w.writerows(filas)


def red_chiquita():
    carpeta = tempfile.mkdtemp()
    escribir(carpeta, "estaciones.csv", ["nombre"], [[x] for x in ["A", "B", "C", "D", "E"]])
    escribir(carpeta, "rutas.csv", ["ruta", "orden", "estacion"], [
        ["R1", 1, "A"], ["R1", 2, "B"], ["R1", 3, "C"],
        ["R2", 2, "D"], ["R2", 1, "C"],          # desordenada a proposito
    ])
    escribir(carpeta, "horarios.csv", ["ruta", "estacion", "hora"], [
        ["R1", "A", "06:10"], ["R1", "A", "06:00"], ["R1", "A", "07:30"],   # desordenadas
        ["R1", "B", "06:05"], ["R1", "C", "06:20"],
        ["R2", "C", "08:00"], ["R2", "C", "25:10"],                          # hora tipo GTFS > 24
        ["R2", "D", "08:05"],
        ["R9", "E", "09:00"],                                                # ruta que no existe
    ])
    return Red(carpeta)


class TestOrdenar(unittest.TestCase):
    def test_merge_sort_contra_sorted(self):
        rnd = random.Random(1)
        for _ in range(300):
            lista = [rnd.randint(-50, 50) for _ in range(rnd.randint(0, 120))]
            self.assertEqual(merge_sort(lista), sorted(lista))

    def test_merge_sort_no_modifica_la_entrada(self):
        lista = [3, 1, 2]
        merge_sort(lista)
        self.assertEqual(lista, [3, 1, 2])

    def test_merge_sort_estable_con_clave(self):
        pares = [(2, "a"), (1, "b"), (2, "c"), (1, "d"), (0, "e")]
        self.assertEqual(merge_sort(pares, lambda p: p[0]),
                         [(0, "e"), (1, "b"), (1, "d"), (2, "a"), (2, "c")])

    def test_binaria(self):
        lista = [1, 3, 3, 3, 8]
        self.assertEqual(primer_mayor_o_igual(lista, 0), 0)
        self.assertEqual(primer_mayor_o_igual(lista, 3), 1)    # primer igual
        self.assertEqual(primer_mayor_o_igual(lista, 4), 4)
        self.assertEqual(primer_mayor_o_igual(lista, 9), 5)    # ninguno: len
        self.assertEqual(primer_mayor_o_igual([], 5), 0)


class TestR4ProximoBus(unittest.TestCase):
    def setUp(self):
        self.red = red_chiquita()

    def test_horarios_cargados_en_minutos_y_ordenados(self):
        self.assertEqual(self.red.horarios.get("R1|A"), [360, 370, 450])
        self.assertEqual(self.red.horarios.get("R2|C"), [480, 1510])

    def test_casos_normales_y_hora_exacta(self):
        self.assertEqual(self.red.proximo_bus("A", "R1", "05:00"), "06:00")
        self.assertEqual(self.red.proximo_bus("A", "R1", "06:00"), "06:00")   # la exacta cuenta
        self.assertEqual(self.red.proximo_bus("A", "R1", "06:01"), "06:10")
        self.assertIsNone(self.red.proximo_bus("A", "R1", "07:31"))          # no hay mas ese dia

    def test_horas_despues_de_medianoche(self):
        self.assertEqual(self.red.proximo_bus("C", "R2", "23:00"), "25:10")

    def test_casos_borde(self):
        self.assertIsNone(self.red.proximo_bus("NO EXISTE", "R1", "06:00"))
        self.assertIsNone(self.red.proximo_bus("A", "NO EXISTE", "06:00"))
        self.assertIsNone(self.red.proximo_bus("D", "R1", "06:00"))          # R1 no para en D
        self.assertIsNone(self.red.proximo_bus("A", "R1", "hora mala"))
        self.red.estaciones.get("A").abierta = False                         # cerrada: nadie sube
        self.assertIsNone(self.red.proximo_bus("A", "R1", "06:00"))

    def test_quitar_parada_y_deshacer(self):
        self.assertTrue(self.red.quitar_parada("R1", "B"))
        self.assertIsNone(self.red.proximo_bus("B", "R1", "06:00"))
        self.assertTrue(self.red.deshacer())
        self.assertEqual(self.red.proximo_bus("B", "R1", "06:00"), "06:05")


class TestR6Ranking(unittest.TestCase):
    def setUp(self):
        self.red = red_chiquita()

    def test_buses_dia_solo_de_rutas_que_paran(self):
        cuenta = [(n, self.red.estaciones.get(n).buses_dia) for n in "ABCDE"]
        self.assertEqual(cuenta, [("A", 3), ("B", 1), ("C", 3), ("D", 1), ("E", 0)])

    def test_orden_y_empates_alfabeticos(self):
        self.assertEqual(self.red.ranking(5), [("A", 3), ("C", 3), ("B", 1), ("D", 1), ("E", 0)])
        self.assertEqual(self.red.ranking(2), [("A", 3), ("C", 3)])
        self.assertEqual(self.red.ranking(0), [])
        self.assertEqual(len(self.red.ranking(100)), 5)
        self.assertIsInstance(self.red.ranking(1)[0], tuple)

    def test_ganchos_de_cerrar_y_reabrir(self):
        # lo que hacen cerrar/reabrir (R8) con el ranking
        self.red.estaciones.get("A").abierta = False
        self.red._ranking_quitar("A")
        self.assertEqual(self.red.ranking(2), [("C", 3), ("B", 1)])
        self.red.estaciones.get("A").abierta = True
        self.red._ranking_poner("A")
        self.assertEqual(self.red.ranking(2), [("A", 3), ("C", 3)])

    def test_editar_rutas_actualiza_el_ranking(self):
        self.assertTrue(self.red.quitar_parada("R1", "A"))                  # A pierde sus 3 buses
        self.assertIn(("A", 0), self.red.ranking(5))
        self.assertTrue(self.red.deshacer())
        self.assertEqual(self.red.ranking(1), [("A", 3)])
        self.assertTrue(self.red.agregar_parada("R2", "E", "C"))           # E hereda los 2 de C en R2
        self.assertEqual(dict(self.red.ranking(5))["E"], 2)

    def test_avl_contra_fuerza_bruta(self):
        rnd = random.Random(7)
        r = Ranking()
        real = {}
        for _ in range(4000):
            nombre = "E" + str(rnd.randint(0, 150))
            accion = rnd.random()
            if accion < 0.4:
                buses = rnd.randint(0, 30)
                self.assertEqual(r.poner(nombre, buses), nombre not in real)
                real.setdefault(nombre, buses)
            elif accion < 0.7:
                self.assertEqual(r.quitar(nombre), nombre in real)
                real.pop(nombre, None)
            elif nombre in real:
                real[nombre] = rnd.randint(0, 30)
                r.actualizar(nombre, real[nombre])
            esperado = sorted(real.items(), key=lambda x: (-x[1], x[0]))[:10]
            self.assertEqual(r.primeros(10), esperado)
        self.assertEqual(len(r), len(real))


class TestRedReal(unittest.TestCase):
    def test_ranking_y_proximo_bus_contra_fuerza_bruta(self):
        red = Red(DATOS)
        horarios = {}
        rutas = {}
        with open(os.path.join(DATOS, "rutas.csv"), encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                rutas.setdefault(fila["ruta"], set()).add(fila["estacion"])
        with open(os.path.join(DATOS, "horarios.csv"), encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                h, m = fila["hora"].split(":")
                horarios.setdefault((fila["ruta"], fila["estacion"]), []).append(int(h) * 60 + int(m))
        cuenta = {}
        for (ruta, est), horas in horarios.items():
            if est in rutas.get(ruta, ()):
                cuenta[est] = cuenta.get(est, 0) + len(horas)
        nombres = red.estaciones.claves()
        esperado = sorted(((n, cuenta.get(n, 0)) for n in nombres), key=lambda x: (-x[1], x[0]))
        self.assertEqual(red.ranking(20), esperado[:20])
        rnd = random.Random(3)
        claves = list(horarios)
        for _ in range(500):
            ruta, est = rnd.choice(claves)
            hora = "%02d:%02d" % (rnd.randrange(24), rnd.randrange(60))
            objetivo = int(hora[:2]) * 60 + int(hora[3:])
            futuras = sorted(x for x in horarios[(ruta, est)] if x >= objetivo)
            esperado_bus = None if not futuras else "%02d:%02d" % (futuras[0] // 60, futuras[0] % 60)
            self.assertEqual(red.proximo_bus(est, ruta, hora), esperado_bus)


if __name__ == "__main__":
    unittest.main()
