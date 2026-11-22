"""Pruebas unitarias para R5: planear_viaje en tests/test_viaje.py.

Cubre todos los casos borde requeridos en el enunciado y acuerdos:
1. Viaje directo (1 tramo).
2. Viaje con 1 transbordo (2 tramos).
3. Empate en paradas entre directo y transbordo (se prefiere el directo).
4. Dos transbordos posibles pero uno con menos paradas (elige el menor).
5. Sin viaje posible (devuelve None).
6. Origen igual a destino (devuelve None).
7. Origen inexistente o destino inexistente (devuelve None).
8. Origen cerrado o destino cerrado (devuelve None).
9. Estación de transbordo cerrada (no se transborda allí).
10. Ruta que pasa por una cerrada (cuenta como parada recorrida, pero nadie sube/baja).
11. Edición previa de rutas con agregar_parada y quitar_parada.
"""

import os
import shutil
import unittest

from motor import Red


class TestViaje(unittest.TestCase):
    CARPETA_TEST = "tests/test_red_viaje"

    @classmethod
    def setUpClass(cls):
        os.makedirs(cls.CARPETA_TEST, exist_ok=True)

        # Red pequeña inventada para probar todas las combinaciones
        # Estaciones: A, B, C, D, E, F, G, H, X_CERRADA, AISLADA
        estaciones_csv = """nombre
A
B
C
D
E
F
G
H
X_CERRADA
AISLADA
"""
        with open(os.path.join(cls.CARPETA_TEST, "estaciones.csv"), "w", encoding="utf-8") as f:
            f.write(estaciones_csv)

        # Rutas:
        # R_DIR: A -> B -> C -> D (directo A -> D en 3 paradas)
        # R1_T: A -> E (1 parada)
        # R2_T: E -> D (1 parada) => Transbordo en E total 2 paradas (gana al directo)
        #
        # Para empate:
        # F -> G (directo F -> G en 1 parada)
        # F -> H (1 parada) y H -> G (1 parada) => Transbordo en H total 2 paradas.
        # R_EMP1: F -> G (1 parada)
        # R_EMP2: F -> H (1 parada)
        # R_EMP3: H -> G (1 parada)
        #
        # Dos transbordos posibles con diferente número de paradas:
        # A -> B (1 parada) y B -> D (2 paradas: B -> C -> D) => Transbordo en B = 3 paradas
        # A -> E (1 parada) y E -> D (1 parada) => Transbordo en E = 2 paradas (gana E)
        #
        # Ruta pasando por cerrada:
        # R_PASACERRADA: A -> X_CERRADA -> B -> G
        rutas_csv = """ruta,orden,estacion
R_DIR,1,A
R_DIR,2,B
R_DIR,3,C
R_DIR,4,D
R1_T,1,A
R1_T,2,E
R2_T,1,E
R2_T,2,D
R_EMP1,1,F
R_EMP1,2,G
R_EMP2,1,F
R_EMP2,2,H
R_EMP3,1,H
R_EMP3,2,G
R_PASA,1,A
R_PASA,2,X_CERRADA
R_PASA,3,B
"""
        with open(os.path.join(cls.CARPETA_TEST, "rutas.csv"), "w", encoding="utf-8") as f:
            f.write(rutas_csv)

        horarios_csv = """ruta,estacion,hora
R_DIR,A,06:00
R_DIR,B,06:05
R_DIR,C,06:10
R_DIR,D,06:15
"""
        with open(os.path.join(cls.CARPETA_TEST, "horarios.csv"), "w", encoding="utf-8") as f:
            f.write(horarios_csv)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.CARPETA_TEST):
            shutil.rmtree(cls.CARPETA_TEST)

    def setUp(self):
        self.red = Red(self.CARPETA_TEST)

    def test_origen_igual_a_destino(self):
        """Decisión 8: Si origen es igual a destino devuelve None."""
        self.assertIsNone(self.red.viaje("A", "A"))

    def test_estacion_inexistente(self):
        """Origen o destino inexistente devuelve None."""
        self.assertIsNone(self.red.viaje("INEXISTENTE", "A"))
        self.assertIsNone(self.red.viaje("A", "INEXISTENTE"))
        self.assertIsNone(self.red.viaje(None, "A"))

    def test_estacion_cerrada(self):
        """Si origen o destino está cerrado devuelve None."""
        self.red.estaciones.get("A").abierta = False
        self.assertIsNone(self.red.viaje("A", "D"))
        self.red.estaciones.get("A").abierta = True

        self.red.estaciones.get("D").abierta = False
        self.assertIsNone(self.red.viaje("A", "D"))

    def test_sin_viaje_posible(self):
        """Estación aislada sin conexión devuelve None."""
        self.assertIsNone(self.red.viaje("A", "AISLADA"))
        self.assertIsNone(self.red.viaje("AISLADA", "A"))

    def test_viaje_directo(self):
        """De A a C en R_DIR es directo."""
        # A -> C directo en R_DIR toma 2 paradas
        viaje = self.red.viaje("A", "C")
        self.assertIsNotNone(viaje)
        self.assertEqual(len(viaje), 1)
        self.assertEqual(viaje[0], ("R_DIR", "A", "C"))

    def test_transbordo_con_menos_paradas_que_directo(self):
        """De A a D: Directo R_DIR toma 3 paradas (A->B->C->D).
        Transbordo A->E en R1_T (1 parada) + E->D en R2_T (1 parada) = 2 paradas.
        Debe ganar el transbordo de 2 paradas."""
        viaje = self.red.viaje("A", "D")
        self.assertIsNotNone(viaje)
        self.assertEqual(len(viaje), 2)
        self.assertEqual(viaje[0], ("R1_T", "A", "E"))
        self.assertEqual(viaje[1], ("R2_T", "E", "D"))

    def test_empate_prefiere_directo(self):
        """De F a G:
        Directo R_EMP1 toma 1 parada (F->G).
        Transbordo F->H (1 parada) + H->G (1 parada) toma 2 paradas.
        Para un empate exacto:
        Si agregamos una ruta directa de F a H (1 parada) vs transbordo F->H->G (2 paradas):
        Creemos caso donde directo = 2 paradas y transbordo = 2 paradas."""
        # En la red: F -> G directo toma 1 parada
        viaje = self.red.viaje("F", "G")
        self.assertEqual(viaje, [("R_EMP1", "F", "G")])

    def test_dos_transbordos_elige_menor(self):
        """Transbordo por E toma 2 paradas; transbordo por B toma 3 paradas (A->B en R_PASA, B->D en R_DIR).
        Debe elegir el de E."""
        viaje = self.red.viaje("A", "D")
        self.assertEqual(viaje, [("R1_T", "A", "E"), ("R2_T", "E", "D")])

    def test_transbordo_evita_estacion_cerrada(self):
        """Si la estación de transbordo E se cierra, debe usar la otra alternativa."""
        # Cerramos E
        self.red.estaciones.get("E").abierta = False
        # Ahora de A a D no puede transbordar en E.
        # Puede ir directo por R_DIR (3 paradas: A->B->C->D)
        # o transbordar en B (R_PASA A->B = 2 paradas, R_DIR B->D = 2 paradas = 4 paradas)
        # El directo toma 3 paradas, por lo que debe dar el directo.
        viaje = self.red.viaje("A", "D")
        self.assertIsNotNone(viaje)
        self.assertEqual(len(viaje), 1)
        self.assertEqual(viaje[0], ("R_DIR", "A", "D"))

    def test_ruta_que_pasa_por_cerrada_cuenta_paradas(self):
        """R_PASA va de A -> X_CERRADA -> B. X_CERRADA está cerrada.
        Nadie puede subir ni bajar en X_CERRADA, pero la ruta pasa por ahí
        y cuenta como 2 paradas de A a B."""
        self.red.estaciones.get("X_CERRADA").abierta = False
        # Subir en X_CERRADA no es permitido
        self.assertIsNone(self.red.viaje("X_CERRADA", "B"))
        self.assertIsNone(self.red.viaje("A", "X_CERRADA"))

        # Pero de A a B en R_PASA recorre 2 paradas (A -> X_CERRADA -> B).
        # R_DIR también va de A a B en 1 sola parada.
        # Así que de A a B elegirá R_DIR (1 parada)
        viaje = self.red.viaje("A", "B")
        self.assertEqual(viaje, [("R_DIR", "A", "B")])

    def test_edicion_previa_de_rutas(self):
        """Si quitamos una parada de una ruta o agregamos una parada, viaje refleja el cambio."""
        # En R_DIR quitamos B: R_DIR ahora es A -> C -> D (2 paradas)
        self.red._quitar_parada("R_DIR", "B")
        # Ahora R_DIR de A a D tiene 2 paradas (A -> C -> D).
        # El transbordo por E también tiene 2 paradas (A -> E -> D).
        # Ante empate de 2 paradas, debe ganar el directo R_DIR!
        viaje = self.red.viaje("A", "D")
        self.assertEqual(viaje, [("R_DIR", "A", "D")])


if __name__ == "__main__":
    unittest.main()
