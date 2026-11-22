"""Servidor web principal para el Planeador de Viajes de TransMilenio.

Llama exclusivamente al motor (sin reglas de negocio en el front)
y mantiene la instancia de Red en memoria para evitar recargas.
Arranque con un solo comando: python app/main.py
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Agregar raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor import Red, simular_fila
from panel.medir_rendimiento import cargar_o_ejecutar_resultados

# Instancia global en memoria de la red
CARPETA_DATOS = "datos"
print("Iniciando TransMilenio App...")
print(f"Cargando red desde '{CARPETA_DATOS}'...")
red_global = Red(CARPETA_DATOS)
print("Red cargada exitosamente.")


class TransmilenioHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Deshabilitar cache para APIs y desarrollo
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_GET(self):
        url_parsed = urlparse(self.path)
        ruta = url_parsed.path
        params = parse_qs(url_parsed.query)

        # 1. Rutas de la API REST
        if ruta.startswith("/api/"):
            self.manejar_api_get(ruta, params)
            return

        # 2. Servir la SPA principal
        if ruta == "/" or ruta == "/index.html":
            ruta_html = os.path.join(os.path.dirname(__file__), "index.html")
            if os.path.exists(ruta_html):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(ruta_html, "rb") as f:
                    self.wfile.write(f.read())
                return

        # Archivos estáticos por defecto
        super().do_GET()

    def do_POST(self):
        url_parsed = urlparse(self.path)
        ruta = url_parsed.path

        longitud = int(self.headers.get("Content-Length", 0))
        cuerpo = self.rfile.read(longitud).decode("utf-8") if longitud > 0 else "{}"
        try:
            datos = json.loads(cuerpo)
        except Exception:
            datos = {}

        if ruta == "/api/agregar_parada":
            r = datos.get("ruta", "")
            nueva = datos.get("nueva", "")
            despues = datos.get("despues_de", "")
            exito = red_global.agregar_parada(r, nueva, despues)
            self._responder_json({"exito": bool(exito)})
            return

        if ruta == "/api/quitar_parada":
            r = datos.get("ruta", "")
            est = datos.get("estacion", "")
            exito = red_global.quitar_parada(r, est)
            self._responder_json({"exito": bool(exito)})
            return

        if ruta == "/api/simular_fila":
            llegadas = datos.get("llegadas", [])
            frecuencia = int(datos.get("frecuencia", 60))
            capacidad = int(datos.get("capacidad", 10))
            salidas = simular_fila(llegadas, frecuencia, capacidad)
            self._responder_json({"salidas": salidas})
            return

        self.send_response(404)
        self.end_headers()

    def manejar_api_get(self, ruta, params):
        def _p(nombre, default=""):
            val = params.get(nombre, [default])[0]
            return val

        if ruta == "/api/estaciones":
            claves = red_global.estaciones.claves()
            claves.sort()
            self._responder_json(claves)
            return

        if ruta == "/api/rutas":
            claves = red_global.rutas.claves()
            claves.sort()
            self._responder_json(claves)
            return

        if ruta == "/api/estado":
            nom = _p("nombre")
            res = red_global.estado(nom)  # toda la regla vive en el motor (R1)
            self._responder_json({"estado": res})
            return

        if ruta == "/api/autocompletar":
            pref = _p("prefijo")
            k = int(_p("k", "5"))
            res = red_global.autocompletar(pref, k)
            if res is None:
                res = []
            self._responder_json(res)
            return

        if ruta == "/api/rango":
            desde = _p("desde")
            hasta = _p("hasta")
            res = red_global.rango(desde, hasta)
            if res is None:
                res = []
            self._responder_json(res)
            return

        if ruta == "/api/proximo_bus":
            est = _p("estacion")
            r = _p("ruta")
            hora = _p("hora")
            res = red_global.proximo_bus(est, r, hora)
            self._responder_json({"proximo_bus": res})
            return

        if ruta == "/api/viaje":
            orig = _p("origen")
            dest = _p("destino")
            res = red_global.viaje(orig, dest)
            self._responder_json({"viaje": res})
            return

        if ruta == "/api/ranking":
            k = int(_p("k", "10"))
            res = red_global.ranking(k)
            if res is None:
                res = []
            self._responder_json(res)
            return

        if ruta == "/api/recorrido":
            r = _p("ruta")
            al_reves = _p("al_reves", "false").lower() == "true"
            res = red_global.recorrido(r, al_reves=al_reves)
            self._responder_json(res)
            return

        if ruta == "/api/cerrar":
            nom = _p("nombre")
            res = red_global.cerrar(nom)
            self._responder_json({"cambio": bool(res)})
            return

        if ruta == "/api/reabrir":
            nom = _p("nombre")
            res = red_global.reabrir(nom)
            self._responder_json({"cambio": bool(res)})
            return

        if ruta == "/api/deshacer":
            res = red_global.deshacer()
            self._responder_json({"exito": bool(res)})
            return

        if ruta == "/api/rehacer":
            res = red_global.rehacer()
            self._responder_json({"exito": bool(res)})
            return

        if ruta == "/api/rendimiento":
            datos_bench = cargar_o_ejecutar_resultados()
            self._responder_json(datos_bench)
            return

        self.send_response(404)
        self.end_headers()

    def _responder_json(self, objeto):
        contenido = json.dumps(objeto, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)


def iniciar_servidor(puerto=8000):
    servidor = None
    puerto_actual = puerto
    while puerto_actual < puerto + 20:
        try:
            servidor = HTTPServer(("localhost", puerto_actual), TransmilenioHandler)
            break
        except OSError:
            puerto_actual += 1

    if servidor is None:
        print("No se pudo iniciar el servidor en el rango de puertos.")
        sys.exit(1)

    url = f"http://localhost:{puerto_actual}"
    print(f"\n=======================================================")
    print(f"  App TransMilenio lista y corriendo en:")
    print(f"  --> {url}")
    print(f"  Presiona Ctrl+C para detener el servidor.")
    print(f"=======================================================\n")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    iniciar_servidor(8000)
