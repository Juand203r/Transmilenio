# TransMilenio - Planeador de Viajes y Panel de Rendimiento

Estructuras de Datos y Algoritmos - Proyecto Final  
Universidad de La Sabana  
Profesor: Sebastian Silva  
Integrantes: Juan Sebastian Bode Velasquez, Juan Diego Lozano Ortiz, Gabriel Alejandro Matiz Mora, Juan Sebastian Ramirez Pico  

---

## Instrucciones de Ejecucion

Para iniciar la aplicacion web con todos los modulos:

```bash
python app/main.py
```

Una vez ejecutado el comando, abrir el navegador en:
```
http://localhost:8000
```

El servidor web utiliza exclusivamente librerias estandar de Python (`http.server`, `json`, `urllib`), por lo cual no requiere dependencias externas para arrancar. Para ejecutar los scripts de medicion y analisis estadistico del panel se pueden instalar las librerias auxiliares con:

```bash
pip install -r requirements.txt
```

Para regenerar los tres CSV desde el GTFS (y, opcionalmente, las coordenadas para el mapa):

```bash
python conversion/convertir_gtfs.py ruta/al/gtfs.zip datos/ --coordenadas
```

## App Desplegada
La app no esta publicada en un servidor externo: se ejecuta en local con el comando unico `python app/main.py` y queda disponible en `http://localhost:8000`.
- Frontend (`app/index.html`): interfaz web que solo llama al motor a traves de endpoints REST de `app/main.py`; la instancia de la red vive en memoria del servidor.
- Panel de rendimiento (R11): pestaña "Panel Rendimiento" de la misma app, con una grafica log-log por operacion (medido vs. esperado) y la tabla de pendientes.

---

## R12: Justificacion de Decisiones de Diseno y Complejidad (R1 a R10)

### R1. Buscar una Estacion (`red.estado(nombre)`)
- **Estructura y algoritmo:** Tabla hash con resolucion de colisiones por encadenamiento. Se calcula `hash(nombre) % capacidad` para acceder directamente a la cubeta.
- **Por que:** Es la consulta mas recurrente de la aplicacion. Con un factor de carga acotado a 0.75, la busqueda toma tiempo constante en promedio.
- **Alternativa descartada:** Busqueda binaria sobre arreglo ordenado ($O(\log N)$) o busqueda lineal ($O(N)$). Se descartaron porque en una red de 80.000 estaciones anadir sobrecosto logaritmico o lineal en la operacion basica degrada el desempeno general.
- **Complejidad:** $O(1)$ promedio, donde $N$ es el total de estaciones registradas en la red.

### R2. Autocompletar (`red.autocompletar(prefijo, k)`)
- **Estructura y algoritmo:** Arbol Binario de Busqueda (ABB) que almacena exclusivamente las estaciones abiertas. Se desciende hasta el nodo raiz del prefijo y se realiza un recorrido in-order limitado a $k$ elementos.
- **Por que:** Permite ubicar la primera coincidencia en tiempo logaritmico y recuperar los resultados ya ordenados alfabeticamente sin necesidad de un ordenamiento posterior.
- **Alternativa descartada:** Filtrar un arreglo plano con `startswith` ($O(N)$) o implementar un Trie. El escaneo lineal no escala con $N$, y el Trie incrementa la memoria por nodo de forma innecesaria para el alcance del problema.
- **Complejidad:** $O(\log N + k)$ promedio, donde $N$ es el numero de estaciones abiertas y $k$ es la cota maxima de sugerencias.

### R3. Listar un Rango (`red.rango(desde, hasta)`)
- **Estructura y algoritmo:** Arbol Binario de Busqueda (ABB) con busqueda del limite inferior y recorrido in-order acotado hasta el limite superior.
- **Por que:** La propiedad de orden del arbol garantiza que los elementos se visitan en orden alfabetico estricto visitando unicamente los subarboles relevantes.
- **Alternativa descartada:** Arreglo ordenado con busqueda binaria. Aunque la consulta toma $O(\log N + m)$, mantener el arreglo ordenado ante inserciones o eliminaciones por cierres y aperturas cuesta $O(N)$ por desplazamientos en memoria.
- **Complejidad:** $O(\log N + m)$ promedio, donde $N$ es el total de estaciones abiertas y $m$ es el numero de estaciones contenidas en el intervalo.

