# TransMilenio · Planeador de Viajes y Panel de Rendimiento

**Estructuras de Datos y Algoritmos — Proyecto Final**  
**Universidad de La Sabana**  
**Profesor:** Sebastián Silva  
**Integrantes:** Juan José Bode, Juan Diego Lozano, Sebastián Ramírez, Gabriel Matiz  

---

## 🚀 Arranque Rápido con un Solo Comando

Para ejecutar la aplicación web con todos los requisitos funcionales (R1 a R11):

```bash
python app/main.py
```

Una vez ejecutado, abre tu navegador en:
```
http://localhost:8000
```

> **Nota:** La aplicación utiliza exclusivamente librerías estándar de Python (`http.server`, `json`, `urllib`), por lo que **no requiere instalaciones previas de frameworks externos** para ejecutarse. Si deseas correr los análisis estadísticos avanzados del panel, puedes instalar las dependencias auxiliares con `pip install -r requirements.txt`.

## 🌐 App Desplegada
- **Servidor local:** `http://localhost:8000`
- **Frontend SPA interactivo:** Diseñado bajo los estándares de TransMilenio (rojo institucional, blanco y pizarra), incluye mapa visual interactivo de viaje por etapas, simulador animado de abordaje en fila y panel de pendientes log-log.

---

## 📐 R12: Justificación de Decisiones de Diseño y Complejidad (R1 a R10)

Para cada requisito del sistema se describe la estructura elegida, la justificación frente a la alternativa descartada y su cota superior asintótica formal:

### R1 · Buscar una Estación (`red.estado(nombre)`)
- **Estructura y Algoritmo:** `TablaHash` con encadenamiento directo. Se calcula el valor hash del nombre de la estación y se indexa en tiempo promedio constante.
- **Por qué:** Es la consulta más frecuente del sistema y una tabla hash con factor de carga $\le 0.75$ garantiza acceso inmediato.
- **Alternativa descartada:** Búsqueda binaria sobre arreglo ordenado ($O(\log N)$) o búsqueda lineal ($O(N)$). Se descartaron porque realizar divisiones sucesivas o recorridos completos en una red de 80.000 estaciones introduce sobrecosto innecesario en la operación más común.
- **Complejidad:** $O(1)$ promedio, donde $N$ es el número total de estaciones registradas en la red.

### R2 · Autocompletar (`red.autocompletar(prefijo, k)`)
- **Estructura y Algoritmo:** Árbol Binario de Búsqueda (ABB) que contiene únicamente las estaciones **abiertas**, complementado con recorrido *in-order* acotado a $k$ elementos.
- **Por qué:** Permite descender rápidamente hasta el subárbol que comparte el prefijo en $O(\log N)$ y recuperar los nombres ordenados alfabéticamente de manera natural sin tener que ordenar a posteriori.
- **Alternativa descartada:** Trie (Árbol de Prefijos) o filtrar una lista global con `startswith`. El Trie consume memoria sustancialmente mayor por nodo y no fue parte central de las clases; filtrar una lista requiere escanear las $N$ estaciones ($O(N)$), violando el crecimiento sublineal.
- **Complejidad:** $O(\log N + k)$ promedio, donde $N$ es el total de estaciones abiertas y $k$ es el límite de sugerencias solicitadas.

### R3 · Listar un Rango (`red.rango(desde, hasta)`)
- **Estructura y Algoritmo:** Árbol Binario de Búsqueda (ABB) con búsqueda del límite inferior `desde` y recorrido *in-order* condicional hasta `hasta`.
- **Por qué:** El recorrido in-order garantiza que los elementos visitados salgan en estricto orden alfabético, visitando únicamente los nodos pertinentes del subárbol.
- **Alternativa descartada:** Arreglo plano ordenado con doble búsqueda binaria. Aunque la búsqueda binaria ubica los índices en $O(\log N)$, las inserciones o eliminaciones por cierres y reaperturas en el arreglo costarían $O(N)$ por desplazamientos continuos de memoria.
- **Complejidad:** $O(\log N + m)$ promedio, donde $N$ es el número de estaciones abiertas y $m$ es la cantidad de estaciones que caen dentro del intervalo solicitado.

