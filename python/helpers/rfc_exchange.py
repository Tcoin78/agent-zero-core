import os
from python.helpers.dotenv import get_dotenv_value

# Clave usada en .env
KEY_ROOT_PASSWORD = "RFC_ROOT_PASSWORD"

async def get_root_password():
    """
    Devuelve la contraseña root directamente desde la variable de entorno RFC_ROOT_PASSWORD
    o desde el archivo .env si no está presente como variable.
    """
    return _get_root_password()


def _get_root_password():
    """
    Lógica literal y segura para obtener la clave root.
    """
    # 1. Intenta obtener desde variables de entorno
    env_pwd = os.getenv(KEY_ROOT_PASSWORD)
    if env_pwd:
        return env_pwd

    # 2. Si no existe en entorno, intenta desde archivo .env
    dotenv_pwd = get_dotenv_value(KEY_ROOT_PASSWORD)
    if dotenv_pwd:
        return dotenv_pwd

    # 3. Por defecto, cadena vacía si no se encuentra
    return ""