### R4. Proximo Bus (`red.proximo_bus(estacion, ruta, hora)`)
- **Estructura y algoritmo:** Tabla hash con clave compuesta `"ruta|estacion"` que almacena la lista de horarios del dia en minutos ordenada ascendentemente, sobre la cual se aplica busqueda binaria de la primera cota superior ($\ge hora$) (`primer_mayor_o_igual` en `motor/ordenar.py`). Las listas se ordenan una sola vez al cargar `horarios.csv` con `merge_sort`, que primero revisa en $O(H)$ si ya vienen ordenadas (lo normal en el GTFS) y solo en caso contrario ordena en $O(H \log H)$. La hora se devuelve como texto `HH:MM` (1510 minutos se devuelven como `25:10`).
- **Por que:** Una estacion puede registrar cientos de despachos diarios. La busqueda binaria localiza el horario adecuado en a lo sumo $\lceil \log_2(H) \rceil \le 8$ comparaciones.
- **Alternativa descartada:** Busqueda secuencial en la lista de horarios. Recorrer linealmente las salidas en cada consulta resulta ineficiente frente a la particion logaritmica.
- **Complejidad:** $O(1)$ para recuperar la lista de la tabla hash + $O(\log H)$ de la busqueda binaria, donde $H$ es la cantidad de horarios diarios de esa ruta en esa parada. Respecto a $N$ (tamano de la red), la complejidad es $O(1)$.

### R5. Planear un Viaje (`red.viaje(origen, destino)`)
- **Estructura y algoritmo:** Algoritmo de cruce desacoplado mediante tabla hash y lista doblemente enlazada.
  1. *Fase inversa:* A partir de las rutas que pasan por `destino`, se recorre hacia atras con punteros `anterior`, guardando en una tabla hash cada estacion intermedia abierta con su distancia acumulada en paradas hasta el destino.
  2. *Fase directa:* Se recorren hacia adelante las rutas del `origen` con punteros `siguiente`. Si se alcanza `destino`, se registra viaje directo; en cada estacion intermedia abierta, se consulta la tabla hash en $O(1)$ para verificar posibles transbordos a rutas distintas ($r_o \neq r_d$).
- **Por que:** Desacopla la combinatoria de rutas. En lugar de anidar busquedas, indexa las llegadas en $O(R_d \cdot L)$ y las cruza en $O(R_o \cdot L)$ mediante consultas en tiempo constante.
- **Alternativa descartada:** 
  1. Bucles anidados de rutas y paradas ($O(R^2 \cdot L^2)$).
  2. Construccion de un grafo global con BFS/Dijkstra sobre 80.000 estaciones, lo cual demandaria excesivo tiempo y memoria por consulta.
- **Complejidad:** $O(R \cdot L)$, donde $R$ es el numero de rutas por estacion ($R \le 10$) y $L$ la cantidad de paradas de la ruta ($L \le 35$). Es independiente de $N$ (total de estaciones de la ciudad).

