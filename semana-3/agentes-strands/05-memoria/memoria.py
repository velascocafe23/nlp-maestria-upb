"""
memoria.py: memoria de conversacion (contexto entre turnos).

Objetivo pedagogico:
Un agente util recuerda lo que se dijo antes. A esto le llamamos MEMORIA de
conversacion. En Strands, un mismo objeto Agent MANTIENE el historial de la
conversacion automaticamente: cada vez que lo llamas, agrega tu mensaje y su
respuesta a una lista interna de mensajes (agente.messages).

Idea clave:
  - Si reutilizas el MISMO agente en varios turnos, recuerda el contexto.
  - Si crearas un agente NUEVO en cada turno, empezaria "en blanco" cada vez.

En este script simulamos una conversacion de varios turnos con el mismo agente
para demostrar que recuerda datos mencionados antes (por ejemplo, el nombre del
usuario y su tema de interes). Al final imprimimos cuantos mensajes hay en el
historial para que el estudiante vea la memoria crecer.

Modelo: gpt-5.6-luna de OpenAI (configurado en comun.py, con la clave del .env).

Ejecutar con:
    python memoria.py
"""

import sys

from strands import Agent

from comun import crear_modelo


def construir_agente():
    """Crea un unico agente que reutilizamos en cada turno."""
    modelo = crear_modelo()

    system_prompt = (
        "Eres un tutor amable. Recuerda los datos que el estudiante te da "
        "durante la conversacion y usalos en tus respuestas. Responde en "
        "espanol y de forma breve."
    )

    # Este agente se crea UNA sola vez. Su historial vivira entre turnos.
    # callback_handler=None apaga la impresion automatica de Strands para que
    # cada turno se lea una sola vez (la que imprime este script).
    agente = Agent(
        model=modelo,
        system_prompt=system_prompt,
        callback_handler=None,
    )
    return agente


def main():
    print("=== Memoria de conversacion (mismo agente, varios turnos) ===\n")

    agente = construir_agente()

    # Turnos de la conversacion. Fijate que el turno 1 da informacion que el
    # agente debera recordar en los turnos 2 y 3.
    turnos = [
        "Hola, me llamo Ana y estoy estudiando redes neuronales.",
        "Puedes recordarme como me llamo?",
        "Recomiendame un primer paso para el tema que te dije que estudio.",
    ]

    for numero, mensaje in enumerate(turnos, start=1):
        print("Turno " + str(numero))
        print("Usuario: " + mensaje)
        try:
            respuesta = agente(mensaje)
        except Exception as error:
            print("[error] Fallo la llamada al modelo:")
            print(type(error).__name__ + ": " + str(error))
            sys.exit(1)
        print("Agente: " + str(respuesta).strip() + "\n")

    # El historial de mensajes vive dentro del agente.
    # Cada turno agrega, al menos, el mensaje del usuario y la respuesta.
    total = len(agente.messages)
    print("Mensajes guardados en el historial del agente: " + str(total))
    print("(Por eso el agente pudo recordar el nombre y el tema de Ana.)")


if __name__ == "__main__":
    main()
