"""
multiples_tools.py: un agente con varias herramientas.

Objetivo pedagogico:
Cuando un agente tiene VARIAS herramientas, el modelo debe DECIDIR cual usar
(o si usar varias) segun la pregunta. El estudiante no programa esa decision:
la toma el modelo, guiado por:

  - El nombre de cada herramienta.
  - El docstring (descripcion) de cada herramienta.
  - Los type hints de los parametros.

Esto muestra el poder del tool calling: das varias capacidades al agente y el
elige la adecuada para cada situacion. Un buen docstring es clave, porque es lo
que el modelo lee para decidir.

Aqui damos al agente cuatro herramientas: convertir moneda, convertir
temperatura, contar palabras y calcular el area de un rectangulo. Luego le
hacemos preguntas variadas para ver como elige.

Modelo: gpt-5.6-luna de OpenAI (configurado en comun.py, con la clave del .env).

Ejecutar con:
    python multiples_tools.py
"""

import sys

from strands import Agent, tool

from comun import crear_modelo, crear_traza_herramientas


@tool
def convertir_moneda(monto: float, tasa: float) -> float:
    """Convierte un monto de dinero multiplicandolo por una tasa de cambio.

    Args:
        monto: cantidad en la moneda de origen.
        tasa: cuantas unidades de la moneda destino equivalen a una de origen.
    """
    return monto * tasa


@tool
def celsius_a_fahrenheit(celsius: float) -> float:
    """Convierte una temperatura de grados Celsius a grados Fahrenheit.

    Args:
        celsius: temperatura en grados Celsius.
    """
    return (celsius * 9.0 / 5.0) + 32.0


@tool
def contar_palabras(texto: str) -> int:
    """Cuenta cuantas palabras tiene un texto.

    Args:
        texto: cadena de texto a analizar.
    """
    return len(texto.split())


@tool
def area_rectangulo(base: float, altura: float) -> float:
    """Calcula el area de un rectangulo a partir de su base y su altura.

    Args:
        base: longitud de la base.
        altura: longitud de la altura.
    """
    return base * altura


def construir_agente():
    """Crea el agente con cuatro herramientas distintas."""
    modelo = crear_modelo()

    system_prompt = (
        "Eres un asistente con varias herramientas. Analiza cada pregunta y "
        "elige la herramienta correcta. Si una pregunta no necesita ninguna "
        "herramienta, responde directamente. Responde en espanol y breve."
    )

    # El callback de comun.py anuncia que herramienta elige el modelo en cada
    # pregunta. Es la prueba visible de que la decision la toma el modelo y no
    # nuestro codigo. No imprime la respuesta, de eso se encarga main().
    agente = Agent(
        model=modelo,
        system_prompt=system_prompt,
        tools=[
            convertir_moneda,
            celsius_a_fahrenheit,
            contar_palabras,
            area_rectangulo,
        ],
        callback_handler=crear_traza_herramientas(),
    )
    return agente


def main():
    print("=== Agente con multiples herramientas ===")
    print("El modelo decide cual herramienta usar en cada caso.\n")

    agente = construir_agente()

    preguntas = [
        "Convierte 100 dolares a pesos si la tasa es 4000.",
        "Cuantos grados Fahrenheit son 37 grados Celsius?",
        'Cuantas palabras tiene la frase "los agentes de IA son utiles"?',
        "Cual es el area de un rectangulo de base 8 y altura 3?",
    ]

    for pregunta in preguntas:
        print("Usuario: " + pregunta)
        try:
            # Mientras corre, el callback imprime la linea [HERRAMIENTA] con la
            # tool que eligio el modelo. Luego imprimimos la respuesta final.
            respuesta = agente(pregunta)
        except Exception as error:
            print("[error] Fallo la llamada al modelo:")
            print(type(error).__name__ + ": " + str(error))
            sys.exit(1)
        print("Agente: " + str(respuesta).strip() + "\n")


if __name__ == "__main__":
    main()