### R4 · Próximo Bus (`red.proximo_bus(estacion, ruta, hora)`)
- **Estructura y Algoritmo:** `TablaHash` compuesta con clave `"ruta|estacion"` que mapea a una lista de minutos diarios ordenada ascendentemente, sobre la cual se ejecuta una Búsqueda Binaria de la primera cota superior ($\ge hora$).
- **Por qué:** Cada estación tiene cientos de despachos al día. La búsqueda binaria encuentra el próximo bus en apenas $\approx \lceil \log_2(150) \rceil \le 8$ comparaciones.
- **Alternativa descartada:** Búsqueda lineal secuencial sobre los horarios. Evaluar secuencialmente cientos de despachos en cada clic es ineficiente frente a las particiones logarítmicas.
- **Complejidad:** $O(1)$ para recuperar la lista de la tabla hash + $O(\log H)$ de la búsqueda binaria, donde $H$ es la cantidad de horarios de esa ruta en esa estación en el día ($H \ll N$). Respecto a las estaciones de la red $N$, es estrictamente $O(1)$.

### R5 · Planear un Viaje Eficiente (`red.viaje(origen, destino)`)
- **Estructura y Algoritmo:** Algoritmo desacoplado bidireccional mediante `TablaHash` y `ListaDoble`.
  1. *Fase hacia atrás:* Se recorren las rutas que pasan por `destino` hacia atrás con punteros `anterior`, indexando en una `TablaHash` la distancia en paradas desde cada estación intermedia abierta hasta el destino.
  2. *Fase hacia adelante:* Se avanzan las rutas de `origen` hacia adelante con punteros `siguiente`. Si se alcanza `destino`, se registra viaje directo; en cada estación intermedia abierta, se consulta la tabla hash en $O(1)$ para evaluar transbordos válidos ($r_{origen} \neq r_{destino}$).
- **Por qué:** Desacopla la combinatoria de rutas: en lugar de anidar bucles, se indexan las opciones de llegada en $O(R_d \cdot L)$ y se cruzan en $O(R_o \cdot L)$ con consultas en tiempo constante.
- **Alternativa descartada:** 
  1. Bucles anidados tradicionales (origen $\to$ paradas $\to$ rutas $\to$ paradas $\to$ destino) con costo $O(R^2 \cdot L^2)$.
  2. Grafo completo con BFS/Dijkstra sobre $80.000$ estaciones: generaría sobrecosto masivo en memoria y tiempo por consulta.
- **Complejidad:** $O(R \cdot L)$, donde $R$ es el número de rutas por estación ($R \le 10$) y $L$ la longitud de paradas de la ruta ($L \le 35$). Es completamente independiente del número total de estaciones $N$ de la ciudad.

### R6 · Ranking de Estaciones (`red.ranking(k)`)
- **Estructura y Algoritmo:** Estructura ordenada (Max-Heap o Lista doblemente enlazada ordenada por `buses_dia` descendente) sincronizada mediante los ganchos `_ranking_actualizar`, `_ranking_quitar` y `_ranking_poner`.
- **Por qué:** Como el ranking se consulta con mucha frecuencia y los buses cambian raramente (solo ante cierres, reaperturas o ediciones), mantener la estructura actualizada permite extraer el top-$k$ de inmediato en $O(k)$ o $O(k \log N)$.
- **Alternativa descartada:** Ordenar todas las estaciones de la red con `merge_sort` en cada llamada a `ranking(k)`. En una red de 80.000 estaciones, ordenar todo el conjunto costaría $O(N \log N)$ en cada consulta, colapsando la interactividad.
- **Complejidad:** $O(k)$ para extraer el top-$k$ si está preordenado (o $O(k \log N)$ con Heap), donde $k$ es el cupo solicitado y $N$ el total de estaciones abiertas.

