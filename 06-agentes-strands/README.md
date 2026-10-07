# Laboratorio: agentes de IA con Strands Agents y OpenAI (gpt-5.6-luna)

Este laboratorio ensena, paso a paso, como construir agentes de IA con el
framework Strands Agents, usando `gpt-5.6-luna` de OpenAI como modelo. La clave
de la API se carga desde un archivo `.env` (nunca se escribe en el codigo).

Todo corre en un equipo normal sin GPU: el modelo vive en la API de OpenAI y tu
maquina solo hace las llamadas.

## Organizacion del laboratorio

El laboratorio esta dividido en modulos incrementales, uno por carpeta. Cada
modulo es autocontenido: trae su propio script, su copia de `comun.py`, su
`requirements.txt` y su `README.md` con instrucciones. Recorre los modulos en
orden, del 00 al 07.

| Carpeta | Concepto que ensena |
|---|---|
| `00-setup/` | Verifica librerias, valida la clave del `.env` y prueba el modelo. |
| `01-primer-agente/` | Los tres pilares: modelo, system prompt y Agent (una interaccion). |
| `02-agent-loop/` | El ciclo del agente: observar, pensar, actuar (con trazas visibles). |
| `03-tools-propias/` | Crear herramientas con el decorador `@tool` (tool calling). |
| `04-multiples-tools/` | Varias herramientas: el modelo decide cual usar. |
| `05-memoria/` | Memoria de conversacion: mantener contexto entre turnos. |
| `06-multiagente/` | Patron agente como herramienta: un orquestador delega en especialistas. |
| `07-reto/` | Plantilla con TODOs para que construyas tu propio agente. |

Ademas, el modulo `01-primer-agente/` incluye una subcarpeta `agente-cli/` con
un ejemplo interactivo de terminal (estilo `recipe-bot-cli` del workshop): un
agente con bucle de conversacion y dos herramientas propias. Ver
`01-primer-agente/agente-cli/README.md`.

## Requisitos

- Python 3.10 o superior.
- Una clave de API de OpenAI con acceso a `gpt-5.6-luna`.
- Conexion a internet (las llamadas van a la API de OpenAI).

## Instalacion

Hay UN solo `requirements.txt`, en la raiz del laboratorio, y se instala una
sola vez. Todos los modulos comparten el mismo entorno de Python, asi que con
esto quedan cubiertos del 00 al 07:

```bash
pip install -r requirements.txt
```

Si prefieres trabajar en un entorno virtual (recomendado):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Esto instala `strands-agents[openai]` y `python-dotenv`.

Detalle importante: el extra `[openai]` no es opcional. Es el que instala la
libreria `openai` que necesitan los proveedores de OpenAI de Strands. Si
instalas solo `strands-agents`, los scripts fallan con
`ModuleNotFoundError: No module named 'openai'`.

El `requirements.txt` incluye ademas dos dependencias comentadas,
`strands-agents-tools` y `ddgs`. Ningun script de los modulos 00 a 07 las usa,
por eso quedan fuera de la instalacion por defecto. Descomentalas si en el reto
(modulo 07) quieres usar las herramientas que trae Strands, por ejemplo
busqueda web.

Desde la carpeta de un modulo, el comando lleva la ruta relativa a la raiz:

```bash
cd 03-tools-propias
pip install -r ../requirements.txt
```

## Configurar la clave de OpenAI (archivo .env)

La clave se lee de un archivo `.env` mediante la libreria `python-dotenv`.
Nunca se escribe en el codigo. Basta con UN solo `.env`, en la raiz del
laboratorio, y sirve para todos los modulos.

Se configura una vez, desde la raiz:

1. Copia la plantilla:

   ```bash
   cp .env.example .env
   ```

2. Abre `.env` y coloca tu clave real:

   ```
   OPENAI_API_KEY=sk-tu-clave-real
   ```

Como funciona la busqueda: `comun.py` usa `find_dotenv(usecwd=True)`, que parte
de la carpeta desde la que ejecutas el script y sube por las carpetas padre
hasta encontrar un `.env`. Asi, corriendo `python memoria.py` dentro de
`05-memoria/`, encuentra el `.env` de la raiz. Si prefieres una clave distinta
para un modulo concreto, pon un `.env` dentro de esa carpeta: tiene prioridad
porque se encuentra primero.

No compartas ni subas el archivo `.env` a ningun repositorio (ya esta en
`.gitignore`). En un aula, cada estudiante debe usar su propia clave (idealmente
con un limite de gasto bajo configurado en su cuenta de OpenAI).

## Como correr el laboratorio

Empieza siempre por la verificacion del entorno y luego avanza en orden. Cada
modulo se ejecuta entrando a su carpeta y corriendo su script:

