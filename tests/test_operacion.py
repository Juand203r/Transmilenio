import csv
import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time

from motor import Red, simular_fila
from motor.cola import Cola
from motor.historial import AccionCerrar, AccionReabrir
from motor.lista_doble import ListaDoble
from motor.pila import Pila


def escribir(carpeta, archivo, encabezado, filas):
    with open(os.path.join(carpeta, archivo), "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(encabezado)
        for fila in filas:
            escritor.writerow(fila)


class RedConGancho(Red):
    def __init__(self, carpeta):
        self.llamadas = []
        super().__init__(carpeta)

    def _ranking_actualizar(self, nombre):
        self.llamadas.append(nombre)


def armar_red(estaciones, rutas, clase=RedConGancho):
    carpeta = tempfile.mkdtemp()
    escribir(carpeta, "estaciones.csv", ["nombre"], [[e] for e in estaciones])
    escribir(carpeta, "rutas.csv", ["ruta", "orden", "estacion"], rutas)
    escribir(carpeta, "horarios.csv", ["ruta", "estacion", "hora"], [])
    return clase(carpeta)


ESTACIONES = ["A", "B", "C", "D", "E", "F", "G", "H"]
RUTAS = [
    ["R1", 1, "A"],
    ["R2", 1, "C"],
    ["R1", 2, "B"],
    ["R1", 3, "C"],
    ["R3", 2, "G"],
    ["R2", 2, "E"],
    ["R1", 4, "D"],
    ["R3", 1, "D"],
    ["R2", 3, "F"],
]


def red_base():
    red = armar_red(ESTACIONES, RUTAS)
    red.horarios.set("R1|B", [480, 500, 520])
    red.horarios.set("R1|D", [490, 510])
    red.estaciones.get("B").buses_dia = 3
    red.estaciones.get("D").buses_dia = 2
    return red


class TestListaDoble(unittest.TestCase):
    def test_vacia(self):
        lista = ListaDoble()
        self.assertEqual(lista.nombres(), [])
        self.assertEqual(lista.nombres(True), [])
        self.assertEqual(len(lista), 0)
        self.assertIsNone(lista.cabeza)
        self.assertIsNone(lista.cola)

    def test_agregar_al_final(self):
        lista = ListaDoble()
        for n in ["A", "B", "C"]:
            self.assertTrue(lista.agregar_al_final(n))
        self.assertEqual(lista.nombres(), ["A", "B", "C"])
        self.assertEqual(lista.nombres(True), ["C", "B", "A"])
        self.assertEqual(len(lista), 3)
        self.assertFalse(lista.agregar_al_final("B"))
        self.assertEqual(len(lista), 3)

    def test_insertar_al_inicio(self):
        lista = ListaDoble()
        self.assertTrue(lista.insertar_al_inicio("B"))
        self.assertEqual(lista.cabeza.nombre, "B")
        self.assertEqual(lista.cola.nombre, "B")
        self.assertTrue(lista.insertar_al_inicio("A"))
        self.assertEqual(lista.nombres(), ["A", "B"])
        self.assertEqual(lista.nombres(True), ["B", "A"])
        self.assertFalse(lista.insertar_al_inicio("A"))

    def test_insertar_despues_en_medio_y_cola(self):
        lista = ListaDoble()
        lista.agregar_al_final("A")
        lista.agregar_al_final("C")
        self.assertTrue(lista.insertar_despues("A", "B"))
        self.assertEqual(lista.nombres(), ["A", "B", "C"])
        self.assertEqual(lista.nombres(True), ["C", "B", "A"])
        self.assertTrue(lista.insertar_despues("C", "D"))
        self.assertEqual(lista.cola.nombre, "D")
        self.assertEqual(lista.nombres(True), ["D", "C", "B", "A"])

    def test_insertar_despues_casos_invalidos(self):
        lista = ListaDoble()
        lista.agregar_al_final("A")
        self.assertFalse(lista.insertar_despues("Z", "B"))
        self.assertFalse(lista.insertar_despues("A", "A"))
        lista.agregar_al_final("B")
        self.assertFalse(lista.insertar_despues("A", "B"))
        self.assertEqual(lista.nombres(), ["A", "B"])

    def test_quitar_cabeza_medio_cola_y_unico(self):
        lista = ListaDoble()
        for n in ["A", "B", "C", "D"]:
            lista.agregar_al_final(n)
        self.assertTrue(lista.quitar("B"))
        self.assertEqual(lista.nombres(), ["A", "C", "D"])
        self.assertEqual(lista.nombres(True), ["D", "C", "A"])
        self.assertTrue(lista.quitar("A"))
        self.assertEqual(lista.cabeza.nombre, "C")
        self.assertIsNone(lista.cabeza.anterior)
        self.assertTrue(lista.quitar("D"))
        self.assertEqual(lista.cola.nombre, "C")
        self.assertIsNone(lista.cola.siguiente)
        self.assertTrue(lista.quitar("C"))
        self.assertIsNone(lista.cabeza)
        self.assertIsNone(lista.cola)
        self.assertEqual(len(lista), 0)
        self.assertFalse(lista.quitar("C"))

    def test_nodo_y_contiene(self):
        lista = ListaDoble()
        lista.agregar_al_final("A")
        lista.agregar_al_final("B")
        self.assertEqual(lista.nodo("B").anterior.nombre, "A")
        self.assertEqual(lista.nodo("A").siguiente.nombre, "B")
        self.assertIsNone(lista.nodo("Z"))
        self.assertTrue(lista.contiene("A"))
        lista.quitar("A")
        self.assertFalse(lista.contiene("A"))

    def test_contra_modelo_con_operaciones_aleatorias(self):
        random.seed(5)
        lista = ListaDoble()
        modelo = []
        for _ in range(5000):
            n = "N" + str(random.randint(0, 60))
            op = random.randint(0, 3)
            if op == 0:
                esperado = n not in modelo
                self.assertEqual(lista.agregar_al_final(n), esperado)
                if esperado:
                    modelo.append(n)
            elif op == 1:
                esperado = n not in modelo
                self.assertEqual(lista.insertar_al_inicio(n), esperado)
                if esperado:
                    modelo.insert(0, n)
            elif op == 2 and modelo:
                ref = modelo[random.randint(0, len(modelo) - 1)]
                esperado = n not in modelo
                self.assertEqual(lista.insertar_despues(ref, n), esperado)
                if esperado:
                    modelo.insert(modelo.index(ref) + 1, n)
            else:
                esperado = n in modelo
                self.assertEqual(lista.quitar(n), esperado)
                if esperado:
                    modelo.remove(n)
            self.assertEqual(lista.nombres(), modelo)
            self.assertEqual(lista.nombres(True), modelo[::-1])
            self.assertEqual(len(lista), len(modelo))


class TestCargaRutas(unittest.TestCase):
    def test_recorridos_ordenados_aunque_el_archivo_venga_mezclado(self):
        red = armar_red(ESTACIONES, RUTAS)
        self.assertEqual(red.recorrido("R1"), ["A", "B", "C", "D"])
        self.assertEqual(red.recorrido("R2"), ["C", "E", "F"])
        self.assertEqual(red.recorrido("R3"), ["D", "G"])

    def test_recorrido_al_reves(self):
        red = armar_red(ESTACIONES, RUTAS)
        self.assertEqual(red.recorrido("R1", al_reves=True), ["D", "C", "B", "A"])
        self.assertEqual(red.recorrido("R3", True), ["G", "D"])

    def test_orden_numerico_y_no_de_texto(self):
        filas = [["R", 10, "J"], ["R", 2, "B"], ["R", 1, "A"], ["R", 12, "L"], ["R", 3, "C"], ["R", 11, "K"]]
        red = armar_red(["A", "B", "C", "J", "K", "L"], filas)
        self.assertEqual(red.recorrido("R"), ["A", "B", "C", "J", "K", "L"])

    def test_ruta_inexistente(self):
        red = armar_red(ESTACIONES, RUTAS)
        self.assertEqual(red.recorrido("NO"), [])
        self.assertEqual(red.recorrido("NO", True), [])

    def test_rutas_por_estacion(self):
        red = armar_red(ESTACIONES, RUTAS)
        esperado = {"A": ["R1"], "B": ["R1"], "C": ["R1", "R2"], "D": ["R1", "R3"],
                    "E": ["R2"], "F": ["R2"], "G": ["R3"], "H": []}
        for estacion in esperado:
            self.assertEqual(sorted(red.rutas_por_estacion.get(estacion)), esperado[estacion])

    def test_estacion_repetida_o_desconocida_se_ignora(self):
        filas = [["R1", 1, "A"], ["R1", 2, "A"], ["R1", 3, "ZZZ"], ["R1", 4, "B"]]
        red = armar_red(["A", "B"], filas)
        self.assertEqual(red.recorrido("R1"), ["A", "B"])
        self.assertEqual(red.rutas_por_estacion.get("A"), ["R1"])

    def test_sin_filas_de_rutas(self):
        red = armar_red(["A", "B"], [])
        self.assertEqual(len(red.rutas), 0)
        self.assertEqual(red.rutas_por_estacion.get("A"), [])

    def test_carga_grande(self):
        n = 20000
        estaciones = ["E" + str(i).zfill(6) for i in range(n)]
        filas = []
        for j in range(3000):
            for t in range(20):
                filas.append(["R" + str(j), t + 1, estaciones[(j * 20 + t * 37) % n]])
        random.seed(2)
        random.shuffle(filas)
        red = armar_red(estaciones, filas)
        self.assertEqual(len(red.rutas), 3000)
        self.assertEqual(len(red.recorrido("R7")), 20)
        self.assertEqual(red.recorrido("R7")[0], estaciones[140 % n])


class TestAgregarParada(unittest.TestCase):
    def test_agrega_en_medio(self):
        red = red_base()
        self.assertTrue(red.agregar_parada("R1", "E", "B"))
        self.assertEqual(red.recorrido("R1"), ["A", "B", "E", "C", "D"])
        self.assertEqual(red.recorrido("R1", True), ["D", "C", "E", "B", "A"])

    def test_agrega_despues_de_la_ultima(self):
        red = red_base()
        self.assertTrue(red.agregar_parada("R1", "H", "D"))
        self.assertEqual(red.recorrido("R1"), ["A", "B", "C", "D", "H"])
        self.assertEqual(red.recorrido("R1", True), ["H", "D", "C", "B", "A"])

    def test_casos_que_devuelven_false_y_no_cambian_nada(self):
        red = red_base()
        antes = red.recorrido("R1")
        self.assertFalse(red.agregar_parada("NO", "E", "B"))
        self.assertFalse(red.agregar_parada("R1", "NO", "B"))
        self.assertFalse(red.agregar_parada("R1", "C", "B"))
        self.assertFalse(red.agregar_parada("R1", "E", "NO"))
        self.assertFalse(red.agregar_parada("R1", "E", "H"))
        self.assertFalse(red.agregar_parada("R1", "B", "B"))
        self.assertEqual(red.recorrido("R1"), antes)
        self.assertEqual(red.llamadas, [])
        self.assertEqual(red.rutas_por_estacion.get("E"), ["R2"])

    def test_copia_horarios_y_suma_buses_dia(self):
        red = red_base()
        red.estaciones.get("E").buses_dia = 1
        red.agregar_parada("R1", "E", "B")
        self.assertEqual(red.horarios.get("R1|E"), [480, 500, 520])
        self.assertIsNot(red.horarios.get("R1|E"), red.horarios.get("R1|B"))
        red.horarios.get("R1|E").append(999)
        self.assertEqual(red.horarios.get("R1|B"), [480, 500, 520])
        self.assertEqual(red.estaciones.get("E").buses_dia, 3 + 1)

    def test_actualiza_rutas_por_estacion_y_llama_al_gancho(self):
        red = red_base()
        red.agregar_parada("R1", "E", "B")
        self.assertEqual(sorted(red.rutas_por_estacion.get("E")), ["R1", "R2"])
        self.assertEqual(red.llamadas, ["E"])

    def test_despues_de_sin_horarios_no_llama_al_gancho(self):
        red = red_base()
        self.assertTrue(red.agregar_parada("R1", "E", "A"))
        self.assertIsNone(red.horarios.get("R1|E"))
        self.assertEqual(red.estaciones.get("E").buses_dia, 0)
        self.assertEqual(red.llamadas, [])

    def test_estacion_cerrada_se_puede_agregar_y_usar_como_referencia(self):
        red = red_base()
        red.estaciones.get("E").abierta = False
        red.estaciones.get("B").abierta = False
        self.assertTrue(red.agregar_parada("R1", "E", "B"))
        self.assertEqual(red.recorrido("R1"), ["A", "B", "E", "C", "D"])

    def test_agregar_a_ruta_vacia_devuelve_false(self):
        red = red_base()
        for n in ["D", "G"]:
            red.quitar_parada("R3", n)
        self.assertFalse(red.agregar_parada("R3", "A", "D"))
        self.assertEqual(red.recorrido("R3"), [])


class TestQuitarParada(unittest.TestCase):
    def test_quita_en_medio_cabeza_y_cola(self):
        red = red_base()
        self.assertTrue(red.quitar_parada("R1", "B"))
        self.assertEqual(red.recorrido("R1"), ["A", "C", "D"])
        self.assertTrue(red.quitar_parada("R1", "A"))
        self.assertEqual(red.recorrido("R1"), ["C", "D"])
        self.assertTrue(red.quitar_parada("R1", "D"))
        self.assertEqual(red.recorrido("R1"), ["C"])
        self.assertEqual(red.recorrido("R1", True), ["C"])

    def test_ruta_que_queda_con_una_sola_parada_y_luego_vacia(self):
        red = red_base()
        self.assertTrue(red.quitar_parada("R3", "G"))
        self.assertEqual(red.recorrido("R3"), ["D"])
        self.assertTrue(red.quitar_parada("R3", "D"))
        self.assertEqual(red.recorrido("R3"), [])
        self.assertEqual(red.recorrido("R3", True), [])

    def test_casos_que_devuelven_false(self):
        red = red_base()
        self.assertFalse(red.quitar_parada("NO", "A"))
        self.assertFalse(red.quitar_parada("R1", "NO"))
        self.assertFalse(red.quitar_parada("R1", "E"))
        self.assertTrue(red.quitar_parada("R1", "A"))
        self.assertFalse(red.quitar_parada("R1", "A"))
        self.assertEqual(red.llamadas, [])

    def test_borra_horarios_resta_buses_dia_y_llama_al_gancho(self):
        red = red_base()
        red.quitar_parada("R1", "B")
        self.assertIsNone(red.horarios.get("R1|B"))
        self.assertEqual(red.estaciones.get("B").buses_dia, 0)
        self.assertEqual(red.llamadas, ["B"])

    def test_actualiza_rutas_por_estacion_sin_tocar_otras_rutas(self):
        red = red_base()
        red.quitar_parada("R1", "D")
        self.assertEqual(red.rutas_por_estacion.get("D"), ["R3"])
        red.quitar_parada("R3", "D")
        self.assertEqual(red.rutas_por_estacion.get("D"), [])
        self.assertEqual(sorted(red.rutas_por_estacion.get("C")), ["R1", "R2"])

    def test_estacion_cerrada_se_puede_quitar(self):
        red = red_base()
        red.estaciones.get("B").abierta = False
        self.assertTrue(red.quitar_parada("R1", "B"))
        self.assertEqual(red.recorrido("R1"), ["A", "C", "D"])

    def test_quitar_y_volver_a_agregar(self):
        red = red_base()
        red.quitar_parada("R1", "C")
        self.assertTrue(red.agregar_parada("R1", "C", "B"))
        self.assertEqual(red.recorrido("R1"), ["A", "B", "C", "D"])
        self.assertEqual(sorted(red.rutas_por_estacion.get("C")), ["R1", "R2"])

    def test_la_recorrida_hacia_atras_sigue_consistente_tras_muchos_cambios(self):
        random.seed(9)
        red = armar_red(["S" + str(i) for i in range(30)], [["R", i + 1, "S" + str(i)] for i in range(10)])
        modelo = ["S" + str(i) for i in range(10)]
        for _ in range(2000):
            e = "S" + str(random.randint(0, 29))
            if random.random() < 0.5 and modelo:
                ref = modelo[random.randint(0, len(modelo) - 1)]
                esperado = e not in modelo
                self.assertEqual(red.agregar_parada("R", e, ref), esperado)
                if esperado:
                    modelo.insert(modelo.index(ref) + 1, e)
            else:
                esperado = e in modelo
                self.assertEqual(red.quitar_parada("R", e), esperado)
                if esperado:
                    modelo.remove(e)
            self.assertEqual(red.recorrido("R"), modelo)
            self.assertEqual(red.recorrido("R", True), modelo[::-1])


class RedConCierre(RedConGancho):
    def _cerrar(self, nombre):
        estacion = self.estaciones.get(nombre)
        if estacion is None or not estacion.abierta:
            return False
        estacion.abierta = False
        return True

    def _reabrir(self, nombre):
        estacion = self.estaciones.get(nombre)
        if estacion is None or estacion.abierta:
            return False
        estacion.abierta = True
        return True

    def cerrar(self, nombre):
        return self._ejecutar(AccionCerrar(self, nombre))

    def reabrir(self, nombre):
        return self._ejecutar(AccionReabrir(self, nombre))


def foto(red):
    rutas = []
    for ruta in sorted(red.rutas.claves()):
        rutas.append((ruta, tuple(red.recorrido(ruta)), tuple(red.recorrido(ruta, True))))
    estaciones = []
    for nombre in sorted(red.estaciones.claves()):
        e = red.estaciones.get(nombre)
        estaciones.append((nombre, e.abierta, e.buses_dia, tuple(sorted(red.rutas_por_estacion.get(nombre)))))
    horarios = []
    for clave in sorted(red.horarios.claves()):
        horarios.append((clave, tuple(red.horarios.get(clave))))
    return (tuple(rutas), tuple(estaciones), tuple(horarios))


def red_con_horarios(semilla, clase=RedConCierre):
    random.seed(semilla)
    estaciones = ["S" + str(i) for i in range(12)]
    filas = []
    for r in range(4):
        indices = list(range(12))
        random.shuffle(indices)
        for orden in range(5):
            filas.append(["R" + str(r), orden + 1, estaciones[indices[orden]]])
    red = armar_red(estaciones, filas, clase)
    for ruta in red.rutas.claves():
        for nombre in red.recorrido(ruta):
            horas = [random.randint(300, 1400) for _ in range(random.randint(1, 5))]
            red.horarios.set(ruta + "|" + nombre, horas)
            red.estaciones.get(nombre).buses_dia += len(horas)
    return red


def buses_consistentes(red):
    for nombre in red.estaciones.claves():
        total = 0
        for ruta in red.rutas_por_estacion.get(nombre):
            total += len(red.horarios.get(ruta + "|" + nombre))
        if red.estaciones.get(nombre).buses_dia != total:
            return False
    return True


class TestPila(unittest.TestCase):
    def test_vacia(self):
        pila = Pila()
        self.assertTrue(pila.esta_vacia())
        self.assertIsNone(pila.pop())
        self.assertIsNone(pila.peek())
        self.assertEqual(len(pila), 0)

    def test_lifo(self):
        pila = Pila()
        for x in [1, 2, 3]:
            pila.push(x)
        self.assertEqual(pila.peek(), 3)
        self.assertEqual(len(pila), 3)
        self.assertEqual([pila.pop(), pila.pop(), pila.pop()], [3, 2, 1])
        self.assertTrue(pila.esta_vacia())
        self.assertIsNone(pila.pop())

    def test_peek_no_quita(self):
        pila = Pila()
        pila.push("A")
        pila.peek()
        self.assertEqual(len(pila), 1)


class TestDeshacerRehacer(unittest.TestCase):
    def test_sin_historia(self):
        red = red_base()
        self.assertFalse(red.deshacer())
        self.assertFalse(red.rehacer())

    def test_deshacer_y_rehacer_agregar(self):
        red = red_con_horarios(1)
        inicial = foto(red)
        ruta = "R0"
        nombres = red.recorrido(ruta)
        libre = None
        for i in range(12):
            if "S" + str(i) not in nombres:
                libre = "S" + str(i)
        self.assertTrue(red.agregar_parada(ruta, libre, nombres[1]))
        despues = foto(red)
        self.assertNotEqual(inicial, despues)
        self.assertTrue(red.deshacer())
        self.assertEqual(foto(red), inicial)
        self.assertTrue(red.rehacer())
        self.assertEqual(foto(red), despues)
        self.assertFalse(red.rehacer())

    def test_deshacer_quitar_en_cabeza_medio_cola_y_unica(self):
        for posicion in [0, 2, 4]:
            red = red_con_horarios(2)
            inicial = foto(red)
            nombre = red.recorrido("R1")[posicion]
            self.assertTrue(red.quitar_parada("R1", nombre))
            self.assertTrue(red.deshacer())
            self.assertEqual(foto(red), inicial)
            self.assertTrue(buses_consistentes(red))
        red = red_con_horarios(3)
        for nombre in red.recorrido("R2"):
            red.quitar_parada("R2", nombre)
        self.assertEqual(red.recorrido("R2"), [])
        for _ in range(5):
            self.assertTrue(red.deshacer())
        self.assertEqual(foto(red), foto(red_con_horarios(3)))

    def test_rehacer_quitar(self):
        red = red_con_horarios(4)
        nombre = red.recorrido("R0")[0]
        red.quitar_parada("R0", nombre)
        quitada = foto(red)
        red.deshacer()
        self.assertTrue(red.rehacer())
        self.assertEqual(foto(red), quitada)

    def test_accion_fallida_no_apila(self):
        red = red_base()
        self.assertFalse(red.agregar_parada("NO", "E", "B"))
        self.assertFalse(red.quitar_parada("R1", "E"))
        self.assertFalse(red.deshacer())

    def test_accion_fallida_no_borra_lo_que_habia_para_rehacer(self):
        red = red_base()
        red.agregar_parada("R1", "E", "B")
        red.deshacer()
        self.assertFalse(red.agregar_parada("NO", "E", "B"))
        self.assertTrue(red.rehacer())
        self.assertEqual(red.recorrido("R1"), ["A", "B", "E", "C", "D"])

    def test_cambio_nuevo_borra_lo_que_habia_para_rehacer(self):
        red = red_base()
        red.agregar_parada("R1", "E", "B")
        red.deshacer()
        red.quitar_parada("R1", "A")
        self.assertFalse(red.rehacer())

    def test_cerrar_y_reabrir(self):
        red = armar_red(ESTACIONES, RUTAS, RedConCierre)
        self.assertTrue(red.cerrar("A"))
        self.assertFalse(red.estaciones.get("A").abierta)
        self.assertFalse(red.cerrar("A"))
        self.assertTrue(red.deshacer())
        self.assertTrue(red.estaciones.get("A").abierta)
        self.assertFalse(red.deshacer())
        self.assertTrue(red.rehacer())
        self.assertFalse(red.estaciones.get("A").abierta)
        self.assertTrue(red.reabrir("A"))
        self.assertTrue(red.deshacer())
        self.assertFalse(red.estaciones.get("A").abierta)

    def test_cadena_mezclada_en_orden_correcto(self):
        red = red_con_horarios(6)
        f0 = foto(red)
        red.cerrar("S3")
        f1 = foto(red)
        nombres = red.recorrido("R0")
        red.quitar_parada("R0", nombres[2])
        f2 = foto(red)
        libre = "S0" if "S0" not in red.recorrido("R1") else "S1"
        if libre in red.recorrido("R1"):
            libre = "S11"
        agregada = red.agregar_parada("R1", libre, red.recorrido("R1")[0])
        f3 = foto(red)
        pasos = [f0, f1, f2, f3] if agregada else [f0, f1, f2]
        for i in range(len(pasos) - 1, 0, -1):
            self.assertTrue(red.deshacer())
            self.assertEqual(foto(red), pasos[i - 1])
        self.assertFalse(red.deshacer())
        for i in range(1, len(pasos)):
            self.assertTrue(red.rehacer())
            self.assertEqual(foto(red), pasos[i])
        self.assertFalse(red.rehacer())

    def test_historia_larga_contra_modelo(self):
        for semilla in range(5):
            red = red_con_horarios(10 + semilla)
            random.seed(100 + semilla)
            historia = [foto(red)]
            posicion = 0
            for _ in range(400):
                op = random.randint(0, 5)
                ruta = "R" + str(random.randint(0, 4))
                est = "S" + str(random.randint(0, 12))
                ref = "S" + str(random.randint(0, 12))
                if op == 0:
                    cambio = red.agregar_parada(ruta, est, ref)
                elif op == 1:
                    cambio = red.quitar_parada(ruta, est)
                elif op == 2:
                    cambio = red.cerrar(est)
                elif op == 3:
                    cambio = red.reabrir(est)
                elif op == 4:
                    hay = posicion > 0
                    self.assertEqual(red.deshacer(), hay)
                    if hay:
                        posicion -= 1
                    cambio = None
                else:
                    hay = posicion < len(historia) - 1
                    self.assertEqual(red.rehacer(), hay)
                    if hay:
                        posicion += 1
                    cambio = None
                if cambio:
                    historia = historia[:posicion + 1]
                    historia.append(foto(red))
                    posicion += 1
                self.assertEqual(foto(red), historia[posicion])
                self.assertTrue(buses_consistentes(red))
            while red.deshacer():
                pass
            self.assertEqual(foto(red), historia[0])
            while red.rehacer():
                pass
            self.assertEqual(foto(red), historia[len(historia) - 1])

    def test_miles_de_acciones(self):
        red = armar_red(["S" + str(i) for i in range(50)], [["R", i + 1, "S" + str(i)] for i in range(50)])
        for i in range(50):
            red.horarios.set("R|S" + str(i), [i])
        inicial = foto(red)
        for _ in range(100):
            for i in range(49):
                red.quitar_parada("R", "S" + str(i + 1))
                red.agregar_parada("R", "S" + str(i + 1), "S" + str(i))
        contador = 0
        while red.deshacer():
            contador += 1
        self.assertEqual(contador, 9800)
        self.assertEqual(foto(red), inicial)


def fila_ingenua(llegadas, frecuencia, capacidad):
    n = len(llegadas)
    resultado = [None] * n
    pendientes = sorted(range(n), key=lambda i: (llegadas[i], i))
    salida = frecuencia
    while pendientes:
        suben = []
        quedan = []
        for i in pendientes:
            if llegadas[i] <= salida and len(suben) < capacidad:
                suben.append(i)
            else:
                quedan.append(i)
        for i in suben:
            resultado[i] = salida
        pendientes = quedan
        salida += frecuencia
    return resultado


class TestCola(unittest.TestCase):
    def test_vacia(self):
        cola = Cola()
        self.assertTrue(cola.esta_vacia())
        self.assertIsNone(cola.dequeue())
        self.assertEqual(len(cola), 0)

    def test_fifo(self):
        cola = Cola()
        for x in [1, 2, 3]:
            cola.enqueue(x)
        self.assertEqual(len(cola), 3)
        self.assertEqual([cola.dequeue(), cola.dequeue(), cola.dequeue()], [1, 2, 3])
        self.assertTrue(cola.esta_vacia())
        self.assertIsNone(cola.dequeue())

    def test_se_puede_reusar_despues_de_vaciarse(self):
        cola = Cola()
        cola.enqueue("A")
        cola.dequeue()
        cola.enqueue("B")
        cola.enqueue("C")
        self.assertEqual(cola.dequeue(), "B")
        self.assertEqual(cola.dequeue(), "C")
        self.assertTrue(cola.esta_vacia())

    def test_intercalando_enqueue_y_dequeue(self):
        cola = Cola()
        esperado = []
        random.seed(4)
        for i in range(3000):
            if random.random() < 0.55:
                cola.enqueue(i)
                esperado.append(i)
            elif esperado:
                self.assertEqual(cola.dequeue(), esperado.pop(0))
            self.assertEqual(len(cola), len(esperado))


class TestSimularFila(unittest.TestCase):
    def test_ejemplo_del_enunciado(self):
        self.assertEqual(simular_fila([30, 5, 5, 70], 60, 2), [120, 60, 60, 120])

    def test_lista_vacia(self):
        self.assertEqual(simular_fila([], 60, 2), [])

    def test_un_solo_pasajero(self):
        self.assertEqual(simular_fila([5], 60, 3), [60])
        self.assertEqual(simular_fila([0], 60, 3), [60])
        self.assertEqual(simular_fila([60], 60, 3), [60])
        self.assertEqual(simular_fila([61], 60, 3), [120])

    def test_capacidad_uno(self):
        self.assertEqual(simular_fila([1, 1, 1, 1], 10, 1), [10, 20, 30, 40])

    def test_mismo_segundo_respeta_el_orden_original(self):
        self.assertEqual(simular_fila([7, 7, 7], 10, 2), [10, 10, 20])

    def test_llegadas_desordenadas(self):
        self.assertEqual(simular_fila([100, 1, 50, 2], 30, 1), [120, 30, 90, 60])

    def test_fila_que_espera_varios_buses(self):
        self.assertEqual(simular_fila([1, 1, 1, 1, 1], 10, 2), [10, 10, 20, 20, 30])

    def test_llegada_exacta_en_multiplo_de_frecuencia(self):
        self.assertEqual(simular_fila([60, 120, 121], 60, 5), [60, 120, 180])

    def test_salto_de_buses_vacios(self):
        self.assertEqual(simular_fila([10 ** 9], 1, 1), [10 ** 9])
        a = 10 ** 9 + 1
        self.assertEqual(simular_fila([a, 5], 60, 1), [-(-a // 60) * 60, 60])

    def test_capacidad_o_frecuencia_invalida(self):
        self.assertEqual(simular_fila([1, 2, 3], 60, 0), [None, None, None])
        self.assertEqual(simular_fila([1, 2, 3], 0, 2), [None, None, None])
        self.assertEqual(simular_fila([], 0, 0), [])

    def test_no_modifica_la_entrada(self):
        llegadas = [30, 5, 5, 70]
        simular_fila(llegadas, 60, 2)
        self.assertEqual(llegadas, [30, 5, 5, 70])

    def test_ordenadas_y_desordenadas_dan_lo_mismo(self):
        random.seed(8)
        llegadas = [random.randint(0, 300) for _ in range(500)]
        orden = sorted(range(500), key=lambda i: (llegadas[i], i))
        ordenadas = [llegadas[i] for i in orden]
        respuesta_ordenada = simular_fila(ordenadas, 17, 6)
        respuesta = simular_fila(llegadas, 17, 6)
        for posicion in range(500):
            self.assertEqual(respuesta[orden[posicion]], respuesta_ordenada[posicion])

    def test_contra_simulacion_ingenua(self):
        random.seed(12)
        for _ in range(400):
            n = random.randint(0, 40)
            tope = random.choice([0, 5, 60, 300])
            llegadas = [random.randint(0, tope) for _ in range(n)]
            frecuencia = random.randint(1, 25)
            capacidad = random.randint(1, 6)
            self.assertEqual(simular_fila(llegadas, frecuencia, capacidad),
                             fila_ingenua(llegadas, frecuencia, capacidad))

    def test_cientos_de_miles_de_pasajeros(self):
        random.seed(21)
        total = 300000
        llegadas = [random.randint(0, 3600) for _ in range(total)]
        frecuencia = 30
        capacidad = 200
        inicio = time.perf_counter()
        salidas = simular_fila(llegadas, frecuencia, capacidad)
        self.assertLess(time.perf_counter() - inicio, 20)
        orden = sorted(range(total), key=lambda i: (llegadas[i], i))
        por_bus = 0
        bus_anterior = 0
        for i in orden:
            self.assertEqual(salidas[i] % frecuencia, 0)
            self.assertGreaterEqual(salidas[i], llegadas[i])
            self.assertGreaterEqual(salidas[i], bus_anterior)
            if salidas[i] == bus_anterior:
                por_bus += 1
            else:
                por_bus = 1
                bus_anterior = salidas[i]
            self.assertLessEqual(por_bus, capacidad)


if __name__ == "__main__":
    unittest.main()
