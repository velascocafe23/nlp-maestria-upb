# 07-reto: de verdad necesitas un agente?

## Pregunta de investigacion

Para una tarea concreta, que gana y que pierde un sistema cuando dejas que un
LLM decida el flujo, en lugar de decidirlo tu en el codigo?

Los modulos 01 a 06 te ensenaron a construir agentes. Ninguno te enseno a
decidir si hacia falta uno. Ese es el trabajo de este reto, y es la pregunta que
de verdad se hace en un proyecto real, donde un agente cuesta plata, latencia y
predictibilidad.

## Que se evalua

No se evalua que el codigo corra. Se evalua que sepas disenar un experimento,
medirlo y sostener una conclusion con datos. La conclusion no esta decidida de
antemano: depende del dominio que elijas y de la mezcla de casos que armes.
"Para mi tarea el agente no se justifica" es una respuesta excelente si viene
con numeros y con una lectura honesta de sus limites.

## Que vas a construir

La misma tarea, en el dominio que tu elijas, resuelta con tres arquitecturas:

| | Arquitectura | Quien decide el flujo |
|---|---|---|
| A1 | Cadena determinista | Tu codigo, con reglas fijas. Es el baseline. |
| A2 | Agente monolitico | Un `Agent` con todas las herramientas (modulo 04). |
| A3 | Orquestador y especialistas | Un orquestador que delega (modulo 06). |

Mas un banco de casos de prueba que las somete a las tres a lo mismo, y un
informe escrito donde interpretas los resultados.

## Archivos del modulo

| Archivo | Que es |
|---|---|
| `reto.py` | Tu trabajo. Tiene las partes marcadas con TODO. |
| `arnes.py` | La infraestructura de medicion. No la modifiques, pero leela. |
| `ANALISIS.md` | La plantilla de tu informe. Es parte de la entrega. |
| `comun.py` | El modelo y la clave, igual que en los demas modulos. |
| `resultados.csv` | Lo genera el arnes al correr. Se entrega tambien. |

El dominio es libre. `reto.py` viene con un ejemplo funcional de mini inventario
para que el archivo corra desde el primer minuto y veas el mecanismo completo:
se espera que lo reemplaces por tu dominio.

## Requisitos obligatorios

1. **Dominio propio**, distinto del ejemplo de inventario. Elige uno donde el
   flujo no sea siempre el mismo: si tu tarea siempre se resuelve con los mismos
   tres pasos en el mismo orden, A1 gana por goleada y el reto se vuelve trivial.
2. **Al menos tres herramientas** con `@tool`. Una debe consultar datos y poder
   fallar con un dato inexistente; otra debe ser calculo determinista.
3. **Un esquema Pydantic** de salida estructurada, igual para las tres
   arquitecturas. Sin esto la comparacion no es justa y los verificadores se
   vuelven frageles.
4. **Las tres arquitecturas implementadas** y respetando el contrato de
   `Arquitectura.ejecutar`: crear el estado adentro, en cada llamada.
5. **A3 con al menos dos especialistas**, cada uno con su propio system prompt y
   su propio subconjunto de herramientas, en silencio
   (`callback_handler=None`).
6. **Banco de ocho a diez casos** que cubra las seis categorias de
   `arnes.CATEGORIAS`: `una_tool`, `composicion`, `sin_tool`,
   `dato_inexistente`, `ambiguo`, `memoria`.
7. **Un verificador programatico por caso**. Apoyate en el campo estructurado.
8. **Minimo tres repeticiones** por caso.
9. **`ANALISIS.md` completo**, con el `resultados.csv` que lo respalda.

## Restricciones de diseno

Estas reglas existen para que la comparacion mida lo que dice medir.

- **A1 no puede delegar decisiones al LLM.** Se permite como maximo una llamada
  al modelo, y solo para redactar la respuesta final en lenguaje natural. Que
  herramienta se llama y en que orden lo decide tu codigo. Tambien es valido no
  usar el LLM en absoluto.
- **Las tres arquitecturas comparten las mismas herramientas.** Las funciones
  decoradas con `@tool` se pueden llamar como funciones normales, asi que A1
  reutiliza exactamente las mismas, instrumentadas con `RegistroManual`.
- **Cuando A1 no entiende la pregunta, debe decirlo.** Devuelve una Observacion
  con un texto de rechazo y sin herramientas. No simules exito: ese rechazo es
  el dato que vas a comparar en la categoria `ambiguo`.
- **Nada de estado compartido entre casos.** El arnes crea el sistema de cero en
  cada caso y repeticion a proposito. Si cacheas un agente en una variable
  global, tus numeros dejan de medir el caso y empiezan a medir el orden en que
  corriste los casos.

## Como ejecutarlo

1. Entra a la carpeta del modulo:

   ```bash
   cd 07-reto
   ```

2. Instala las dependencias (si no lo has hecho). El reto habilita dos paquetes
   opcionales, `strands-agents-tools` y `ddgs`, por si tu dominio necesita datos
   reales o busqueda web:

   ```bash
   pip install -r ../requirements.txt
   ```