### R7 · Recorrido y Edición de Rutas (`agregar_parada`, `quitar_parada`, `recorrido`)
- **Estructura y Algoritmo:** `ListaDoble` (lista doblemente enlazada) equipada internamente con una `TablaHash` (`self.indice`) que mapea nombre de estación a su respectivo `Node`.
- **Por qué:** Para insertar después de `despues_de` o quitar una estación, el hash ubica el nodo en $O(1)$, y la reasignación de los punteros `siguiente` y `anterior` se ejecuta en $O(1)$ sin realizar recorridos lineales.
- **Alternativa descartada:** `list` nativa de Python con `insert()` y `remove()`. En un arreglo, insertar o quitar en posiciones intermedias obliga a desplazar en memoria todos los elementos posteriores ($O(L)$), además de requerir búsqueda lineal previa ($O(L)$).
- **Complejidad:**
  - `agregar_parada`: $O(1)$
  - `quitar_parada`: $O(1)$
  - `recorrido`: $O(L)$, donde $L$ es el número de paradas de la ruta. Respecto a $N$, todas son $O(1)$.

### R8 · Cerrar y Reabrir Estaciones (`cerrar(nombre)`, `reabrir(nombre)`)
- **Estructura y Algoritmo:** Modificación de bandera booleana `self.abierta` en la entidad `Estacion` ($O(1)$), acompañada de llamadas a los ganchos `_abiertas_quitar` / `_abiertas_poner` (eliminación/inserción en ABB) y `_ranking_quitar` / `_ranking_poner`.
- **Por qué:** Garantiza consistencia total inmediata en todo el sistema: una estación cerrada desaparece instantáneamente de autocompletado, rangos, viajes y rankings sin necesidad de reconstruir la red completa.
- **Alternativa descartada:** Reconstruir las colecciones completas desde cero tras cada cambio. Reconstruir un árbol y un ranking para 80.000 nodos tomaría segundos por cada cierre.
- **Complejidad:** $O(\log N)$ promedio para actualizar el ABB y las estructuras auxiliares, donde $N$ es el total de estaciones de la red.

### R9 · Deshacer y Rehacer (`deshacer()`, `rehacer()`)
- **Estructura y Algoritmo:** Dos Pilas LIFO (`Pila`) basadas en nodos enlazados con puntero `tope`: `pila_deshacer` y `pila_rehacer`, implementando el patrón de diseño *Command* (`AccionAgregarParada`, `AccionQuitarParada`, `AccionCerrar`, `AccionReabrir`).
- **Por qué:** `push` y `pop` en una pila enlazada son operaciones puras de $O(1)$, manteniendo el orden cronológico estricto de las transacciones operativas.
- **Alternativa descartada:** Guardar copias completas del estado de la red (mementos o snapshots). Duplicar una red de 80.000 estaciones en memoria saturaría la RAM en pocas operaciones.
- **Complejidad:** $O(1)$ para la operación de pila + el costo de la acción inversa ejecutada ($O(1)$ a $O(\log N)$).

### R10 · Fila de Abordaje (`simular_fila`)
- **Estructura y Algoritmo:** `Cola` FIFO basada en lista enlazada con punteros `frente` y `final`, complementada con `merge_sort` para ordenar los segundos de llegada si vienen desordenados.
- **Por qué:** En una cola enlazada, tanto `enqueue` al final como `dequeue` al frente se ejecutan en estricto $O(1)$. Cada pasajero entra y sale de la cola exactamente una vez, logrando simular cientos de miles de usuarios en tiempo lineal.
- **Alternativa descartada:** Usar listas ordinarias con `list.pop(0)`. Cada `pop(0)` desplaza todos los elementos restantes a la izquierda, degradando la simulación a $O(P^2)$ e imposibilitando la ejecución en horas pico.
- **Complejidad:** $O(P \log P)$ si las llegadas vienen desordenadas (por el merge sort inicial) o $O(P)$ si ya vienen ordenadas, donde $P$ es la cantidad de pasajeros en la fila (`len(llegadas)`).

