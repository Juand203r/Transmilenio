# Integrantes del Proyecto y Asignacion de Requisitos

Universidad de La Sabana  
Estructuras de Datos y Algoritmos  
Profesor: Sebastian Silva  
Proyecto Final: Planeador de Viajes TransMilenio  

---

## Equipo de Trabajo

| Nombre Completo | Usuario Git / Rama | Requisitos y Modulos a Cargo |
| :--- | :--- | :--- |
| **Juan Sebastian Bode Velasquez** | `Juan-Bode` | **R5** (`motor/viaje.py`: Algoritmo de minimas paradas con TablaHash y recorrido inverso), **R11** (`panel/medir_rendimiento.py`: Panel de rendimiento y calculo de pendientes log-log), `panel/generar_red.py` (Generador de redes sinteticas escalables), `app/` (Aplicacion Web SPA interactiva con mapa de ruta por etapas y simulador de cola), `tests/test_viaje.py`, `README.md` (Consolidacion de decisiones R12 y guia de sustentacion) e `integrantes.md`. |
| **Juan Diego Lozano Ortiz** | `juandi` | **Infraestructura Base y Carga:** `motor/tabla_hash.py` (Tabla Hash con encadenamiento), `motor/red.py` (Esqueleto, carga de estaciones y rutas, infraestructura transaccional), `motor/lista_doble.py` (Lista doblemente enlazada indexada por hash), `motor/pila.py` (Pila LIFO para deshacer/rehacer), `motor/cola.py` (Cola FIFO enlazada), `motor/historial.py` (Patron Command: Acciones de estacion y ruta), **R7** (`agregar_parada`, `quitar_parada`, `recorrido`), **R9** (`deshacer`, `rehacer`), **R10** (`motor/fila.py`: Simulacion de abordaje en O(n log n)), `panel/fila_pop0.py` (Referencia cuadratica O(n^2)), `tests/test_base.py`, `tests/test_operacion.py`. |
| **Gabriel Alejandro Matiz Mora** | `Gabriel-Matiz` | **R4 y R6:** `motor/ordenar.py` (MergeSort estable), `motor/ranking.py` (R6: Ranking de estaciones mas transitadas, `_construir_ranking`, `_ranking_quitar`, `_ranking_poner`, `_ranking_actualizar`), `conversion/convertir_gtfs.py` (Script de conversion GTFS a CSVs y normalizacion de horarios 25:10), carga de horarios en `_cargar_horarios` y `proximo_bus` (R4: busqueda binaria sobre horarios diarios). |
| **Juan Sebastian Ramirez Pico** | `Sebas-Ramirez` | **R1, R2, R3 y R8:** `motor/abb.py` (Arbol Binario de Busqueda para estaciones abiertas), `estado` (R1), `autocompletar` (R2: busqueda de prefijo in-order hasta k elementos), `rango` (R3: recorrido in-order entre cotas [desde, hasta]), `_construir_abiertas`, `_abiertas_poner`, `_abiertas_quitar`, `cerrar` y `reabrir` (R8). |

---

## Consistencia con el Historial de Git
- **Branch de trabajo de Juan:** `Juan-Bode`.
- **Desarrollos realizados:**
  - `panel/generar_red.py`: Implementacion completa del generador sintetico que permite verificar la escalabilidad del sistema con 10k, 20k, 40k y 80k estaciones.
  - `motor/viaje.py`: Implementacion del algoritmo desacoplado en $O(R \cdot L)$ utilizando `TablaHash` hacia atras desde el destino y avance hacia adelante desde el origen con `ListaDoble`.
  - `tests/test_viaje.py`: Bateria de pruebas unitarias que cubre los casos borde requeridos.
  - `panel/medir_rendimiento.py`: Script de medicion empirica con mediana de `perf_counter` y calculo de pendientes log-log.
  - `app/main.py` y `app/index.html`: Servidor web y frontend de TransMilenio con visualizador de etapas de viaje y simulador de abordaje.
  - `README.md`: Documentacion de diseno, decisiones y sustentacion teorica formal.
