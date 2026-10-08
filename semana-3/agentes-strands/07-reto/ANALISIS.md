# Analisis: de verdad necesitas un agente?

- **Autor:** Sebastián Velasco Ardila
- **Dominio elegido:** asistente de reservas para apartamentos turísticos en Armenia, Quindío (alquiler por noches)
- **Fecha de la corrida:** 7 de octubre de 2026, 19:50–20:02 (hora de Colombia), desde Windows 11 con Python 3.12
- **Modelo y repeticiones:** `gpt-5.6-luna` vía `OpenAIResponsesModel` (Strands Agents), 3 repeticiones por caso, 10 casos, 3 arquitecturas = 90 corridas

## 1. La tarea

Tengo apartamentos en Armenia que alquilo por noches a turistas. El sistema atiende el chat de un huésped potencial: le dice cuánta gente cabe y cuánto vale la noche de un apartamento, si está libre en unas fechas, cuánto le sale una estadía completa, cuál apartamento le sirve a su grupo, y cuáles son las reglas de la casa (mascotas, cancelación, horarios, parqueadero). El usuario es alguien que escribe desde el celular, a veces con todos los datos y a veces con la mitad.

Definí cinco herramientas, cada una con una responsabilidad distinta:

| Herramienta | Tipo | Puede fallar con |
|---|---|---|
| `consultar_apartamento(codigo)` | consulta de datos | código inexistente |
| `buscar_por_capacidad(huespedes)` | consulta de datos | grupo más grande que cualquier apartamento |
| `verificar_disponibilidad(codigo, fecha, noches)` | consulta de calendario | código inexistente |
| `cotizar_estadia(codigo, noches, huespedes)` | cálculo determinista (noches × tarifa, aseo, 10 % desde 7 noches) | capacidad excedida, mínimo de noches |
| `consultar_politica(tema)` | consulta de reglas | tema sin política registrada |

El flujo es variable por construcción: una pregunta de capacidad necesita una herramienta; una de "¿está libre y cuánto sale?" necesita dos en un orden; "somos 6, ¿cuál nos sirve y cuánto es una semana?" exige primero elegir el apartamento y después cotizar; un "gracias, ya con eso" no necesita ninguna. Hay algo que decidir en cada mensaje, y esa decisión es lo que se compara. Los datos (catálogo, calendario y políticas) están en memoria y son ilustrativos, para que el experimento sea reproducible y no dependa de internet.

## 2. Hipótesis previas

_Escritas antes de la corrida completa, con A1 ya probado en local (no gasta API) y A2/A3 sin ejecutar. No se modificaron después de ver los resultados._

| Arquitectura | Dónde espero que gane | Dónde espero que pierda |
|---|---|---|
| A1 determinista | Latencia (milisegundos) y costo (0 tokens). Consistencia perfecta: 10/10 casos estables. 100 % en `una_tool`, `dato_inexistente` y `composicion` cuando el mensaje trae los datos en el formato que esperan las reglas. | `ambiguo` (0 %: "apto 2" no coincide con el patrón `APT-n`) y la mitad de `sin_tool` (no puede responder conocimiento general). Riesgo de responder **con confianza algo equivocado** cuando una regla dispara por la palabra incorrecta. |
| A2 monolítico | `ambiguo` y `sin_tool`: entiende redacción informal y sabe cuándo no usar herramientas. Debería estar cerca del 90 % de éxito global. | Selección exacta: espero que a veces llame `consultar_apartamento` de más antes de cotizar (la métrica de selección lo castiga aunque la respuesta sea correcta). Latencia de 3 a 8 s y unos 1.000 a 2.000 tokens por caso. Alguna inestabilidad entre repeticiones en `ambiguo`. |
| A3 orquestador | Igual o apenas mejor que A2 en `composicion` si el reparto de responsabilidades ayuda al modelo a no mezclar tareas. | Latencia (dos niveles de LLM, 7 a 15 s), tokens (el doble que A2) y `memoria`: el especialista se crea nuevo en cada llamada, así que la memoria vive solo en el orquestador y hay que confiar en que reenvíe el contexto. Espero que **no** mejore el éxito respecto a A2. |

**La predicción que más importa:** sin medir nada, elegiría A2 para producción. El dominio tiene suficiente variabilidad de redacción como para que las reglas de A1 se queden cortas con usuarios reales, y A3 agrega complejidad que tres herramientas sencillas no justifican. Mi apuesta concreta: A2 gana en éxito global (≈ 90 % vs. ≈ 70 % de A1 vs. ≈ 80 % de A3), A1 gana en todo lo demás (costo, latencia, consistencia), y A3 no supera a A2 en ninguna categoría.