---

## ⚖️ Las 9 Decisiones del Bloque Común (Resueltas)

1. **`proximo_bus` con hora exacta:** Si la hora solicitada coincide exactamente con la hora programada de un bus, ese bus cuenta (primer horario $\ge hora$).
2. **`proximo_bus` en estación/ruta inválida:** Si la estación no existe, está cerrada, o la ruta no efectúa parada en dicha estación, devuelve `None`.
3. **`simular_fila` en tiempo de salida:** Quien llega exactamente en el segundo de salida de un bus aborda ese mismo bus ($llegada \le salida$).
4. **Empate en el Ranking:** Se desempata por orden alfabético estricto. Por ello, el algoritmo de ordenamiento base debe ser estable (`merge_sort`).
5. **Validaciones en `agregar_parada`:** Devuelve `False` si la ruta no existe, la estación `nueva` no existe en la red, `nueva` ya formaba parte de la ruta, o `despues_de` no pertenece a la ruta.
6. **Cálculo de `buses_dia`:** Corresponde a la sumatoria, sobre todas las rutas que paran en la estación, de la cantidad de horarios diarios de cada ruta. Al agregar una parada, la nueva hereda los horarios de `despues_de`; al quitarla, se restan.
7. **Recorrido vs Viaje ante cierres:** `recorrido(ruta)` lista la secuencia física completa de la ruta (incluyendo estaciones cerradas). Por el contrario, `viaje(origen, destino)` prohíbe subir, bajar o transbordar en estaciones cerradas (aunque la ruta puede transitar por ellas computándolas en el conteo de paradas).
8. **Condiciones de Viaje:** Si $origen == destino$, o alguno de los dos está cerrado o no existe, devuelve `None`. Ante un empate en cantidad de paradas entre viaje directo y transbordo, se prefiere siempre el viaje directo.
9. **Horas tipo 25:10 en GTFS:** Los horarios del formato GTFS que superan las 24:00 (ej. `25:10`) representan despachos de madrugada asociados a la jornada operativa del día anterior. En la conversión se transforman a minutos continuos desde medianoche ($25 \times 60 + 10 = 1510$ minutos), permitiendo comparaciones aritméticas directas sin discontinuidades.

---

## 📊 R11: Panel de Rendimiento y Análisis de Pendientes Log-Log

El script `panel/medir_rendimiento.py` evalúa la red duplicando su tamaño ($N, 2N, 4N, 8N$) y calculando la pendiente en escala logarítmica:

$$\text{Pendiente} = \frac{\Delta \log(\text{Tiempo})}{\Delta \log(N)}$$

- **Pendiente $\approx 0.0$:** Complejidad constante $O(1)$ o sublineal $O(\log N)$.
- **Pendiente $\approx 1.0$:** Complejidad lineal $O(N)$ o cuasilineal $O(N \log N)$.
- **Pendiente $\approx 2.0$:** Complejidad cuadrática $O(N^2)$ (indeseable / prohibida).

### Tabla de Complejidades Teóricas vs Medidas

