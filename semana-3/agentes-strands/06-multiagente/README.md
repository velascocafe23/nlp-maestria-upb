# 06-multiagente: agente como herramienta

## Objetivo

Aprender el patron "agente como herramienta" (agent-as-tool): un orquestador
que delega en agentes especialistas.

## Concepto que ensena

A veces un solo agente con muchas responsabilidades se vuelve dificil de
controlar. Una solucion es dividir el trabajo en agentes especialistas y tener
un agente orquestador que delega en ellos.

El patron funciona asi:

- Envuelves a un agente especialista dentro de una funcion decorada con @tool.
- Esa funcion crea el agente especialista, le pasa la consulta como texto y
  devuelve su respuesta como texto.
- El orquestador recibe esa funcion como una herramienta mas y decide cuando
  delegar.

Puntos importantes:

- La interfaz entre agentes es texto: el orquestador manda un string y recibe
  un string de vuelta.
- Cada especialista tiene su propio contexto aislado: no ve el historial del
  orquestador.
- callback_handler=None hace que el especialista trabaje en silencio.

Este modulo tiene dos especialistas: un traductor ingles a espanol y un
resumidor.

## Como ejecutarlo

1. Entra a la carpeta del modulo:

   ```bash
   cd 06-multiagente
   ```

2. Instala las dependencias (si no lo has hecho):

   Hay un solo requirements.txt para todo el laboratorio, en la raiz:

   ```bash
   pip install -r ../requirements.txt
   ```

3. Asegurate de que exista un archivo .env con tu clave de OpenAI en la RAIZ
   del laboratorio. Se crea una sola vez y sirve para todos los modulos. Si
   todavia no lo tienes:

   ```bash
   cp ../.env.example ../.env
   ```

   Edita ese .env y coloca tu clave real (OPENAI_API_KEY=sk-...). comun.py
   busca el .env subiendo desde la carpeta actual hacia las carpetas padre, por
   eso lo encuentra en la raiz y no hace falta copiarlo dentro de este modulo.

4. Corre el script:

   ```bash
   python multiagente.py
   ```

## Que observar

- El orquestador primero delega en el traductor y luego en el resumidor. Las
  dos lineas `[DELEGA]` te muestran ese orden:

  ```
    [DELEGA] el modelo decide usar: traductor_ingles_espanol
    [DELEGA] el modelo decide usar: resumidor
  ```

- Los especialistas trabajan en silencio (no imprimen su salida intermedia).
- La respuesta final combina el trabajo de ambos especialistas.
- El anuncio `[DELEGA]` sale de `crear_traza_herramientas("DELEGA")`, el mismo
  callback de `comun.py` que usan los modulos 03 y 04, solo con otra etiqueta:
  para el orquestador, usar una herramienta ES delegar en un especialista.
