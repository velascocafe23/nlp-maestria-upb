"""
asistente_cli.py: asistente de terminal interactivo con Strands Agents.

Objetivo pedagogico:
Este ejemplo replica el patron del workshop oficial (recipe-bot-cli): un agente
que corre en un bucle interactivo desde la terminal. A diferencia de los
scripts 00 a 07 (que hacen una o pocas interacciones y terminan), aqui el
estudiante conversa con el agente de forma continua hasta escribir 'salir'.

Muestra tres ideas juntas:
  1. Un agente con system prompt (su rol y su tono).
  2. Un par de herramientas propias con @tool (el modelo decide cuando usarlas).
  3. Un bucle de conversacion que mantiene el contexto entre turnos, porque
     reutilizamos el MISMO objeto Agent en cada vuelta del bucle.

Modelo: gpt-5.6-luna de OpenAI (configurado en comun.py, con la clave del .env).

Como correrlo:
    cd 01-primer-agente/agente-cli
    pip install -r requirements.txt
    (crea un archivo .env con OPENAI_API_KEY, puedes copiar el de la raiz)
    python asistente_cli.py
"""

import datetime
import sys

from strands import Agent, tool

from comun import crear_modelo, crear_traza_herramientas


@tool
def calculadora(operacion: str) -> str:
    """Evalua una operacion aritmetica simple y devuelve el resultado.

    Usa esta herramienta cuando el usuario pida un calculo numerico.

    Args:
        operacion: expresion aritmetica con numeros y los signos + - * / ( ).
            Ejemplos: "3 * (4 + 5)", "128 / 4".
    """
    # Por seguridad solo permitimos digitos, espacios y operadores basicos.
    permitidos = set("0123456789+-*/(). ")
    if not operacion or set(operacion) - permitidos:
        return "Operacion no valida: usa solo numeros y los signos + - * / ( )."
    try:
        # eval acotado: sin acceso a variables ni funciones del entorno.
        resultado = eval(operacion, {"__builtins__": {}}, {})
    except Exception as error:
        return "No pude calcular la operacion: " + str(error)
    return str(resultado)


@tool
def hora_actual() -> str:
    """Devuelve la fecha y la hora actuales del sistema.

    Usa esta herramienta cuando el usuario pregunte por la fecha o la hora.
    """
    ahora = datetime.datetime.now()
    return ahora.strftime("%Y-%m-%d %H:%M:%S")


def construir_agente():
    """Crea el agente asistente con sus dos herramientas."""
    modelo = crear_modelo()

    system_prompt = (
        "Eres un asistente de un curso de procesamiento de lenguaje natural. "
        "Respondes en espanol, de forma clara y breve. Tienes dos herramientas: "
        "una calculadora y una que da la hora actual. Usalas cuando la pregunta "
        "lo requiera. Si la pregunta no necesita herramientas, responde directo."
    )

    # El callback de comun.py anuncia que herramienta elige el modelo en cada
    # turno, sin imprimir la respuesta. Asi la conversacion se lee limpia (una
    # sola linea "Asistente >" por turno) y ademas se ve el tool calling.
    return Agent(
        model=modelo,
        system_prompt=system_prompt,
        tools=[calculadora, hora_actual],
        callback_handler=crear_traza_herramientas(),
    )


def main():
    print("\nAsistente del curso. Escribe tu pregunta o 'salir' para terminar.\n")

    try:
        agente = construir_agente()
    except SystemExit as salida:
        # crear_modelo corta con un mensaje claro si falta la clave.
        print(salida)
        sys.exit(1)

    # Reutilizamos el MISMO agente en cada vuelta: asi recuerda el contexto.
    while True:
        try:
            entrada = input("Tu > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break

        if entrada.lower() in ("salir", "exit", "quit"):
            print("Hasta luego.")
            break

        if not entrada:
            continue

        try:
            respuesta = agente(entrada)
        except Exception as error:
            print("[error] Fallo la llamada al modelo:")
            print(type(error).__name__ + ": " + str(error))
            continue

        print("\nAsistente > " + str(respuesta).strip() + "\n")


if __name__ == "__main__":
    main()