## 3. Diseño experimental

**Las tres arquitecturas.**

- **A1 determinista:** expresiones regulares extraen código (`APT-n`), fecha ISO, noches (dígitos o palabras, "una semana" = 7), número de personas y palabras clave de políticas; una cadena de `if` decide qué herramientas llamar y en qué orden (política → código con fecha/noches → código solo → personas sin código → saludo → rechazo). **No hace ninguna llamada al modelo**, ni siquiera para redactar: la respuesta se arma con plantillas, así que A1 reporta 0 tokens. Cuando ninguna regla aplica, devuelve un rechazo honesto (`resuelta=False`) sin herramientas. La memoria entre turnos es la concatenación de los turnos: es la decisión más simple posible y el experimento mide dónde alcanza.
- **A2 monolítico:** un `Agent` con las cinco herramientas, un system prompt que le pide no inventar datos y no usar herramientas cuando no hacen falta, y salida estructurada con el esquema `RespuestaReserva`. El modelo decide todo.
- **A3 orquestador:** un orquestador sin herramientas de dominio que delega en tres especialistas envueltos con `@tool` (inventario: catálogo y calendario; cotizaciones: precios; políticas: reglas), cada uno con su system prompt, su subconjunto de herramientas y `callback_handler=None`. Solo el orquestador habla con el huésped y produce la salida estructurada.

**El esquema común** (`RespuestaReserva`): `resuelta`, `codigo`, `total`, `disponible`, `mensaje`. Las tres arquitecturas lo devuelven, y los verificadores se apoyan en él.

**El banco de casos** (10 casos, 6 categorías):

| Categoría | Casos | Qué expone en este dominio |
|---|---|---|
| `una_tool` | 2 | camino feliz de catálogo y de políticas |
| `composicion` | 2 | disponibilidad + cotización; elegir apartamento + cotizar una semana con descuento |
| `sin_tool` | 2 | una despedida (falsos positivos) y una pregunta de conocimiento general que ninguna herramienta puede responder |
| `dato_inexistente` | 1 | apartamento que no existe: admitirlo sin inventar tarifa |
| `ambiguo` | 1 | redacción informal sin formato de código, sin fechas ni noches |
| `memoria` | 2 | el segundo turno depende del primero; en uno de ellos los dos turnos son de temas distintos |

**Verificadores.** Cada caso comprueba el campo estructurado y, cuando hay una cifra correcta posible, que el total coincida con el que produce la propia herramienta `cotizar_estadia` (calculado fuera del arnés, así no se escribe el número a mano). Para `ambiguo`, donde no existe un total correcto, el éxito es identificar el `APT-2` y dar la tarifa o pedir el dato que falta. Para `dato_inexistente`, el éxito es `resuelta=False`. Los escribí antes de ver una sola respuesta de A2 o A3; sí vi las de A1, y por eso el caso `conocimiento_general` exige una afirmación ("sí", "Eje Cafetero" o "Quindío") y no solo `resuelta=True`.

**Repeticiones:** 3, el mínimo del enunciado. Con 10 casos son 30 observaciones por arquitectura y 3 por celda de la tabla de categorías: suficiente para ver patrones gruesos, no para diferencias finas (ver amenazas a la validez).

**Comparabilidad de la selección en A3.** Decidí mantener los especialistas opacos: el arnés ve `especialista_inventario`, `especialista_cotizaciones`, `especialista_politicas` y no las herramientas internas. Por eso **la métrica `seleccion` de A3 no es comparable con la de A1 y A2** y espero que salga cercana a 0 % en todo lo que no sea `sin_tool`. No le di al orquestador acceso directo a las herramientas porque eso lo convertiría en un A2 con tres herramientas más, y dejaría de medir el patrón de delegación. Para A3 la pregunta de selección se responde a mano leyendo la columna `herramientas` del CSV (qué especialista eligió), y la comparación justa entre arquitecturas es la tasa de éxito, la latencia y los tokens.

## 4. Resultados

Tablas tal como las imprimió el arnés (90 corridas, 0 excepciones). Datos crudos en [`resultados.csv`](resultados.csv).

### Resumen por arquitectura

```
==============================================================================
RESUMEN POR ARQUITECTURA
==============================================================================
arquitectura             seleccion   exito  latencia   tokens  llamadas  errores
------------------------------------------------------------------------------
A1 determinista                80%     80%     0.00s        0       1.2        0
A2 monolitico                  93%    100%     5.38s     2669       1.4        0
A3 orquestador                 20%     83%    10.21s     2002       1.3        0
```

