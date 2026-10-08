# primer_agente.py
# Objetivo: mostrar los tres pilares de un agente con Strands Agents:
#   1) El modelo (el "cerebro", aqui gpt-5.6-luna via el proveedor de OpenAI).
#   2) El system prompt (las instrucciones que definen su rol y su tono).
#   3) El Agent (la pieza que une modelo mas instrucciones y ejecuta el ciclo).
#
# Este script hace una sola interaccion (no hay bucle) para centrarse en como
# se arma un agente basico y como se le hace una pregunta.
#
# Como correrlo:
#   python primer_agente.py

from strands import Agent

from comun import crear_modelo


def main():
    # Pilar 1: el modelo. crear_modelo vive en comun.py y devuelve gpt-5.6-luna
    # ya configurado con la clave del archivo .env.
    modelo = crear_modelo()

    # Pilar 2: el system prompt. Define quien es el agente y como debe responder.
    system_prompt = (
        "Eres un asistente educativo de un curso de procesamiento de lenguaje "
        "natural. Explicas conceptos tecnicos en espanol, de forma clara y "
        "breve, con ejemplos sencillos cuando ayudan a entender."
    )

    # Pilar 3: el Agent. Une el modelo con el system prompt.
    # callback_handler=None apaga la impresion automatica de Strands (que va
    # mostrando la respuesta mientras se genera). Asi la unica salida es la que
    # imprime este script mas abajo y no vemos la respuesta dos veces.
    agente = Agent(
        model=modelo,
        system_prompt=system_prompt,
        callback_handler=None,
    )

    # Una sola interaccion: le pasamos una pregunta y el agente responde.
    pregunta = "En una frase, que es un agente de IA?"
    print("Pregunta:", pregunta)

    respuesta = agente(pregunta)

    # El objeto de respuesta se puede imprimir directamente como texto.
    print("\nRespuesta del agente:")
    print(respuesta)


if __name__ == "__main__":
    main()