### R6. Ranking de Estaciones (`red.ranking(k)`)
- **Estructura y algoritmo:** Arbol binario de busqueda balanceado (AVL, `motor/ranking.py`) con claves `(-buses_dia, nombre)` de las estaciones abiertas, mas una tabla hash `nombre -> clave actual`. Por el signo menos, el recorrido in-order entrega primero las estaciones con mas buses y, en empate, en orden alfabetico. `ranking(k)` baja hasta la clave minima y recorre in-order solo $k$ nodos (con una pila, sin recursion). Se arma al cargar en $O(N)$ desde las claves ya ordenadas con `merge_sort` (el elemento del medio es la raiz) y se sincroniza con los ganchos `_ranking_quitar` (cerrar), `_ranking_poner` (reabrir) y `_ranking_actualizar` (editar rutas cambia `buses_dia`). La tabla hash recuerda la clave vieja, que es la que hay que borrar del arbol cuando `buses_dia` ya cambio.
- **Por que:** El ranking se consulta repetidamente pero sufre modificaciones unicamente ante eventos de cierre, reapertura o edicion de paradas. Mantener el orden de forma incremental permite responder en $O(k)$ sin recalcular toda la red.
- **Alternativas descartadas:** (1) Ordenar todas las estaciones con `merge_sort` en cada invocacion de `ranking(k)`: $O(N \log N)$ por peticion. (2) Arreglo o lista enlazada ordenada: la consulta seria $O(k)$, pero reubicar una estacion al cerrar, reabrir o editar cuesta $O(N)$. (3) Monticulo maximo: actualiza en $O(\log N)$, pero sacar el top $k$ cuesta $O(k \log N)$ y borrar una estacion cualquiera (cerrarla) no es directo. (4) ABB sin balancear: con claves que llegan ordenadas se degenera en una lista y todo pasa a $O(N)$; el AVL rota para mantener altura $O(\log N)$.
- **Complejidad:** `ranking(k)` en $O(\log N + k)$; `_ranking_quitar`, `_ranking_poner` y `_ranking_actualizar` en $O(\log N)$; construccion en $O(N \log N)$ por el ordenamiento inicial. $N$ es el total de estaciones abiertas y $k$ el numero pedido. Medido de 10.000 a 80.000 estaciones: pendiente de `ranking(10)` y de editar rutas cercana a 0.

### R7. Recorrido y Edicion de Rutas (`agregar_parada`, `quitar_parada`, `recorrido`)
- **Estructura y algoritmo:** `ListaDoble` con indice interno mediante tabla hash (`self.indice`) que mapea nombre de estacion a su respectivo `Node`.
- **Por que:** Para insertar despues de una parada o retirar una estacion, el hash localiza el nodo en $O(1)$ y los punteros `siguiente` y `anterior` se reasignan en $O(1)$ sin recorrer la lista.
- **Alternativa descartada:** Listas nativas de Python con `insert()` y `remove()`. Las inserciones intermedias en arreglos contiguos fuerzan el desplazamiento en memoria de todos los elementos posteriores ($O(L)$), sumado a la busqueda lineal previa.
- **Complejidad:**
  - `agregar_parada`: $O(1)$
  - `quitar_parada`: $O(1)$
  - `recorrido`: $O(L)$, donde $L$ es la longitud de la ruta. Respecto a $N$, es $O(1)$.

### R8. Cerrar y Reabrir Estaciones (`cerrar`, `reabrir`)
- **Estructura y algoritmo:** Actualizacion de la bandera `abierta` en el objeto `Estacion` ($O(1)$) junto con llamadas a `_abiertas_quitar` / `_abiertas_poner` (ABB) y `_ranking_quitar` / `_ranking_poner`.
- **Por que:** Evita reconstruir las colecciones completas tras cada cambio de estado, manteniendo coherencia inmediata en busquedas, autocompletado y rutas.
- **Alternativa descartada:** Reconstruir el arbol y el ranking desde cero. Para 80.000 estaciones, la reconstruccion tomaria varios segundos por cada cierre.
- **Complejidad:** $O(\log N)$ promedio para actualizar el arbol y las estructuras asociadas, donde $N$ es el total de estaciones en la red.

### R9. Deshacer y Rehacer (`deshacer`, `rehacer`)
- **Estructura y algoritmo:** Dos instancias de `Pila` LIFO enlazada (`pila_deshacer` y `pila_rehacer`) bajo el patron Command (`AccionAgregarParada`, `AccionQuitarParada`, `AccionCerrar`, `AccionReabrir`).
- **Por que:** Las operaciones `push` y `pop` sobre nodos enlazados son $O(1)$ estricto y conservan el orden cronologico de las acciones sin duplicar informacion.
- **Alternativa descartada:** Guardar copias completas de la red (snapshots). Duplicar una estructura de decenas de miles de estaciones saturaria la memoria en pocas iteraciones.
- **Complejidad:** $O(1)$ para la manipulacion de la pila mas el costo de la accion inversa ejecutada ($O(1)$ a $O(\log N)$).

