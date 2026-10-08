# 04-multiples-tools: varias herramientas, el modelo decide

## Objetivo

Ver como un agente elige entre VARIAS herramientas segun la pregunta.

## Concepto que ensena

Cuando un agente tiene varias herramientas, el modelo debe decidir cual usar (o
si usar varias). El estudiante no programa esa decision: la toma el modelo,
guiado por:

- El nombre de cada herramienta.
- El docstring (descripcion) de cada herramienta.
- Los type hints de los parametros.

Un buen docstring es clave, porque es lo que el modelo lee para decidir. Este
modulo da al agente cuatro herramientas (convertir moneda, convertir
temperatura, contar palabras y area de un rectangulo) y le hace preguntas
variadas para ver como elige.

## Como ejecutarlo

1. Entra a la carpeta del modulo:

   ```bash
   cd 04-multiples-tools
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
   python multiples_tools.py
   ```

## Que observar

- Cada pregunta activa una herramienta distinta, y la linea
  `[HERRAMIENTA] el modelo decide usar: ...` te dice cual eligio en cada caso.
- El modelo hace la correspondencia entre la intencion de la pregunta y la
  herramienta adecuada, sin que tu programes esa logica.
- Prueba a agregar una pregunta que no necesite ninguna herramienta (por
  ejemplo "quien escribio el Quijote?"): la linea `[HERRAMIENTA]` no aparece,
  porque el modelo decide responder directo.
