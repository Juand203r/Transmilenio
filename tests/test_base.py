import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from motor import Red, simular_fila
from motor.red import Estacion
from motor.tabla_hash import TablaHash


class ClaveColisionada:
    def __init__(self, nombre):
        self.nombre = nombre

    def __hash__(self):
        return 7

    def __eq__(self, otra):
        return isinstance(otra, ClaveColisionada) and self.nombre == otra.nombre


class TestTablaHash(unittest.TestCase):
    def test_get_clave_inexistente(self):
        t = TablaHash()
        self.assertIsNone(t.get("A"))
        t.set("A", 1)
        self.assertIsNone(t.get("B"))

    def test_set_y_get(self):
        t = TablaHash()
        t.set("A", 1)
        t.set("B", 2)
        self.assertEqual(t.get("A"), 1)
        self.assertEqual(t.get("B"), 2)
        self.assertEqual(len(t), 2)

    def test_set_reemplaza_sin_aumentar_len(self):
        t = TablaHash()
        t.set("A", 1)
        t.set("A", 9)
        self.assertEqual(t.get("A"), 9)
        self.assertEqual(len(t), 1)

    def test_contiene(self):
        t = TablaHash()
        t.set("A", 1)
        self.assertTrue(t.contiene("A"))
        self.assertFalse(t.contiene("B"))

    def test_contiene_con_valor_none(self):
        t = TablaHash()
        t.set("A", None)
        self.assertTrue(t.contiene("A"))
        self.assertIsNone(t.get("A"))

    def test_colisiones_forzadas(self):
        t = TablaHash()
        claves = [ClaveColisionada(str(i)) for i in range(50)]
        for i, c in enumerate(claves):
            t.set(c, i)
        self.assertEqual(len(t), 50)
        for i, c in enumerate(claves):
            self.assertEqual(t.get(c), i)
        self.assertIsNone(t.get(ClaveColisionada("no")))

    def test_delete_en_colisiones_cabeza_medio_cola(self):
        t = TablaHash(capacidad=1024)
        a, b, c, d = [ClaveColisionada(x) for x in "abcd"]
        for i, x in enumerate([a, b, c, d]):
            t.set(x, i)
        self.assertTrue(t.delete(d))
        self.assertTrue(t.delete(b))
        self.assertTrue(t.delete(a))
        self.assertFalse(t.contiene(a))
        self.assertFalse(t.contiene(b))
        self.assertFalse(t.contiene(d))
        self.assertEqual(t.get(c), 2)
        self.assertEqual(len(t), 1)

    def test_delete_inexistente_y_repetido(self):
        t = TablaHash()
        self.assertFalse(t.delete("A"))
        t.set("A", 1)
        self.assertTrue(t.delete("A"))
        self.assertFalse(t.delete("A"))
        self.assertEqual(len(t), 0)
        self.assertIsNone(t.get("A"))

    def test_redimension_conserva_todo(self):
        t = TablaHash()
        tamano_inicial = t.tamano
        for i in range(5000):
            t.set("K" + str(i), i)
        self.assertGreater(t.tamano, tamano_inicial)
        self.assertEqual(len(t), 5000)
        for i in range(5000):
            self.assertEqual(t.get("K" + str(i)), i)

    def test_factor_de_carga_nunca_supera_el_maximo(self):
        t = TablaHash()
        for i in range(2000):
            t.set("K" + str(i), i)
            self.assertLessEqual(len(t) * 4, t.tamano * 3)

    def test_tamano_se_duplica(self):
        t = TablaHash(capacidad=16)
        for i in range(13):
            t.set(str(i), i)
        self.assertEqual(t.tamano, 32)

    def test_claves_y_valores(self):
        t = TablaHash()
        for i in range(100):
            t.set("K" + str(i), i)
        t.delete("K5")
        self.assertEqual(len(t.claves()), 99)
        self.assertEqual(len(t.valores()), 99)
        self.assertEqual(sorted(t.claves()), sorted("K" + str(i) for i in range(100) if i != 5))
        self.assertEqual(sorted(t.valores()), [i for i in range(100) if i != 5])

    def test_tabla_vacia(self):
        t = TablaHash()
        self.assertEqual(t.claves(), [])
        self.assertEqual(t.valores(), [])
        self.assertEqual(len(t), 0)

    def test_capacidad_invalida(self):
        t = TablaHash(capacidad=0)
        t.set("A", 1)
        self.assertEqual(t.get("A"), 1)

    def test_contra_dict_con_operaciones_aleatorias(self):
        import random
        random.seed(3)
        t = TablaHash()
        d = {}
        for _ in range(20000):
            k = str(random.randint(0, 800))
            op = random.random()
            if op < 0.5:
                v = random.randint(0, 9)
                t.set(k, v)
                d[k] = v
            elif op < 0.8:
                self.assertEqual(t.get(k), d.get(k))
                self.assertEqual(t.contiene(k), k in d)
            else:
                self.assertEqual(t.delete(k), k in d)
                d.pop(k, None)
            self.assertEqual(len(t), len(d))
        self.assertEqual(sorted(t.claves()), sorted(d))


