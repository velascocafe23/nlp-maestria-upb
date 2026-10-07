# agent_loop.py
# Objetivo: hacer visible el ciclo interno del agente (observar, pensar,
# actuar). Un agente no solo responde: recibe una entrada (observa), el modelo
# razona que hacer (piensa) y, si tiene herramientas, decide llamarlas (actua),
# repitiendo el ciclo hasta tener una respuesta final.
#
# Para "ver" ese ciclo usamos dos mecanismos que ofrece Strands:
#   1) El logging de la libreria (subimos el nivel a DEBUG para ver trazas).
#   2) Un callback_handler propio que imprime los eventos que emite el agente.
#
# Le damos al agente una herramienta simple (una calculadora) para que tenga
# un motivo real para "actuar" y asi el ciclo se note mas.
#
# Como correrlo:
#   python agent_loop.py

import logging

from strands import Agent, tool

from comun import crear_modelo

# Subimos el nivel de logging de Strands para ver las trazas internas.
# Cambia a logging.INFO si el detalle de DEBUG te resulta demasiado ruidoso.
logging.basicConfig(
    level=logging.DEBUG,
    format="%(name)s %(levelname)s | %(message)s",
)
logging.getLogger("strands").setLevel(logging.DEBUG)


@tool
def sumar(a: float, b: float) -> float:
    """Suma dos numeros y devuelve el resultado.

    Args:
        a: primer numero.
        b: segundo numero.
    Returns:
        La suma de a y b.
    """
    return a + b


# Guardamos el id de la ultima herramienta anunciada. Hace falta porque el
# evento current_tool_use llega MUCHAS veces para una misma llamada: Strands lo
# reemite en cada fragmento mientras se van armando los argumentos. Sin este
# control, veriamos la linea [ACTUAR] repetida diez veces para una sola decision.
_ultima_tool_anunciada = None


def traza(**evento):
    """Callback que Strands invoca durante el ciclo del agente.

    Recibe eventos del agente (texto que se va generando, decisiones de uso de
    herramientas, etc.). Aqui los imprimimos con una etiqueta para distinguir
    las fases del ciclo. La firma usa **evento porque los eventos llegan como
    argumentos con nombre y no siempre traen las mismas claves.
    """
    global _ultima_tool_anunciada

    # Fragmentos de texto que el modelo va produciendo (fase de pensar/responder).
    if "data" in evento:
        print(f"[PENSAR/RESPONDER] {evento['data']}", end="")

    # El modelo decidio usar una herramienta (fase de actuar).
    if evento.get("current_tool_use"):
        herramienta = evento["current_tool_use"]
        # toolUseId identifica una llamada concreta. Solo anunciamos cuando
        # cambia, es decir, una vez por decision real del modelo.
        tool_id = herramienta.get("toolUseId")
        if tool_id != _ultima_tool_anunciada:
            _ultima_tool_anunciada = tool_id
            nombre = herramienta.get("name", "desconocida")
            print(f"\n[ACTUAR] El agente decide usar la herramienta: {nombre}")


def main():
    modelo = crear_modelo()

    system_prompt = (
        "Eres un asistente que resuelve operaciones aritmeticas. Cuando el "
        "usuario pida una suma, usa la herramienta sumar en lugar de calcular "
        "de memoria."
    )

    # Conectamos nuestro callback con callback_handler para observar el ciclo.
    agente = Agent(
        model=modelo,
        system_prompt=system_prompt,
        tools=[sumar],
        callback_handler=traza,
    )

    pregunta = "Cuanto es 128 mas 47? Usa la herramienta y explica el resultado."
    print("=" * 70)
    print("Pregunta:", pregunta)
    print("Observa abajo las trazas del ciclo (DEBUG) y las fases marcadas.")
    print("=" * 70)

    respuesta = agente(pregunta)

    print("\n" + "=" * 70)
    print("Respuesta final del agente:")
    print(respuesta)


if __name__ == "__main__":
    main()
