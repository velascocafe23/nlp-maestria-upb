# 02-agent-loop: el ciclo del agente

## Objetivo

Hacer visible el ciclo interno del agente: observar, pensar, actuar.

## Concepto que ensena

Un agente no solo responde: recibe una entrada (observa), el modelo razona que
hacer (piensa) y, si tiene herramientas, decide llamarlas (actua), repitiendo
el ciclo hasta tener una respuesta final.

Para "ver" ese ciclo usamos dos mecanismos de Strands:

1. El logging de la libreria (subimos el nivel a DEBUG para ver trazas).
2. Un callback_handler propio que imprime los eventos que emite el agente.

Se le da al agente una herramienta simple (una calculadora) para que tenga un
motivo real para "actuar" y asi el ciclo se note mas.

## Como ejecutarlo

1. Entra a la carpeta del modulo:

   ```bash
   cd 02-agent-loop
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
   python agent_loop.py
   ```

## Que observar

- Las trazas DEBUG de la libreria strands en la salida.
- Las fases marcadas por el callback: [PENSAR/RESPONDER] y [ACTUAR].
- Como el agente decide usar la herramienta sumar antes de dar el resultado.