3. Asegurate de que exista el `.env` con tu clave en la RAIZ del laboratorio:

   ```bash
   cp ../.env.example ../.env
   ```

4. Corre el experimento:

   ```bash
   python reto.py
   ```

Tal como viene, A3 lanza `NotImplementedError` y el arnes la registra como error
en lugar de caerse. Vas a ver la columna de A3 en ceros hasta que la implementes:
eso es normal, el experimento empieza en rojo.

Mientras desarrollas, pon `MOSTRAR_TRAZA = True` en `reto.py` para ver que
herramienta elige el modelo en cada paso. Apagalo antes de la corrida final o la
salida se vuelve ilegible.

## Costo y como controlarlo

El arnes imprime el plan antes de empezar. Con 9 casos, 3 arquitecturas y 3
repeticiones son 81 corridas, y A1 no gasta nada. En los ordenes de magnitud de
este laboratorio eso son centavos de dolar, pero conviene que lo veas antes de
lanzarlo, porque el numero crece multiplicando.

Mientras desarrollas, baja `REPETICIONES` a 1 y comenta las arquitecturas que
todavia no tocas en `construir_arquitecturas()`. Sube a 3 o mas solo para la
corrida definitiva, la que reportas.

## Como leer las tablas

El arnes imprime cuatro. Cada una responde una pregunta distinta.

- **Resumen por arquitectura.** El promedio general. Sirve para el titular, pero
  esconde lo interesante, porque depende de cuantos casos de cada tipo pusiste.
  `seleccion` exige coincidencia EXACTA con el conjunto esperado: usar una
  herramienta de mas tambien cuenta como fallo.
- **Tasa de exito por categoria.** Esta es la que sostiene tu conclusion. Aqui se
  ve donde gana cada diseno, y lo normal es que ninguno gane en todo.
- **Consistencia entre repeticiones.** Un sistema con 80% de exito y 100% de
  consistencia falla siempre en lo mismo y puedes arreglarlo. Con 80% de exito y
  50% de consistencia es una loteria, y es mucho peor de operar aunque el
  promedio se vea igual.
- **Errores registrados.** Excepciones. Un sistema que se cae es un resultado
  valido y hay que poder medirlo.

## Entregables

1. `reto.py` con tu dominio, tus tres arquitecturas y tu banco de casos.
2. `ANALISIS.md` completo.
3. `resultados.csv` de la corrida que reportas.

## Rubrica

| Peso | Criterio |
|---|---|
| 25% | Diseno de las tres arquitecturas: fidelidad al patron, A1 realmente determinista, A3 con especialistas de verdad y no un agente disfrazado. |
| 20% | Calidad del banco de casos: cobertura de las seis categorias, casos realistas, verificadores que de verdad verifican. |
| 15% | Instrumentacion correcta: metricas comparables, esquema excluido de la seleccion, sin estado filtrado entre casos. |
| 30% | Analisis escrito: hipotesis previas, lectura de los numeros, amenazas a la validez, recomendacion argumentada. |
| 10% | Reproducibilidad y limpieza: el experimento corre de una sola vez, el CSV respalda lo que afirmas. |

El analisis pesa mas que cualquier bloque de codigo. Es deliberado.

## Trampas comunes

- **Verificadores tramposos.** Si solo compruebas que la respuesta no este
  vacia, tu tasa de exito no mide nada y el informe se cae solo.
- **Una sola corrida.** Estos sistemas son estocasticos. Con una repeticion no
  puedes distinguir entre "mi diseno funciona" y "tuve suerte".
- **Olvidar el esquema en `observar_agente`.** La salida estructurada de Strands
  se implementa como una herramienta sintetica con el nombre de tu clase
  Pydantic. Si no la excluyes, tu metrica de seleccion queda inflada y nunca
  coincide con lo esperado.
- **Comparar la seleccion de A2 contra la de A3 sin aclararlo.** En A3 el arnes
  ve los nombres de los especialistas, no de las herramientas internas. Es una
  decision de diseno experimental que debes declarar y justificar, no un bug.
- **Un dominio de flujo fijo.** Si siempre se resuelve igual, no hay nada que
  decidir y no hay experimento.
- **Concluir lo que ya creias.** Si tus numeros contradicen tu hipotesis,
  reportalo. Eso vale mas que un resultado bonito.

## Si quieres ir mas alla

Nada de esto es obligatorio, pero es por donde seguiria un trabajo serio.

- Una ablacion dentro de A2: los mismos casos con docstrings vagos y con
  docstrings precisos. Cuanto vale documentar bien una herramienta?
- El efecto de `params={"reasoning_effort": ...}` sobre exito, latencia y tokens.
- Traducir tokens a dolares con la tarifa del modelo y poner el costo por tarea
  resuelta al lado de la tasa de exito. Esa es la tabla que mira quien decide.
- Una cuarta arquitectura con una herramienta que salga a internet, y la
  discusion de que le pasa a la consistencia cuando la fuente de datos cambia
  entre repeticiones.
- Intervalos de confianza sobre las tasas en lugar de porcentajes sueltos.