### R10. Fila de Abordaje (`simular_fila`)
- **Estructura y algoritmo:** `Cola` FIFO basada en lista enlazada con punteros `cabeza` y `cola`, precedida por un `merge_sort` sobre los indices de llegada si la secuencia de entrada no viene ordenada.
- **Por que:** Tanto `enqueue` al final como `dequeue` al inicio se ejecutan en $O(1)$. Cada pasajero ingresa y egresa de la estructura exactamente una vez, procesando grandes volumenes de usuarios en tiempo lineal.
- **Alternativa descartada:** Listas convencionales con `list.pop(0)`. En Python, `pop(0)` reubica todos los elementos restantes hacia la izquierda, degradando el algoritmo a $O(P^2)$ e imposibilitando la simulacion en hora pico.
- **Complejidad:** $O(P \log P)$ si las llegadas vienen desordenadas (por el ordenamiento inicial) o $O(P)$ si ya vienen ordenadas, donde $P$ es la cantidad de pasajeros simulados (`len(llegadas)`).

---

## Decisiones Generales del Proyecto

1. **`proximo_bus` en coincidencia exacta:** Si la hora de consulta coincide con la de un bus, dicho bus se toma en cuenta (primer horario $\ge hora$).
2. **`proximo_bus` con parametros invalidos:** Si la estacion no existe, esta cerrada, o la ruta no para en el punto, devuelve `None`.
3. **`simular_fila` en tiempo de partida:** Quien llega en el segundo exacto de salida del bus alcanza a subir ($llegada \le salida$).
4. **Desempate en el ranking:** Ante igualdad en buses diarios, se desempata por orden alfabetico ascendente. Por ello el ordenamiento utilizado es estable.
5. **Validaciones de `agregar_parada`:** Retorna `False` si la ruta no existe, si la nueva estacion no existe, si ya estaba en la ruta o si la estacion de referencia no forma parte del trayecto.
6. **Conteo de `buses_dia`:** Equivale a la suma de horarios diarios de todas las rutas que se detienen en la estacion. Al anadir paradas intermedias, la nueva parada hereda los horarios de `despues_de`.
7. **Recorridos frente a estaciones cerradas:** `recorrido(ruta)` muestra el trazado fisico completo (incluyendo paradas inactivas). `viaje(origen, destino)` prohibe abordar, transbordar o descender en estaciones cerradas, aunque la ruta si transita por ellas y computan en el conteo de paradas recorridas.
8. **Condiciones de viaje:** Si origen y destino coinciden, o alguno esta cerrado o no existe, devuelve `None`. Ante empate en numero de paradas entre viaje directo y transbordo, se prioriza el directo.
9. **Horarios superiores a 24:00 en GTFS:** Las horas tipo `25:10` corresponden a jornadas tecnicas extendidas de la madrugada. Se transforman a minutos acumulados continuos ($25 \times 60 + 10 = 1510$ minutos), evitando saltos y permitiendo comparaciones aritmeticas directas.

---

## R11: Panel de Rendimiento y Metodologia de Medicion

El modulo `panel/medir_rendimiento.py` realiza mediciones sistematicas duplicando el tamano de la red ($N, 2N, 4N, 8N$) y calcula la pendiente en escala logaritmica mediante regresion lineal:

$$\text{Pendiente} = \frac{\Delta \log(\text{Tiempo})}{\Delta \log(N)}$$

- Pendiente $\approx 0.0$: Comportamiento constante $O(1)$ o sublineal $O(\log N)$.
- Pendiente $\approx 1.0$: Comportamiento lineal $O(N)$ o cuasilineal $O(N \log N)$.
- Pendiente $\approx 2.0$: Comportamiento cuadratico $O(N^2)$.

