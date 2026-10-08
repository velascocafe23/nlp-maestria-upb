# comun.py
# Modulo de apoyo compartido por todos los scripts del laboratorio.
# Centraliza dos cosas: la carga de la clave de OpenAI desde el archivo .env
# y la creacion del modelo, para no repetir ese codigo en cada script.

import os

from dotenv import find_dotenv, load_dotenv
from strands.models.openai_responses import OpenAIResponsesModel

# Modelo base del laboratorio. Se deja como constante para poder cambiarlo
# en un solo lugar si hiciera falta.
MODEL_ID = "gpt-5.6-luna"


def cargar_api_key():
    """Carga las variables del archivo .env y devuelve la clave de OpenAI.

    Busca un archivo .env con la linea:
        OPENAI_API_KEY=sk-...

    La busqueda empieza en la carpeta desde la que ejecutas el script y sube
    por las carpetas padre hasta encontrarlo. Por eso basta con UN solo .env
    en la raiz del laboratorio: sirve para todos los modulos. Si prefieres,
    tambien puedes poner un .env dentro de la carpeta del modulo y ese tendra
    prioridad, porque se encuentra primero.

    Corta con un mensaje claro si la clave no esta definida.
    """
    # find_dotenv(usecwd=True) devuelve la ruta del primer .env encontrado
    # subiendo desde el directorio de trabajo actual (cadena vacia si no hay).
    ruta_env = find_dotenv(usecwd=True)
    load_dotenv(ruta_env)  # vuelca las variables del .env en el entorno

    clave = os.environ.get("OPENAI_API_KEY")
    if not clave:
        raise SystemExit(
            "Falta OPENAI_API_KEY.\n"
            "Crea un archivo .env en la raiz del laboratorio (puedes copiar "
            ".env.example) con la linea: OPENAI_API_KEY=tu_clave"
        )
    return clave


def crear_traza_herramientas(etiqueta="HERRAMIENTA"):
    """Devuelve un callback_handler que SOLO anuncia las herramientas usadas.

    Por que existe esta funcion: Strands trae un callback_handler por defecto
    que hace dos cosas a la vez, imprimir la respuesta mientras se genera Y
    marcar cada llamada a herramienta con "Tool #N". Eso deja dos opciones
    malas: si el script imprime la respuesta al final, se ve duplicada; y si la
    apagamos con callback_handler=None, dejamos de ver que herramienta eligio el
    modelo, que es justo lo que queremos ensenar.

    Este callback resuelve las dos cosas: anuncia la herramienta y NO imprime el
    texto de la respuesta, asi el script la imprime una sola vez.

    Detalle importante: Strands reemite el evento current_tool_use en cada
    fragmento mientras arma los argumentos de la llamada. Si imprimieramos cada
    evento, veriamos la misma linea repetida diez veces. Por eso llevamos la
    cuenta de los toolUseId ya anunciados y avisamos una vez por llamada real.

    Args:
        etiqueta: texto que aparece entre corchetes en cada anuncio.
    Returns:
        Una funcion lista para pasar como callback_handler a un Agent.
    """
    anunciadas = set()

    def traza(**evento):
        herramienta = evento.get("current_tool_use")
        if not herramienta:
            return
        tool_id = herramienta.get("toolUseId")
        if tool_id in anunciadas:
            return
        anunciadas.add(tool_id)
        nombre = herramienta.get("name", "desconocida")
        print(f"  [{etiqueta}] el modelo decide usar: {nombre}")

    return traza


def crear_modelo():
    """Crea y devuelve el modelo de OpenAI listo para usar con un Agent.

    Por que OpenAIResponsesModel y no OpenAIModel:
    Strands trae dos proveedores de OpenAI. OpenAIModel habla con el endpoint
    clasico /v1/chat/completions, y OpenAIResponsesModel con /v1/responses, que
    es el que OpenAI recomienda para los modelos de razonamiento.

    Con gpt-5.6-luna la diferencia no es de estilo, es bloqueante: si usas
    OpenAIModel y le das herramientas al agente, la API responde con un error
    400 que dice "Function tools with reasoning_effort are not supported for
    gpt-5.6-luna in /v1/chat/completions". O sea, por chat/completions habria
    que apagar el razonamiento (reasoning_effort='none') para poder usar tools.
    Como el laboratorio se basa justamente en tool calling, usamos
    /v1/responses y conservamos el razonamiento. Lo mismo aplica a los otros
    modelos de la familia gpt-5.6 (sol, terra).

    Nota sobre temperature: es un modelo de razonamiento y no acepta un valor de
    temperature distinto al predeterminado, por eso NO pasamos temperature. Si
    quieres controlar el esfuerzo de razonamiento, puedes pasar
    params={"reasoning_effort": "low" | "medium" | "high"}.
    """
    clave = cargar_api_key()
    return OpenAIResponsesModel(
        client_args={"api_key": clave},
        model_id=MODEL_ID,
    )