### Tasa de exito por categoria

```
==============================================================================
TASA DE EXITO POR CATEGORIA DE CASO
==============================================================================
categoria               A1 determinista      A2 monolitico     A3 orquestador
------------------------------------------------------------------------------
una_tool                           100%               100%               100%
composicion                        100%               100%               100%
sin_tool                            50%               100%               100%
dato_inexistente                   100%               100%                33%
ambiguo                              0%               100%                 0%
memoria                            100%               100%               100%
```

### Consistencia entre repeticiones

```
==============================================================================
CONSISTENCIA ENTRE LAS 3 REPETICIONES
==============================================================================
A1 determinista         10/10 casos estables
A2 monolitico           8/10 casos estables
                        inestables: disponibilidad_y_precio, redaccion_informal
A3 orquestador          9/10 casos estables
                        inestables: apartamento_inexistente
```

### Errores

```
No hubo excepciones en ninguna de las 90 corridas (columna "error" vacía en todo el CSV).
```

### Detalle por categoría (calculado del CSV)

| Categoría | A2 latencia · tokens | A3 latencia · tokens | Especialistas que eligió A3 |
|---|---|---|---|
| una_tool | 4,4 s · 2 170 | 7,8 s · 1 497 | inventario / políticas (el correcto en 6/6) |
| composicion | 5,0 s · 2 944 | 13,6 s · 2 214 | inventario + cotizaciones (6/6) |
| sin_tool | 2,4 s · 1 096 | 3,5 s · 1 194 | ninguno (6/6) |
| dato_inexistente | 4,2 s · 2 168 | 7,5 s · 1 514 | inventario (3/3) |
| ambiguo | 6,6 s · 2 406 | 9,7 s · 1 721 | inventario (3/3) |
| memoria | 9,7 s · 4 851 | 17,6 s · 3 490 | los esperados, incluida políticas en el caso mixto (6/6) |

Costo por tarea resuelta: A1 = 0 tokens; A2 = 80 078 tokens / 30 éxitos = **2 669 tokens por éxito**; A3 = 60 073 / 25 = **2 403 tokens por éxito** (cifra engañosa: ver amenazas a la validez). Tiempo total de la corrida: A1 < 0,01 s; A2 161 s; A3 306 s.

## 5. Interpretacion

**1. Quién ganó dónde.** A2 ganó en todo: 30 de 30, 100 % en las seis categorías. A1 empató con A2 en cuatro categorías (`una_tool`, `composicion`, `dato_inexistente`, `memoria`) y se hundió exactamente donde predije: 0 % en `ambiguo` y 50 % en `sin_tool`. A3 empató en cuatro y perdió en dos: 33 % en `dato_inexistente` y 0 % en `ambiguo`. Lo que diferencia a las arquitecturas no es la capacidad de resolver el camino feliz (ahí las tres son equivalentes) sino qué hacen con la entrada que no viene como se espera.

El fallo de A1 en `ambiguo` merece una lectura más fina que "no entendió". Con *"hola q tal, el apto 2 pa 2 personas la otra semana cuanto sale?"* la regla del código (`APT-n`) no dispara, pero la regla de personas sí ("2 personas"), así que A1 llama `buscar_por_capacidad(2)` y responde **con seguridad que al huésped le sirve el APT-1**, cuando el huésped preguntó por el 2. No es un rechazo honesto: es una respuesta equivocada con tono de correcta, el peor modo de fallo para un sistema de atención. En `conocimiento_general` A1 sí rechaza con honestidad ("no entendí la solicitud"), que es el comportamiento diseñado, y el verificador lo cuenta como fallo porque la tarea era responder.

A3 falló en `apartamento_inexistente` dos de tres veces. Las tres veces delegó en el especialista correcto (`especialista_inventario`), que tiene la herramienta que lanza el error; lo que se perdió está en el tramo de vuelta: el orquestador recibe un texto del especialista diciendo que el APT-9 no existe y, al rellenar el esquema, marcó `resuelta=True` en dos repeticiones (el mensaje era correcto, el campo no). En `ambiguo`, A3 también eligió bien el especialista pero el verificador exige `codigo == "APT-2"` en el campo estructurado y la tarifa o una petición de datos en el texto; con dos saltos de LLM (orquestador → especialista → orquestador) la información del código se diluyó y el campo llegó vacío o distinto en las tres repeticiones. En ambos casos el patrón es el mismo: **el agente intermedio pierde fidelidad en los campos estructurados**, no en la decisión de a quién llamar.