### Resumen de Pendientes Obtenidas

Corrida oficial: `python panel/medir_rendimiento.py --completo`, redes sinteticas de 10.000, 20.000, 40.000 y 80.000 estaciones, 3 repeticiones por medicion (se toma la mediana). Cada medicion corre un lote de 2.000 consultas distintas (300 en las operaciones que cambian la red) y divide por el tamano del lote, porque una sola llamada dura menos de un microsegundo y su tiempo seria ruido del reloj. Para la fila, $P$ = 4.000, 8.000, 16.000 y 32.000 pasajeros. Los tiempos completos quedan en `panel/resultados_rendimiento.json` y la app los grafica en la pestana "Panel Rendimiento".

| Operacion | Responsable | Variable $n$ | Complejidad Teorica | Pendiente Esp. | Pendiente Med. | Diagnostico |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| Carga Red | Juandi / Todos | $N$ = Estaciones | $O(N \log N)$ | 1.0 | 1.26 | Conforme |
| estado (R1) | Sebas | $N$ = Estaciones | $O(1)$ | 0.0 | 0.21 | Conforme |
| autocompletar (R2) | Sebas | $N$ = Abiertas, $k$ | $O(\log N + k)$ | 0.1 | 0.06 | Conforme |
| rango (R3) | Sebas | $N$ = Abiertas, $m$ = 20 | $O(\log N + m)$ | 0.1 | 0.27 | Conforme |
| proximo_bus (R4) | Gabito | $H$ = Horarios parada | $O(\log H) \approx O(1)$ | 0.0 | 0.14 | Conforme |
| ranking (R6) | Gabito | $k$ = 10, $N$ = Abiertas | $O(\log N + k)$ | 0.0 | 0.32 | Conforme |
| agregar_parada (R7) | Juandi | $N$ = Estaciones | $O(1)$ + $O(\log N)$ del ranking | 0.0 | 0.17 | Conforme |
| quitar_parada (R7) | Juandi | $N$ = Estaciones | $O(1)$ + $O(\log N)$ del ranking | 0.0 | 0.16 | Conforme |
| recorrido (R7) | Juandi | $L$ = Paradas ruta | $O(L) \approx O(1)$ | 0.0 | 0.35 | Conforme |
| cerrar (R8) | Sebas | $N$ = Estaciones | $O(\log N)$ | 0.1 | 0.21 | Conforme |
| reabrir (R8) | Sebas | $N$ = Estaciones | $O(\log N)$ | 0.1 | 0.17 | Conforme |
| deshacer (R9) | Juandi | $N$ = Estaciones | $O(1)$ + costo del cambio | 0.0 | 0.16 | Conforme |
| rehacer (R9) | Juandi | $N$ = Estaciones | $O(1)$ + costo del cambio | 0.0 | 0.16 | Conforme |
| simular_fila (R10) | Juandi | $P$ = Pasajeros | $O(P \log P)$ | 1.0 | 1.16 | Conforme |
| simular_fila_pop0 | Juandi | $P$ = Pasajeros | $O(P^2)$ | 2.0 | 2.07 | Penalizacion pop(0) |

### Analisis de Variaciones Observadas
1. **Pendientes entre 0.1 y 0.4 en operaciones $O(1)$ u $O(\log N)$:** no vienen del algoritmo sino de la memoria. La tabla hash mantiene el mismo factor de carga (~0.61) y cadenas promedio de ~1.34 nodos tanto en 10.000 como en 80.000 estaciones, y el AVL sube apenas de ~14 a ~17 niveles. Lo que cambia es que con 80.000 estaciones los nodos ya no caben en la cache del procesador y cada salto de puntero tarda un poco mas. La carga y la fila quedan algo por encima de 1.0 por el factor $\log N$ y por el costo de Python al crear millones de objetos.
2. **Costo amortizado en TablaHash:** Las operaciones de insercion sufren un costo puntual al duplicar el tamano de la tabla cuando se sobrepasa el umbral de carga, manteniendo un promedio $O(1)$ amortizado a lo largo del tiempo.
3. **Evidencia empirica de `pop(0)`:** La implementacion con `Cola` presenta una pendiente de $\approx 1.1$ (lineal con los pasajeros), mientras que `simular_fila_pop0` exhibe una pendiente marcadamente superior debido al costo de reindexacion interna de la lista de Python.

