# tools_propias.py
# Objetivo: aprender a crear herramientas (tools) propias con el decorador
# @tool de Strands. Una herramienta es simplemente una funcion de Python que el
# modelo puede decidir llamar cuando la necesita. A esto se le llama tool
# calling: el modelo no ejecuta el codigo, decide que funcion invocar y con que
# argumentos, y Strands se encarga de ejecutarla y devolverle el resultado.
#
# Claves para que una tool funcione bien:
#   1) El decorador @tool encima de la funcion.
#   2) Un docstring que describa que hace (el modelo lo lee para decidir).
#   3) Type hints en los parametros y en el retorno (ayudan al modelo).
#
# Aqui creamos dos tools: una calculadora y una que devuelve la hora actual.
#
# Como correrlo:
#   python tools_propias.py

from datetime import datetime

from strands import Agent, tool

from comun import crear_modelo, crear_traza_herramientas


@tool
def calculadora(operacion: str, a: float, b: float) -> str:
    """Realiza una operacion aritmetica basica entre dos numeros.

    Args:
        operacion: una de estas palabras: sumar, restar, multiplicar, dividir.
        a: primer numero.
        b: segundo numero.
    Returns:
        Un texto con el resultado, o un mensaje de error si la operacion no es
        valida o si se intenta dividir entre cero.
    """
    if operacion == "sumar":
        return f"El resultado es {a + b}"
    if operacion == "restar":
        return f"El resultado es {a - b}"
    if operacion == "multiplicar":
        return f"El resultado es {a * b}"
    if operacion == "dividir":
        if b == 0:
            return "Error: no se puede dividir entre cero."
        return f"El resultado es {a / b}"
    return (
        "Error: operacion no reconocida. "
        "Usa: sumar, restar, multiplicar o dividir."
    )


@tool
def hora_actual() -> str:
    """Devuelve la fecha y hora actual del sistema.

    Returns:
        Una cadena con la fecha y hora en formato legible (AAAA-MM-DD HH:MM:SS).
    """
    ahora = datetime.now()
    return ahora.strftime("%Y-%m-%d %H:%M:%S")


def main():
    modelo = crear_modelo()

    system_prompt = (
        "Eres un asistente con acceso a dos herramientas: una calculadora y un "
        "reloj. Cuando el usuario pida un calculo o pregunte la hora, usa la "
        "herramienta adecuada en lugar de responder de memoria."
    )

    # crear_traza_herramientas (de comun.py) nos da un callback que anuncia cada
    # herramienta que el modelo decide usar, sin imprimir la respuesta. Asi vemos
    # el tool calling en accion Y leemos la respuesta una sola vez, la que
    # imprime este script mas abajo.
    agente = Agent(
        model=modelo,
        system_prompt=system_prompt,
        tools=[calculadora, hora_actual],
        callback_handler=crear_traza_herramientas(),
    )

    # Hacemos dos preguntas, una por cada herramienta, para ver el tool calling.
    for pregunta in [
        "Cuanto es 15 multiplicado por 12?",
        "Que hora es en este momento?",
    ]:
        print("=" * 70)
        print("Pregunta:", pregunta)
        respuesta = agente(pregunta)
        print("\nRespuesta del agente:")
        print(respuesta)
        print()


if __name__ == "__main__":
    main()
