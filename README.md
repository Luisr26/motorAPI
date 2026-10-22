# motor-api

API + página web para controlar la velocidad y dirección de un motor DC conectado a un ESP32 con driver L298N.

## Archivos

| Archivo | Qué hace |
|---|---|
| `main.py` | La API (FastAPI). Guarda el estado del motor en memoria y sirve la página web. |
| `static/index.html` | La página web: slider, botones y el indicador de conexión. HTML + CSS + JS sin librerías. |
| `requirements.txt` | Librerías de Python que Render instala. |
| `.gitignore` | Lo que NO se sube a GitHub (venv, cachés, `.env`, sketches con credenciales). |

## Endpoints

| Método | Ruta | Quién lo usa | Qué hace |
|---|---|---|---|
| GET | `/` | Navegador | Página de control |
| GET | `/motor/` | ESP32 | Devuelve `{"velocidad", "direccion"}` y registra el contacto |
| PUT | `/motor/` | Web | Cambia el estado. Valida velocidad 0-100 y dirección `adelante\|atras\|stop` |
| GET | `/estado/` | Web | Estado + `conectado` + `segundos_desde_contacto` |
| GET | `/docs` | Tú | Documentación interactiva de FastAPI |

## Correr en local (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Abre http://localhost:8000

## Render

- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
