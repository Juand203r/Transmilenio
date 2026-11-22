# Integrantes del Proyecto y Asignación de Requisitos

**Universidad de La Sabana**  
**Estructuras de Datos y Algoritmos**  
**Profesor:** Sebastián Silva  
**Proyecto Final:** Planeador de Viajes TransMilenio  

---

## 👥 Equipo de Trabajo

| Nombre Completo | Usuario Git / Rama | Requisitos y Módulos a Cargo |
| :--- | :--- | :--- |
| **Juan José Bode** | `Juan-Bode` | **R5** (`motor/viaje.py`: Algoritmo de mínimas paradas con TablaHash y recorrido inverso), **R11** (`panel/medir_rendimiento.py`: Panel de rendimiento y cálculo de pendientes log-log), `panel/generar_red.py` (Generador de redes sintéticas escalables), `app/` (Aplicación Web SPA interactiva con mapa de ruta por etapas y simulador animado de cola), `tests/test_viaje.py`, `README.md` (Consolidación de decisiones R12 y guía de sustentación) e `integrantes.md`. |
| **Juan Diego Lozano (Juandi)** | `juandi` | **Infraestructura Base y Carga:** `motor/tabla_hash.py` (Tabla Hash con encadenamiento), `motor/red.py` (Esqueleto, carga de estaciones y rutas, infraestructura transaccional), `motor/lista_doble.py` (Lista doblemente enlazada indexada por hash), `motor/pila.py` (Pila LIFO para deshacer/rehacer), `motor/cola.py` (Cola FIFO enlazada), `motor/historial.py` (Patrón Command: Acciones de estación y ruta), **R7** (`agregar_parada`, `quitar_parada`, `recorrido`), **R9** (`deshacer`, `rehacer`), **R10** (`motor/fila.py`: Simulación de abordaje en O(n log n)), `panel/fila_pop0.py` (Referencia cuadrática O(n²)), `tests/test_base.py`, `tests/test_operacion.py`. |
| **Sebastián Ramírez (Sebas)** | `Sebas-Ramirez` | **R1, R2, R3 y R8:** `motor/abb.py` (Árbol Binario de Búsqueda para estaciones abiertas), `estado` (R1), `autocompletar` (R2: búsqueda de prefijo in-order hasta k elementos), `rango` (R3: recorrido in-order entre cotas [desde, hasta]), `_construir_abiertas`, `_abiertas_poner`, `_abiertas_quitar`, `cerrar` y `reabrir` (R8). |
| **Gabriel Matiz (Gabito)** | `Gabriel-Matiz` | **R4 y R6:** `motor/ordenar.py` (MergeSort estable), `motor/ranking.py` (R6: Ranking de estaciones más transitadas, `_construir_ranking`, `_ranking_quitar`, `_ranking_poner`, `_ranking_actualizar`), `conversion/convertir_gtfs.py` (Script de conversión GTFS a CSVs y normalización de horarios 25:10), carga de horarios en `_cargar_horarios` y `proximo_bus` (R4: búsqueda binaria sobre horarios diarios). |

---

## 📌 Consistencia con el Historial de Git
- **Branch de trabajo de Juan:** `Juan-Bode`.
- **Desarrollos realizados:**
  - `panel/generar_red.py`: Implementación completa del generador sintético que permite verificar la escalabilidad del sistema con 10k, 20k, 40k y 80k estaciones.
  - `motor/viaje.py`: Implementación del algoritmo desacoplado en $O(R \cdot L)$ utilizando `TablaHash` hacia atrás desde el destino y avance hacia adelante desde el origen con `ListaDoble`.
  - `tests/test_viaje.py`: Batería exhaustiva de pruebas unitarias que cubre los 11 casos borde requeridos.
  - `panel/medir_rendimiento.py`: Script de medición empírica con mediana de `perf_counter` y cálculo de pendientes log-log.
  - `app/main.py` y `app/index.html`: Servidor web sin dependencias externas y frontend de TransMilenio con visualizador de etapas de viaje y simulador animado de abordaje.
  - `README.md`: Documentación completa de diseño, decisiones y sustentación teórica.