**2. Cuánto costó la flexibilidad.** A1 resolvió 24 de 30 tareas en menos de una centésima de segundo total y sin un solo token. A2 resolvió las 30 a 5,4 s y 2 669 tokens promedio por caso, es decir, **cada tarea que A2 resolvió y A1 no (son 6: tres de `ambiguo` y tres de `conocimiento_general`) costó, prorrateado, unos 13 000 tokens y 27 s de latencia acumulada**. Visto así, el agente se paga si una respuesta equivocada o un rechazo a un huésped real vale más que eso, y en un negocio de reservas donde cada mensaje mal atendido es una reserva que se va a otro anfitrión, sí lo vale. A3 costó el doble de latencia que A2 (10,2 s vs. 5,4 s; en `memoria` 17,6 s vs. 9,7 s) para resolver menos.

**3. Dónde se equivocó mi hipótesis.** Acerté en la dirección general (A2 > A3 ≥ A1 en éxito, A1 imbatible en costo y consistencia) pero fallé en tres cosas concretas. Primera, subestimé a A2: predije ≈ 90 % y sacó 100 %, con una selección de 93 % que solo falló por llamar `consultar_apartamento` de más dos veces, ambas en casos que resolvió bien; esperaba más herramientas de sobra. Segunda, acerté en que A3 no superaría a A2 pero me equivoqué en **dónde** perdería: predije `memoria` (por los especialistas sin estado) y A3 sacó 6/6 en memoria, porque la memoria vive en el orquestador y este reenvió bien el contexto; perdió en `dato_inexistente` y `ambiguo`, que no tenía en la lista. Tercera, A1 sacó 80 % y no 70 %: el caso `disponibilidad_y_precio` lo pasó porque corregí la fecha del caso antes de la corrida definitiva (la original caía sobre una noche ocupada y el verificador esperaba disponibilidad), un ajuste al banco de casos, no a A1. Que A2 saque 100 % también debería hacerme sospechar de mis casos: diez casos escritos por quien diseñó las herramientas probablemente son más limpios que diez mensajes reales de huéspedes.

**4. Casos inestables.** A2 fue inestable en dos casos, pero en los dos el **éxito** fue estable y lo que varió fue la **selección**: en `disponibilidad_y_precio` una repetición añadió `consultar_apartamento` antes de cotizar; en `redaccion_informal` una repetición decidió además cotizar (asumiendo noches) y las otras dos solo consultaron. A3 fue inestable en `apartamento_inexistente` (dos fallos, un éxito) y ahí sí varió el resultado, lo que lo hace peor de operar: el mismo mensaje unas veces se marca resuelto y otras no. Lo común a los tres casos inestables es que son los que admiten más de una ruta razonable; donde la ruta es única (`una_tool`, `memoria`) los agentes fueron tan estables como A1.

**5. El caso `sin_tool`.** Ninguna arquitectura usó una herramienta cuando no hacía falta: A1 por diseño, A2 y A3 en 12 de 12 corridas (selección 100 % en esa categoría). Los dos agentes tampoco gastaron en decidir: `sin_tool` fue su categoría más barata (≈ 1 100–1 200 tokens, 2,4–3,5 s). El system prompt que pide "si no necesita datos de la casa, responde directamente" fue suficiente. A1 falló la mitad por la razón opuesta: no puede responder sin herramientas lo que no está en sus plantillas.

**6. ¿A3 mejoró algo respecto a A2?** No. Mismo éxito o peor en todas las categorías, el doble de latencia en todas, y aparentemente menos tokens, que es un artefacto de medición (ver abajo). Lo único que A3 hizo igual de bien que A2 fue la delegación en sí: eligió el especialista correcto en 30 de 30 corridas, incluido el caso mixto de política + reserva donde activó los tres. El patrón orquestador-especialistas no aportó nada aquí porque el dominio tiene cinco herramientas simples que caben con holgura en un solo agente; la capa adicional solo añadió un punto donde la información estructurada se pierde. Es un resultado frecuente y conviene decirlo sin adornos.

## 6. Amenazas a la validez