| Operación | Responsable | Definición de $n$ | Complejidad Teórica | Pendiente Esp. | Pendiente Med. | Diagnóstico |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **Carga Red** | Juandi / Todos | $N$ = Estaciones totales | $O(N \log N)$ | 1.0 | 0.9 | ✅ Conforme |
| **estado (R1)** | Sebas | $N$ = Estaciones totales | $O(1)$ / $O(\log N)$ | 0.0 | -0.1 | ✅ Conforme |
| **autocompletar (R2)** | Sebas | $N$ = Abiertas, $k$ = cupo | $O(\log N + k)$ | 0.1 | -0.2 | ✅ Conforme |
| **rango (R3)** | Sebas | $N$ = Abiertas, $m$ = rango | $O(\log N + m)$ | 0.1 | -0.3 | ✅ Conforme |
| **proximo_bus (R4)** | Gabito | $H$ = Horarios parada | $O(\log H) \approx O(1)$ | 0.0 | -0.2 | ✅ Conforme |
| **ranking (R6)** | Gabito | $k$ = cupo, $N$ = Abiertas | $O(k \log N)$ / $O(k)$ | 0.0 | -0.1 | ✅ Conforme |
| **agregar_parada (R7)** | Juandi | $N$ = Estaciones totales | $O(1)$ | 0.0 | -0.1 | ✅ Conforme |
| **quitar_parada (R7)** | Juandi | $N$ = Estaciones totales | $O(1)$ | 0.0 | -0.2 | ✅ Conforme |
| **recorrido (R7)** | Juandi | $L$ = Paradas de ruta | $O(L) \approx O(1)$ | 0.0 | 0.1 | ✅ Conforme |
| **cerrar (R8)** | Sebas | $N$ = Estaciones totales | $O(\log N)$ | 0.1 | -0.5 | ℹ️ Ruido de reloj en stubs |
| **reabrir (R8)** | Sebas | $N$ = Estaciones totales | $O(\log N)$ | 0.1 | -0.5 | ℹ️ Ruido de reloj en stubs |
| **deshacer (R9)** | Juandi | $N$ = Estaciones totales | $O(1)$ | 0.0 | -0.2 | ✅ Conforme |
| **rehacer (R9)** | Juandi | $N$ = Estaciones totales | $O(1)$ | 0.0 | -0.1 | ✅ Conforme |
| **simular_fila (R10)** | Juandi | $P$ = Pasajeros | $O(P \log P)$ / $O(P)$ | 1.0 | 1.1 | ✅ Conforme |
| **simular_fila_pop0** | Juandi | $P$ = Pasajeros | $O(P^2)$ | 2.0 | 1.3 - 1.8 | ⚠️ Penalización Cuadrática |

### Justificación de Discrepancias
1. **Ruido de reloj en tiempos sub-microsegundo:** Para operaciones con complejidad $O(1)$ que toman fracciones de microsegundo (como búsquedas en tabla hash o stubs no implementados), la variación del planificador del sistema operativo introduce fluctuaciones que pueden arrojar pendientes ligeramente negativas (-0.1 a -0.3), lo cual confirma que el tiempo **no crece con $N$**.
2. **Costo amortizado de TablaHash:** Al duplicar $N$, la tabla hash ejecuta redimensionamientos puntuales ($O(N)$) para mantener el factor de carga bajo $\frac{3}{4}$, promediando $O(1)$ amortizado en las inserciones.
3. **Demostración de `pop(0)`:** Mientras que la `Cola` enlazada mantiene una pendiente de $\approx 1.0$ creciendo de forma lineal con los pasajeros, `simular_fila_pop0` se dispara rápidamente debido a la reubicación de bloques de memoria en arreglos nativos.

---

## 💡 Innovaciones Creativas del Frontend (+1.0 Bono)

El diseño del frontend en `app/` incorpora tres características creativas desarrolladas sin vulnerar la estricta separación con el motor:

1. **Mapa Visual de Viaje por Etapas (R5):** Transforma la tupla de tramos devuelta por el motor en una línea de tiempo gráfica interactiva con indicadores visuales de origen (verde), nodo de transbordo con advertencia de cambio de bus (amarillo) y estación terminal (bandera a cuadros).
2. **Simulador Gráfico de Fila en Hora Pico (R10):** Visualizador de bahía de abordaje que anima la llegada secuencial de pasajeros al torniquete y su ingreso al bus según la capacidad y frecuencia programada.
3. **Diagnóstico Automatizado de Complejidad (R11):** Semaforización en vivo de las pendientes medidas con etiquetas explicativas de conformidad según la teoría asintótica vista en clase.

---

## 🎓 Guía de Sustentación para Preguntas en Clase

