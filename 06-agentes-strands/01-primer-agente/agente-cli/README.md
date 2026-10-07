# Ejemplo CLI: asistente interactivo

Este ejemplo replica el patron del workshop oficial (`recipe-bot-cli`): un agente
que corre en un bucle interactivo desde la terminal, en lugar de hacer una sola
interaccion y terminar.

## Que muestra

- Un agente con system prompt (rol y tono).
- Dos herramientas propias con `@tool`: una calculadora y una que da la hora.
- Un bucle de conversacion que mantiene el contexto entre turnos, porque
  reutiliza el mismo objeto `Agent` en cada vuelta.

## Como ejecutarlo

1. Entra a esta carpeta:

   ```bash
   cd 01-primer-agente/agente-cli
   ```

2. Instala las dependencias, si no lo has hecho. Hay un solo requirements.txt
   para todo el laboratorio, en la raiz:

   ```bash
   pip install -r ../../requirements.txt
   ```

3. Asegurate de tener el archivo `.env` con tu clave en la RAIZ del
   laboratorio (el mismo que usan los demas modulos):

   ```
   OPENAI_API_KEY=sk-tu-clave-real
   ```

   `comun.py` lo busca subiendo desde esta carpeta hacia las carpetas padre, asi
   que no necesitas crear una copia aqui.

4. Corre el asistente:

   ```bash
   python asistente_cli.py
   ```

Escribe preguntas como "cuanto es 3 * (4 + 5)?" o "que hora es?" y veras que el
agente responde con el resultado exacto, porque delega en sus herramientas.
Escribe `salir` para terminar.

Antes de cada respuesta veras una linea como esta cuando el modelo decida usar
una herramienta:

```
  [HERRAMIENTA] el modelo decide usar: calculadora
```

Y si la pregunta no necesita herramientas (por ejemplo "quien escribio el
Quijote?"), esa linea no aparece: el agente responde directo. Ese contraste es lo
interesante, porque la decision la toma el modelo, no el codigo.

Ese anuncio lo produce `crear_traza_herramientas()`, un `callback_handler` que
vive en `comun.py`. Solo imprime la herramienta elegida, no el texto de la
respuesta, para que el bucle la muestre una sola vez tras `Asistente >`.
