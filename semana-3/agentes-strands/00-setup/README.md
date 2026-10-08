# 00-setup: verificacion del entorno

## Objetivo

Comprobar que tu entorno esta listo antes de construir agentes. Este es el
primer modulo que debes correr.

## Concepto que ensena

Antes de programar agentes conviene validar tres cosas, en orden:

1. Que las librerias necesarias esten instaladas (strands-agents con el extra
   [openai], que es el que trae la libreria openai, y python-dotenv).
2. Que exista la clave OPENAI_API_KEY en el archivo .env de la raiz.
3. Que se pueda crear el modelo `gpt-5.6-luna` y hacer una llamada real.

## Como ejecutarlo

1. Entra a la carpeta del modulo:

   ```bash
   cd 00-setup
   ```

2. Instala las dependencias (si no lo has hecho):

   ```bash
   pip install -r ../requirements.txt
   ```

   Hay un solo requirements.txt para todo el laboratorio y vive en la raiz.
   Con instalarlo una vez quedan cubiertos todos los modulos, porque comparten
   el mismo entorno de Python.

3. Crea un archivo .env con tu clave de OpenAI en la RAIZ del laboratorio.
   Esto se hace UNA sola vez: ese mismo .env sirve para todos los modulos.
   Puedes partir de la plantilla:

   ```bash
   cp ../.env.example ../.env
   ```

   Luego edita ese .env y coloca tu clave real:

   ```
   OPENAI_API_KEY=sk-tu-clave-real
   ```

   Nota: comun.py usa find_dotenv(usecwd=True), que busca el .env empezando en
   la carpeta desde la que ejecutas el script y subiendo por las carpetas
   padre. Por eso encuentra el de la raiz sin que tengas que copiarlo en cada
   modulo. Si de todos modos pones un .env dentro de la carpeta del modulo, ese
   tiene prioridad porque se encuentra primero.

4. Corre el script:

   ```bash
   python setup.py
   ```

## Que observar

- Los tres pasos deben marcar OK.
- En el paso 3 el modelo debe responder con la palabra "listo".
- Si algo falla, el script lo dice con un mensaje claro y termina.
