"""
env_config.py
-------------
Lee el archivo .env de la raíz del proyecto y expone
las variables de entorno como constantes reutilizables
en todos los controllers.

Uso:
    from env_config import ENV

    serial_num = ENV["LABJACK_SERIAL"]
    com_port   = ENV["ARDUINO_COM_PORT"]
    user       = ENV["SESSION_USER"]
    password   = ENV["SESSION_PASSWORD"]
"""

import os

_ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

# Valores predeterminados (se sobreescriben con lo que haya en .env)
_DEFAULTS = {
    "LABJACK_SERIAL":   "470026166",
    "ARDUINO_COM_PORT": "COM6",
    "SESSION_USER":     "admin",
    "SESSION_PASSWORD": "1234",
}


def _load_env(path: str) -> dict:
    """Lee el archivo .env y devuelve un dict con las variables."""
    result = dict(_DEFAULTS)
    if not os.path.exists(path):
        return result
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def reload() -> None:
    """
    Recarga el .env en tiempo de ejecución.
    Llama a esto después de guardar cambios en Settings.
    """
    global ENV
    ENV = _load_env(_ENV_FILE)


# Carga inicial
ENV: dict = _load_env(_ENV_FILE)