- **Tokens de A3 subestimados.** `observar_agente` lee `metrics.accumulated_usage` del orquestador. Los especialistas son agentes aparte, creados dentro de cada `@tool`, y **sus tokens no entran en esa cuenta**. Los 2 002 tokens promedio de A3 son solo los del orquestador; el gasto real incluye tres modelos de razonamiento más y es con seguridad mayor que el de A2. Por eso en el punto 2 no uso los tokens de A3 para comparar costo; la latencia (10,2 s vs. 5,4 s), que sí incluye a los especialistas porque el arnés mide tiempo de pared, es la medida honesta. Una corrida seria instrumentaría los especialistas para sumar su uso.
- **Tamaño de la muestra.** Tres observaciones por celda de la tabla de categorías. Una diferencia de 100 % a 67 % es una sola corrida. Solo me creo las diferencias que son 3/3 contra 0/3 o que se repiten en varias categorías (A1 en `ambiguo`, A3 más lento en todo). El 33 % de A3 en `dato_inexistente` podría ser 67 % con otra semilla; el 0 % en `ambiguo` tres veces seguidas es más sólido.
- **Sesgo del banco de casos.** Escribí los casos conociendo las herramientas y, en el caso de A1, conociendo las reglas; corregí una fecha del caso `disponibilidad_y_precio` tras ver que caía en una noche ocupada. Los casos son más limpios que mensajes reales y el 100 % de A2 debe leerse como "sin fallos en estos diez", no como robustez general. La categoría `ambiguo` tiene un solo caso; con cinco variantes de redacción informal el cuadro sería más informativo.
- **Contaminación del verificador.** Los verificadores se escribieron antes de ver respuestas de A2 y A3, pero sí después de ver las de A1 en local; el caso `conocimiento_general` exige una afirmación en el texto porque vi que A1 respondía con un rechazo. Los verificadores de total usan la propia `cotizar_estadia`, así que si la herramienta tuviera un error aritmético, verificador y sistema fallarían juntos y no lo vería.
- **No determinismo.** `gpt-5.6-luna` no acepta temperatura, así que no hay forma de fijar la salida. Tres repeticiones alcanzaron para detectar inestabilidad en 3 de 20 celdas agénticas; no alcanzan para estimar su frecuencia.
- **Sin herramientas de internet.** Todo el dominio está en memoria, así que la fuente no cambió entre corridas; esa amenaza no aplica, a costa de un dominio más controlado que el real (un calendario de Airbnb cambia a diario).
- **Validez externa.** La conclusión "A2 basta y A3 sobra" depende de que el dominio tenga pocas herramientas simples. Con veinte herramientas de varios sistemas, o con especialistas que necesiten prompts largos y distintos, el reparto de A3 podría pagar lo que aquí no pagó. Y la ventaja de A2 sobre A1 depende de cuántos mensajes reales lleguen mal redactados: si los huéspedes escribieran siempre con código y fechas en formato ISO, A1 ganaría.

## 7. Recomendacion

Para esta tarea llevaría a producción **A2, el agente monolítico**, con dos condiciones: un umbral de confianza en el campo `resuelta` para enviar a revisión manual lo que el modelo no marque como resuelto, y un registro de qué herramientas usó en cada conversación para auditar la selección (hoy 93 %, con los fallos del lado seguro: una consulta de más, nunca una de menos). Es la única arquitectura que resolvió los casos que importan de verdad para un anfitrión: el mensaje informal escrito desde el celular y la pregunta general que no está en el catálogo. Su costo, unos 2 700 tokens y 5 s por mensaje, es irrelevante frente al valor de una reserva.

Cambiaría de opinión en tres escenarios. Si el volumen fuera de miles de mensajes por hora, montaría A1 **delante** de A2: las reglas resuelven el 80 % a costo cero y pasan al agente solo lo que no entienden, con la condición de que A1 rechace en vez de adivinar (hoy no lo hace en el caso `ambiguo`). Si apareciera un requisito de auditoría estricto (cada respuesta trazable a una regla), A1 sería la única opción y aceptaría perder los casos ambiguos. Y si el dominio creciera a decenas de herramientas con lógica propia (pagos, contratos, limpieza), volvería a probar A3 instrumentando bien a los especialistas antes de descartarlo.

Lo que no llevaría a producción tal como está: la cadena A1 en su forma actual, porque responde con seguridad cosas equivocadas cuando una regla dispara por la palabra incorrecta (el `buscar_por_capacidad` del caso informal); y la salida estructurada de A3, que perdió `resuelta` y `codigo` en el tramo de vuelta. Tampoco el banco de casos: diez casos escritos por mí no son una validación, son una prueba de humo.

## 8. Trabajo futuro

Instrumentar los especialistas de A3 para medir su consumo real y rehacer la comparación de costo. Reemplazar el banco de casos por 30 o 40 mensajes reales de huéspedes (anonimizados) para medir `ambiguo` con más de un caso y ver si el 100 % de A2 sobrevive. Probar la cascada A1 → A2 con rechazo honesto en A1 y medir qué fracción del tráfico llega al agente, que es el número que decide el costo en producción. Y variar `reasoning_effort` en A2 para ver cuánto de los 5 s se puede recortar sin perder el `ambiguo`.
