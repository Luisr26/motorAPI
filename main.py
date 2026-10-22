"""
motor-api: API para controlar un motor DC conectado a un ESP32 + L298N.

- El ESP32 consulta GET /motor/ cada segundo para saber qué hacer.
- La página web (GET /) cambia el estado con PUT /motor/ y muestra
  si el ESP32 está conectado con GET /estado/.

El estado vive en memoria: si Render reinicia el servicio, vuelve a "stop".
"""

import threading
import time
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Si el ESP32 no consulta en este tiempo, la web lo muestra como desconectado.
SEGUNDOS_CONECTADO = 5

app = FastAPI(title="motor-api", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "PUT"],
    allow_headers=["*"],
)


class EstadoMotor(BaseModel):
    """Lo que la web envía y lo que el ESP32 recibe."""

    velocidad: int = Field(ge=0, le=100, description="Porcentaje 0-100")
    direccion: Literal["adelante", "atras", "stop"]


class Medicion(BaseModel):
    """Lo que muestra el LCD del medidor: voltaje, corriente y potencia."""

    voltaje_v: float
    corriente_ma: float
    potencia_w: float


class EstadoCompleto(EstadoMotor):
    """Lo que ve la web: el estado, la conexión del ESP32 y la última medición."""

    conectado: bool
    segundos_desde_contacto: Optional[float]
    medicion: Optional[Medicion]


# Estado en memoria. El lock evita que dos peticiones a la vez lo dejen a medias.
_lock = threading.Lock()
_estado = EstadoMotor(velocidad=0, direccion="stop")
_ultimo_contacto: Optional[float] = None  # time.monotonic() del último GET del ESP32
_medicion: Optional[Medicion] = None      # última medición que mandó el ESP32

INDEX_HTML = Path(__file__).parent / "static" / "index.html"


@app.get("/", include_in_schema=False)
def pagina_web() -> FileResponse:
    return FileResponse(INDEX_HTML)


@app.get("/motor/", response_model=EstadoMotor)
def leer_motor(
    v: Optional[float] = None,
    i: Optional[float] = None,
    p: Optional[float] = None,
) -> EstadoMotor:
    """
    Lo usa el ESP32. Devuelve el estado deseado y anota la hora del contacto.

    Si el ESP32 manda ?v=..&i=..&p=.. (voltaje V, corriente mA, potencia W),
    se guardan para mostrarlos en la web. Así no hace falta una petición extra.
    """
    global _ultimo_contacto, _medicion
    with _lock:
        _ultimo_contacto = time.monotonic()
        if v is not None and i is not None and p is not None:
            _medicion = Medicion(voltaje_v=v, corriente_ma=i, potencia_w=p)
        return _estado


@app.put("/motor/", response_model=EstadoMotor)
def cambiar_motor(nuevo: EstadoMotor) -> EstadoMotor:
    """Lo usa la web. Pydantic ya validó el rango y la dirección (si no, responde 422)."""
    global _estado
    with _lock:
        _estado = nuevo
        return _estado


@app.get("/estado/", response_model=EstadoCompleto)
def leer_estado() -> EstadoCompleto:
    """Lo usa la web para mostrar el estado y si el ESP32 está conectado."""
    with _lock:
        segundos = None if _ultimo_contacto is None else time.monotonic() - _ultimo_contacto
        return EstadoCompleto(
            **_estado.model_dump(),
            conectado=segundos is not None and segundos < SEGUNDOS_CONECTADO,
            segundos_desde_contacto=None if segundos is None else round(segundos, 1),
            medicion=_medicion,
        )
