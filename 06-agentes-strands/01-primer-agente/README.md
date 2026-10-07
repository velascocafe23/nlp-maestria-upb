# 01-primer-agente: los tres pilares de un agente

## Objetivo

Construir tu primer agente y entender de que partes se compone.

## Concepto que ensena

Los tres pilares de un agente con Strands Agents:

1. El modelo: el "cerebro", aqui `gpt-5.6-luna` via el proveedor de OpenAI.
2. El system prompt: las instrucciones que definen su rol y su tono.
3. El Agent: la pieza que une modelo mas instrucciones y ejecuta el ciclo.

Este modulo hace una sola interaccion (no hay bucle) para centrarse en como se
arma un agente basico y como se le hace una pregunta.

## Como ejecutarlo

1. Entra a la carpeta del modulo:

   ```bash
   cd 01-primer-agente
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
   python primer_agente.py
   ```

## Que observar

- El agente responde en espanol, de forma clara y breve.
- Fijate como el system prompt influye en el tono y el estilo de la respuesta.

## Ejemplo adicional: asistente interactivo (CLI)

La subcarpeta `agente-cli/` contiene un ejemplo interactivo de terminal, al
estilo del `recipe-bot-cli` del workshop oficial. A diferencia de
`primer_agente.py` (una sola interaccion), el CLI corre en un bucle: conversas
con el agente hasta escribir `salir`, y ademas trae dos herramientas propias
(una calculadora y una que da la hora) para ver al modelo elegir cual usar.

Para correrlo:

```bash
cd agente-cli
python asistente_cli.py
```

No hace falta crear un .env aqui: se reutiliza el de la raiz del laboratorio.

Consulta `agente-cli/README.md` para el detalle.