```bash
cd 00-setup && python setup.py
cd ../01-primer-agente && python primer_agente.py
cd ../02-agent-loop && python agent_loop.py
cd ../03-tools-propias && python tools_propias.py
cd ../04-multiples-tools && python multiples_tools.py
cd ../05-memoria && python memoria.py
cd ../06-multiagente && python multiagente.py
cd ../07-reto && python reto.py
```

Consulta el `README.md` dentro de cada carpeta para el detalle de ese modulo.

## Nota sobre el modelo: por que Responses API y no chat completions

Strands trae dos proveedores de OpenAI y aqui la eleccion importa:

- `OpenAIModel`, que habla con el endpoint clasico `/v1/chat/completions`.
- `OpenAIResponsesModel`, que habla con `/v1/responses`, el que OpenAI
  recomienda para los modelos de razonamiento.

Este laboratorio usa `OpenAIResponsesModel`, y no es una preferencia de estilo.
Con la familia `gpt-5.6-*` (incluido `luna`), si usas `OpenAIModel` y le das
herramientas al agente, la API corta con un error 400:

```
Function tools with reasoning_effort are not supported for gpt-5.6-luna
in /v1/chat/completions. To use function tools, use /v1/responses or set
reasoning_effort to 'none'.
```

Es decir, por chat completions habria que apagar el razonamiento para poder usar
herramientas. Como el laboratorio se basa justamente en tool calling (modulos 02,
03, 04, 06 y 07), vamos por `/v1/responses` y conservamos el razonamiento.

Sobre `temperature`: es un modelo de razonamiento y NO acepta un valor distinto
al predeterminado, por eso el modelo se crea sin pasar `temperature` (ver el
`comun.py` de cada modulo). Si necesitas controlar el esfuerzo de razonamiento,
puedes pasar `params={"reasoning_effort": "low" | "medium" | "high"}`.

El modelo se define en la constante `MODEL_ID` de `comun.py`, por si quieres
cambiarlo (por ejemplo a otro de la familia, como `gpt-5.6-terra`). Como cada
modulo tiene su
propia copia de `comun.py` (para que sea autocontenido), ese cambio se hace por
modulo. A diferencia de las dependencias y la clave, que ya estan centralizadas
en la raiz, `comun.py` se mantiene duplicado a proposito: asi el estudiante ve
en su carpeta todo el codigo que se ejecuta.

## Estructura del proyecto

```
lab-agentes-strands/
├── README.md                 # este indice general
├── requirements.txt          # UNICO archivo de dependencias, para todo el lab
├── .env.example              # plantilla de la clave (copiar a .env aqui en la raiz)
├── .env                      # tu clave real (no se sube, esta en .gitignore)
├── 00-setup/
│   ├── setup.py              # verificacion del entorno: librerias, clave y modelo
│   ├── comun.py
│   └── README.md
├── 01-primer-agente/
│   ├── primer_agente.py
│   ├── comun.py
│   ├── README.md
│   └── agente-cli/           (asistente_cli.py, ejemplo interactivo)
├── 02-agent-loop/            (agent_loop.py)
├── 03-tools-propias/         (tools_propias.py)
├── 04-multiples-tools/       (multiples_tools.py)
├── 05-memoria/               (memoria.py)
├── 06-multiagente/           (multiagente.py)
└── 07-reto/                  (reto.py)
```

Cada carpeta de modulo contiene su script, una copia de `comun.py` y su
`README.md`. Las dependencias y la clave viven solo en la raiz.

## Solucion de problemas

- "Falta OPENAI_API_KEY": crea el archivo `.env` en la raiz del laboratorio
  (puedes copiar `.env.example`) y coloca tu clave real.
- `ModuleNotFoundError: No module named 'openai'`: instalaste `strands-agents`
  sin el extra. Corrige con `pip install -r requirements.txt`, que ya pide
  `strands-agents[openai]`.
- `Error code: 401 ... invalid_api_key`: la clave no es valida. Revisa que la
  hayas copiado completa y sin caracteres de sobra. Un error tipico es dejar una
  letra pegada al inicio (`ssk-proj-...` en vez de `sk-proj-...`).
- "Fallo la llamada al modelo": revisa que la clave sea valida, que tengas
  acceso a `gpt-5.6-luna` y que haya conexion a internet.
- `400 ... Function tools with reasoning_effort are not supported ... in
  /v1/chat/completions`: estas usando `OpenAIModel` en lugar de
  `OpenAIResponsesModel`. Ver la nota sobre el modelo mas arriba.
- Error de import de `strands`: ejecuta `pip install -r requirements.txt`.

## Recursos

- Documentacion de Strands Agents: https://strandsagents.com/
- Repositorio de ejemplos: https://github.com/strands-agents/samples
