# setup.py
# Objetivo: verificar que el entorno del laboratorio esta listo antes de
# construir agentes. Comprueba, en orden:
#   1) Que las librerias necesarias esten instaladas (imports).
#   2) Que exista la clave OPENAI_API_KEY en el archivo .env de la raiz.
#   3) Que se pueda crear el modelo gpt-5.6-luna y hacer una llamada real.
#
# Como correrlo, desde esta carpeta:
#   python setup.py
#
# Si algo falla, el script lo dice con un mensaje claro y termina.

import sys


def paso(numero, descripcion):
    """Imprime un encabezado de paso para seguir el avance de la verificacion."""
    print(f"\n[{numero}] {descripcion}")


def main():
    print("Verificacion del entorno (Strands Agents + gpt-5.6-luna de OpenAI)")

    # Paso 1: verificar que los imports funcionan. Se hacen aqui dentro (y no
    # arriba del archivo) para poder dar un mensaje de ayuda si falta instalar.
    paso(1, "Verificando librerias instaladas")
    try:
        import dotenv  # noqa: F401  (solo comprobamos que exista)
        from strands import Agent  # noqa: F401
        from strands.models.openai_responses import OpenAIResponsesModel  # noqa: F401
    except ImportError as error:
        print("  Falta al menos una libreria:", error)
        print("  Solucion: pip install -r ../requirements.txt")
        print("  Ojo: el extra [openai] es obligatorio (ya viene en el archivo);")
        print("  es el que instala la libreria openai que usa el proveedor.")
        sys.exit(1)
    print("  OK: strands-agents (con el extra openai) y python-dotenv disponibles.")

    # Paso 2: verificar que la clave este definida en el archivo .env.
    # cargar_api_key vive en comun.py y corta con un mensaje claro si no esta.
    paso(2, "Verificando OPENAI_API_KEY en el archivo .env")
    try:
        from comun import cargar_api_key

        clave = cargar_api_key()
    except SystemExit as salida:
        # cargar_api_key ya explico el problema; lo repetimos y salimos.
        print(" ", salida)
        sys.exit(1)
    # No imprimimos la clave completa por seguridad, solo una pista.
    print(f"  OK: clave encontrada (empieza por {clave[:6]}...).")

    # Paso 3: crear el modelo y hacer una llamada minima a gpt-5.6-luna.
    paso(3, "Probando conexion con gpt-5.6-luna (llamada minima)")
    try:
        from comun import crear_modelo
        from strands import Agent

        modelo = crear_modelo()
        # callback_handler=None apaga la impresion automatica de Strands, para
        # que la unica salida sea la que imprime este script (sin duplicados).
        agente = Agent(
            model=modelo,
            system_prompt="Responde en espanol, de forma muy breve.",
            callback_handler=None,
        )
        respuesta = agente("Responde unicamente con la palabra: listo")
        print("  Respuesta del modelo:", str(respuesta).strip())
    except Exception as error:
        print("  Fallo la llamada al modelo:", error)
        print("  Revisa que la clave sea valida y que tengas acceso al modelo")
        print("  gpt-5.6-luna (puedes cambiarlo en MODEL_ID de comun.py).")
        sys.exit(1)

    print("\nTodo correcto. El entorno esta listo para el laboratorio.")


if __name__ == "__main__":
    main()