---

## Guia de Sustentacion Tecnica

### P1 (R1 a R3). Busqueda, Autocompletado y Rango
- **Justificacion:** El arbol binario de busqueda mantiene las estaciones ordenadas por construccion. Mientras que una tabla hash requeriria escanear las $N$ estaciones y ordenarlas ($O(N + m \log m)$) para responder un prefijo o un rango, el ABB resuelve la busqueda descendiendo en $O(\log N)$ y recorriendo unicamente los nodos necesarios en orden in-order.

### P2 (R4). Proximo Bus
- **Justificacion:** Como los despachos de cada parada se encuentran previamente ordenados en minutos, la busqueda binaria divide el espacio de busqueda a la mitad en cada paso ($O(\log H)$). Con respecto al tamano de la red $N$, la complejidad es $O(1)$ puesto que los buses que pasan por una estacion no dependen de la cantidad de estaciones existentes en otras zonas de la ciudad.

### P3 (R5). Planear Viaje con Minimas Paradas
> **Respuesta formal de sustentacion:**  
> Se utiliza una tabla hash para indexar hacia atras las estaciones alcanzables desde el destino con sus paradas acumuladas, y un recorrido hacia adelante sobre la lista doblemente enlazada de cada ruta del origen. Esta eleccion resuelve el transbordo en $O(R \cdot L)$ desacoplando las rutas, en comparacion con el costo $O(R^2 \cdot L^2)$ de bucles anidados o el consumo excesivo de memoria de un BFS sobre la red global. Se descarto la busqueda en anchura general porque instanciar y recorrer un grafo de 80.000 estaciones en cada peticion tomaria segundos. La complejidad final es $O(R \cdot L)$, donde $R$ es el numero de rutas por estacion y $L$ las paradas por ruta ($R, L \ll N$), resultando totalmente independiente del total de estaciones de la ciudad.

### P4 (R6 y R8). Ranking y Cierre/Reapertura
- **Justificacion:** Al cerrar una estacion, la regla de negocio exige que no figure en el ranking. En lugar de reordenar las $N$ estaciones en cada cierre o apertura ($O(N \log N)$), los ganchos `_ranking_quitar` y `_ranking_poner` borran o reinsertan su clave `(-buses_dia, nombre)` en el AVL en $O(\log N)$, y `ranking(k)` sigue respondiendo en $O(\log N + k)$. Si se usara un arreglo ordenado, cada cierre correria elementos ($O(N)$); con un heap, sacar el top $k$ costaria $O(k \log N)$ y borrar una estacion del medio no es directo.

### P5 (R7 y R9). Edicion de Rutas y Transacciones
- **Justificacion:** La lista doblemente enlazada permite reasignar punteros en $O(1)$. Para no incurrir en la busqueda lineal de la estacion previa ($O(L)$), cada ruta indexa sus nodos en una tabla hash interna. Para el historial se utilizan pilas LIFO donde `push` y `pop` toman $O(1)$ y permiten revertir mutaciones puntuales sin clonar el estado de la red.

### P6 (R10 y R11). Fila de Abordaje y Panel de Rendimiento
- **Justificacion:** La pendiente en escala logaritmica refleja directamente el exponente de complejidad asintotica. En R10, la cola enlazada mantiene una pendiente de $\approx 1.0$ al ejecutar inserciones y extracciones en tiempo constante. Por el contrario, el uso de `pop(0)` en listas planas obliga a desplazar los bloques contiguos de memoria en cada iteracion, elevando la pendiente hacia $\approx 2.0$ y evidenciando su inviabilidad en entornos de alta demanda.