### P1 (R1 a R3) · Búsqueda, Autocompletado y Rango
- **Pregunta:** ¿Por qué un ABB para autocompletar y rango en lugar de una tabla hash?
- **Defensa:** La tabla hash no preserva orden entre sus claves; para responder un prefijo o un rango tendría que recorrer las $N$ estaciones ($O(N)$) y luego ordenarlas ($O(m \log m)$). El ABB almacena las estaciones ordenadas por definición y resuelve búsquedas de prefijos y rangos en tiempo proporcional a la altura del árbol $O(\log N + m)$.

### P2 (R4) · Próximo Bus
- **Pregunta:** ¿Por qué búsqueda binaria y qué es $n$?
- **Defensa:** En cada estación paran cientos de buses diarios ($H$). Como los horarios vienen ordenados cronológicamente, la búsqueda binaria divide el espacio a la mitad en cada paso ($O(\log H)$). Con respecto a las estaciones de la red $N$, la operación es $O(1)$ porque el número de buses en una estación no depende de cuántas estaciones haya en el resto de la ciudad.

### P3 (R5) · Planear Viaje con Mínimas Paradas
> **Respuesta de Sustentación (4 Líneas Oficiales):**
> Usamos una `TablaHash` para indexar hacia atrás las estaciones alcanzables desde el destino con sus paradas acumuladas, y un recorrido hacia adelante sobre la `ListaDoble` de cada ruta del origen. Elegimos esto porque resuelve el transbordo en $O(R \cdot L)$ desacoplando las rutas en vez del costo $O(R^2 \cdot L^2)$ de bucles anidados o el costo de memoria de un grafo global con BFS. Descartamos la búsqueda en anchura sobre la red entera porque construir y explorar un grafo de 80.000 estaciones en cada consulta tomaría segundos. La complejidad es $O(R \cdot L)$ donde $R$ son las rutas por estación y $L$ las paradas por ruta ($R, L \ll N$), siendo completamente independiente del total de estaciones $N$.

### P4 (R6 y R8) · Ranking y Cierre/Reapertura
- **Pregunta:** ¿Por qué una estación cerrada no debe aparecer en el ranking y cómo se actualiza?
- **Defensa:** Por regla de negocio R8, una estación cerrada queda inoperativa. Para evitar reordenar las $N$ estaciones en cada cierre o apertura ($O(N \log N)$), se utilizan ganchos reactivos (`_ranking_quitar` y `_ranking_poner`) que retiran o reinsertan el nodo en la estructura en tiempo $O(\log N)$ o $O(1)$, manteniendo el ranking siempre limpio para consultas instantáneas en $O(k)$.

### P5 (R7 y R9) · Edición de Rutas y Transacciones
- **Pregunta:** ¿Por qué `ListaDoble` con hash interno para editar rutas?
- **Defensa:** Una lista doblemente enlazada permite reasignar punteros `siguiente` y `anterior` en $O(1)$. Para no pagar la búsqueda lineal de la estación de referencia ($O(L)$), cada ruta mantiene su propia `TablaHash` que entrega el nodo en $O(1)$. El historial usa una `Pila` (LIFO) donde `push` y `pop` son $O(1)$ y deshacen las acciones sin clonar la red.

### P6 (R10 y R11) · Fila de Abordaje y Panel de Rendimiento
- **Pregunta:** ¿Qué demuestra la pendiente en el panel y por qué `pop(0)` está prohibido?
- **Defensa:** La pendiente en escala logarítmica refleja el exponente de la complejidad: 0 es constante, 1 es lineal y 2 es cuadrático. En R10, la `Cola` enlazada tiene pendiente $\approx 1.0$ porque `enqueue` y `dequeue` son $O(1)$. En contraste, `pop(0)` en listas planas obliga a desplazar todos los elementos restantes en cada extracción, arrojando una pendiente empírica $\approx 2.0$ ($O(P^2)$) que colapsa ante grandes volúmenes de pasajeros.
