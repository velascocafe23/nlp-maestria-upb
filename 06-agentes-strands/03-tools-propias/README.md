# 03-tools-propias: crear herramientas con @tool

## Objetivo

Aprender a crear herramientas (tools) propias con el decorador @tool de Strands.

## Concepto que ensena

Una herramienta es una funcion de Python que el modelo puede decidir llamar
cuando la necesita. A esto se le llama tool calling: el modelo no ejecuta el
codigo, decide que funcion invocar y con que argumentos, y Strands se encarga de
ejecutarla y devolverle el resultado.

Claves para que una tool funcione bien:

1. El decorador @tool encima de la funcion.
2. Un docstring que describa que hace (el modelo lo lee para decidir).
3. Type hints en los parametros y en el retorno (ayudan al modelo).

Este modulo crea dos tools: una calculadora y una que devuelve la hora actual.

## Como ejecutarlo

1. Entra a la carpeta del modulo:

   ```bash
   cd 03-tools-propias
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
   python tools_propias.py
   ```

## Que observar

- Antes de cada respuesta aparece una linea que delata la decision del modelo:

  ```
    [HERRAMIENTA] el modelo decide usar: calculadora
  ```

- Ante una pregunta de calculo, el agente usa la tool calculadora.
- Ante una pregunta por la hora, el agente usa la tool hora_actual.
- El modelo elige la herramienta guiado por el nombre y el docstring.
- Ese anuncio lo imprime `crear_traza_herramientas()`, que vive en `comun.py` y
  se pasa al Agent como `callback_handler`. Solo informa de la herramienta
  elegida, no del texto de la respuesta, para que el script la imprima una sola
  vez.
