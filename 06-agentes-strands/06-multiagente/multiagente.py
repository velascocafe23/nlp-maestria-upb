"""
multiagente.py: patron "agente como herramienta" (agent-as-tool).

Objetivo pedagogico:
A veces un solo agente con muchas responsabilidades se vuelve dificil de
controlar. Una solucion es dividir el trabajo en agentes ESPECIALISTAS y tener
un agente ORQUESTADOR que delega en ellos.

El patron "agente como herramienta" funciona asi:
  - Envuelves a un agente especialista dentro de una funcion decorada con @tool.
  - Esa funcion, cuando se llama, crea el agente especialista, le pasa la
    consulta como texto, y devuelve su respuesta como texto.
  - El agente orquestador recibe esa funcion como una herramienta mas y decide
    cuando delegar.

Puntos importantes (segun la documentacion de Strands):
  - La interfaz entre agentes es TEXTO: el orquestador manda un string y recibe
    un string de vuelta.
  - Cada especialista tiene su propio contexto AISLADO: no ve el historial del
    orquestador.
  - Al crear el especialista dentro de la funcion, empieza "fresco" en cada
    llamada. Ademas usamos callback_handler=None para que el especialista
    trabaje en silencio (sin imprimir su salida intermedia).

Aqui el orquestador es un asistente general. Tiene dos especialistas:
  - Un traductor ingles->espanol.
  - Un experto en resumir textos.

Modelo: gpt-5.6-luna de OpenAI (configurado en comun.py, con la clave del .env).

Ejecutar con:
    python multiagente.py
"""

import sys

from strands import Agent, tool

from comun import crear_modelo, crear_traza_herramientas


# ---------------------------------------------------------------------------
# Especialista 1: traductor, envuelto como herramienta.
# ---------------------------------------------------------------------------
@tool
def traductor_ingles_espanol(texto: str) -> str:
    """Traduce un texto del ingles al espanol.

    Usa esta herramienta cuando el usuario pida traducir contenido en ingles.

    Args:
        texto: el texto en ingles que se debe traducir.
    """
    modelo = crear_modelo()
    especialista = Agent(
        model=modelo,
        system_prompt=(
            "Eres un traductor profesional. Traduce del ingles al espanol "
            "con naturalidad. Devuelve unicamente la traduccion, sin notas."
        ),
        # callback_handler=None: el especialista trabaja en silencio.
        callback_handler=None,
    )
    respuesta = especialista(texto)
    return str(respuesta).strip()


# ---------------------------------------------------------------------------
# Especialista 2: resumidor, envuelto como herramienta.
# ---------------------------------------------------------------------------
@tool
def resumidor(texto: str) -> str:
    """Resume un texto en una o dos frases claras.

    Usa esta herramienta cuando el usuario pida resumir o acortar un texto.

    Args:
        texto: el texto que se debe resumir.
    """
    modelo = crear_modelo()
    especialista = Agent(
        model=modelo,
        system_prompt=(
            "Eres un experto en sintesis. Resume el texto recibido en una o "
            "dos frases, conservando la idea principal. Responde en espanol."
        ),
        callback_handler=None,
    )
    respuesta = especialista(texto)
    return str(respuesta).strip()


def construir_orquestador():
    """Crea el agente orquestador que delega en los especialistas."""
    modelo = crear_modelo()

    system_prompt = (
        "Eres un asistente coordinador. Tienes dos especialistas disponibles "
        "como herramientas: un traductor de ingles a espanol y un resumidor. "
        "Analiza la peticion del usuario y delega en el especialista adecuado. "
        "Si una peticion requiere traducir y luego resumir, usa ambos en el "
        "orden correcto. Responde en espanol."
    )

    # Los especialistas trabajan en silencio (callback_handler=None). El
    # orquestador, en cambio, usa el callback de comun.py con la etiqueta
    # DELEGA: asi vemos en que especialista delega y en que orden, que es el
    # punto central de este modulo. No imprime la respuesta, de eso se encarga
    # main(), para no verla duplicada.
    orquestador = Agent(
        model=modelo,
        system_prompt=system_prompt,
        tools=[traductor_ingles_espanol, resumidor],
        callback_handler=crear_traza_herramientas("DELEGA"),
    )
    return orquestador


def main():
    print("=== Multiagente: agente como herramienta (agent-as-tool) ===")
    print("Un orquestador delega en un traductor y en un resumidor.\n")

    orquestador = construir_orquestador()

    peticion = (
        "Toma este texto en ingles, traducelo al espanol y luego dame un "
        'resumen corto: "Artificial intelligence agents can plan, use tools, '
        'and take actions to achieve goals defined by a user."'
    )
    print("Usuario: " + peticion)

    try:
        respuesta = orquestador(peticion)
    except Exception as error:
        print("\n[error] Fallo la llamada al modelo:")
        print(type(error).__name__ + ": " + str(error))
        sys.exit(1)

    print("\nOrquestador: " + str(respuesta).strip())


if __name__ == "__main__":
    main()
