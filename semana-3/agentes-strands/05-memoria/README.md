# 05-memoria: memoria de conversacion

## Objetivo

Entender como un agente mantiene contexto entre turnos.

## Concepto que ensena

Un agente util recuerda lo que se dijo antes. A esto le llamamos memoria de
conversacion. En Strands, un mismo objeto Agent mantiene el historial de la
conversacion automaticamente: cada vez que lo llamas, agrega tu mensaje y su
respuesta a una lista interna de mensajes (agente.messages).

Idea clave:

- Si reutilizas el MISMO agente en varios turnos, recuerda el contexto.
- Si crearas un agente NUEVO en cada turno, empezaria en blanco cada vez.

Este modulo simula una conversacion de varios turnos con el mismo agente y, al
final, imprime cuantos mensajes hay en el historial.

## Como ejecutarlo

1. Entra a la carpeta del modulo:

   ```bash
   cd 05-memoria
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
   python memoria.py
   ```

## Que observar

- En el turno 2 el agente recuerda el nombre dado en el turno 1.
- En el turno 3 el agente usa el tema mencionado antes.
- Al final, el contador de mensajes del historial crece con cada turno.
