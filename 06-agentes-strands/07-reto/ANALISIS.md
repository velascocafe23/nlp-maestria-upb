# Analisis: de verdad necesitas un agente?

- **Autor:** Sebastián Velasco Ardila
- **Dominio elegido:** asistente de reservas para apartamentos turísticos en Armenia, Quindío (alquiler por noches)
- **Fecha de la corrida:** _(pendiente: se completa con la corrida definitiva)_
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

_Escritas antes de la corrida completa, con A1 ya probado en local (no gasta API) y A2/A3 sin ejecutar._

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

_(pendiente: tablas de la corrida definitiva, pegadas tal cual las imprime el arnés)_

### Resumen por arquitectura

```
(pegar)
```

### Tasa de exito por categoria

```
(pegar)
```

### Consistencia entre repeticiones

```
(pegar)
```

### Errores

```
(pegar, o indicar que no hubo)
```

## 5. Interpretacion

_(pendiente: se escribe con los números a la vista)_

## 6. Amenazas a la validez

_(pendiente)_

## 7. Recomendacion

_(pendiente)_

## 8. Trabajo futuro

_(pendiente)_