class TestCargaEstaciones(unittest.TestCase):
    def _red(self, nombres, fin_linea="\n"):
        carpeta = tempfile.mkdtemp()
        with open(os.path.join(carpeta, "estaciones.csv"), "w", newline="", encoding="utf-8") as f:
            f.write("nombre" + fin_linea + fin_linea.join(nombres) + fin_linea)
        with open(os.path.join(carpeta, "rutas.csv"), "w", newline="", encoding="utf-8") as f:
            f.write("ruta,orden,estacion\n")
        with open(os.path.join(carpeta, "horarios.csv"), "w", newline="", encoding="utf-8") as f:
            f.write("ruta,estacion,hora\n")
        return Red(carpeta), carpeta

    def test_carga_estaciones_abiertas_con_cero_buses(self):
        red, _ = self._red(["AGUAS", "CALLE 26", "PORTAL NORTE"])
        self.assertEqual(len(red.estaciones), 3)
        for nombre in ["AGUAS", "CALLE 26", "PORTAL NORTE"]:
            e = red.estaciones.get(nombre)
            self.assertIsInstance(e, Estacion)
            self.assertEqual(e.nombre, nombre)
            self.assertTrue(e.abierta)
            self.assertEqual(e.buses_dia, 0)

    def test_estacion_inexistente(self):
        red, _ = self._red(["AGUAS"])
        self.assertIsNone(red.estaciones.get("NO EXISTE"))

    def test_fin_de_linea_windows(self):
        red, _ = self._red(["AGUAS", "CALLE 26"], fin_linea="\r\n")
        self.assertEqual(len(red.estaciones), 2)
        self.assertIsNotNone(red.estaciones.get("CALLE 26"))

    def test_solo_encabezado(self):
        red, _ = self._red([])
        self.assertEqual(len(red.estaciones), 0)

    def test_carpeta_con_separador_al_final(self):
        _, carpeta = self._red(["AGUAS"])
        red = Red(carpeta + os.sep)
        self.assertEqual(len(red.estaciones), 1)

    def test_carga_grande(self):
        nombres = ["E" + str(i).zfill(6) for i in range(80000)]
        red, _ = self._red(nombres)
        self.assertEqual(len(red.estaciones), 80000)
        self.assertIsNotNone(red.estaciones.get("E079999"))

    def test_atributos_compartidos(self):
        red, _ = self._red(["AGUAS"])
        self.assertIsInstance(red.rutas, TablaHash)
        self.assertIsInstance(red.horarios, TablaHash)
        self.assertIsInstance(red.rutas_por_estacion, TablaHash)

    def test_importacion_del_contrato(self):
        self.assertTrue(callable(Red))
        self.assertTrue(callable(simular_fila))


if __name__ == "__main__":
    unittest.main()
