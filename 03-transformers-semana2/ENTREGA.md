# Entrega 3 · Lab Transformers · Semana 2: embeddings contextuales, comparativa multi-modelo, atención, clustering y zero-shot

**Autor:** Sebastián Velasco Ardila · **Entorno:** Google Colab (GPU T4)
**Notebook:** [`lab_transformers_semana2.ipynb`](lab_transformers_semana2.ipynb) ([abrir en Colab](https://colab.research.google.com/github/velascocafe23/nlp-maestria-upb/blob/main/03-transformers-semana2/lab_transformers_semana2.ipynb))

## Qué se hizo

Ejecuté el notebook completo en T4, incluido el bonus de zero-shot: GloVe vs. BETO sobre "banco", pipelines de sentimiento y NER con tweets y noticias financieras colombianas, comparativa de tres modelos de sentimiento (tamaño, tiempo, accuracy, F1), visualización de atención (bertviz y heatmap), clustering de tweets con t-SNE y clasificación zero-shot con `xlm-roberta-large-xnli`.

## Resultados observados

_(se completan con la salida de la ejecución)_

| Modelo | Tamaño (MB) | Tiempo (s) | Accuracy | F1 |
|---|---|---|---|---|
| RoBERTuito (ES) | | | | |
| BERT multilingüe (5★) | | | | |
| RoBERTa Twitter (EN) | | | | |

- Similitud coseno entre los dos "banco" de BETO: _(x)_.
- Capa/cabeza donde "banco" atiende a "central": _(capa, cabeza, peso)_.
- Zero-shot: _(n)_ de 5 aciertos; el más dudoso: _(…)_.

## Reflexiones

**Reflexión 1 — Estáticos vs. contextuales.** En finanzas la polisemia es la norma: "banco", "cuenta", "interés", "acción", "bono", "cartera". Un vector único mezcla sentidos y confunde al clasificador. El modelo necesita el contexto sintáctico y léxico de la oración; las analogías de GloVe muestran estructura entre palabras, pero no resuelven dos usos de la misma forma.

**Reflexión 2a — Transformer vs. clásico.** BoW falla en "no puedo pagar nada" y "no autoricé" porque trata la negación como una palabra más; el Transformer modela la dependencia entre "no" y el verbo. Aun así preferiría TF-IDF + LogReg en un banco cuando la regulación exige explicar la decisión (SARLAFT, PQRs auditables) o cuando el volumen es masivo y el presupuesto de GPU no existe. El riesgo de usar un modelo de tweets genéricos sin validar: jerga local ("plata", "cuota de manejo"), nombres de productos y sarcasmo pueden degradarlo sin que nadie lo note hasta que un reporte salga mal.

**Reflexión 2b — NER.** Las organizaciones con nombre propio simple (Bancolombia, Ecopetrol, Avianca, Airbus) salen bien; los compuestos con preposición ("Banco de la República", "Bolsa de Valores de Colombia") se parten o se marcan como LOC porque "República" y "Colombia" parecen lugares. Usos reales: extracción de partes y montos en contratos, monitoreo de noticias de competencia, enlace de menciones de clientes. BoW no sirve porque la salida es una etiqueta por token en secuencia.

**Reflexión 3 — Embeddings contextuales.** La similitud < 1 sale de la atención: el vector de "banco" se recombina con los de sus vecinos capa tras capa. Como features, mean pooling de `last_hidden_state` + regresión logística; es el baseline del lab de SFT.

**Comparativa multi-modelo — ¿gana el más grande?** _(ajustar con la tabla)_ Lo esperable y lo que se observa es que el modelo en el idioma y dominio correctos (RoBERTuito, el más pequeño) obtiene el mejor F1; el multilingüe de reseñas pierde información al colapsar 5 estrellas a 3 clases y confunde los neutros; el de Cardiff, entrenado en inglés, cae en español. Para un banco que responde en tiempo real priorizaría latencia si la diferencia de accuracy es de pocos puntos: la queja mal clasificada se corrige en el siguiente turno, la respuesta lenta se nota siempre. Al colapsar 5 estrellas perdemos la intensidad (una queja de 1★ y una de 2★ se vuelven iguales); conservaría la escala fina para priorizar casos críticos.

**Atención.** _(ajustar con la capa/cabeza observada)_ En capas intermedias aparece una cabeza donde "banco" atiende a "central" y "tasa" a "interés"; en capas bajas la atención va a los vecinos inmediatos. Varias cabezas permiten capturar relaciones distintas a la vez (sintaxis local, dependencias largas, correferencia) que una sola matriz tendría que mezclar. Esa capacidad de "juntar" banco + central es lo que separa el banco financiero del banco del parque.

**Clustering.** _(ajustar con la gráfica)_ Los tweets de opinión (positivos y negativos) tienden a separarse de los informativos (DANE, Banco de la República, Ecopetrol), que forman su propio grupo: BETO sin afinar codifica más el registro (noticia vs. opinión) que la polaridad. Los positivos y negativos pueden mezclarse porque comparten vocabulario de servicio bancario; el tweet con mezcla de emociones o sarcasmo queda en la frontera. Con 10 puntos y t-SNE la forma exacta varía; lo que se lee es la tendencia.

**Zero-shot.** El modelo convierte cada categoría en una hipótesis ("Este texto es una queja de servicio") y usa su entrenamiento en NLI para decidir implicación. Suele dudar entre "queja de servicio" y "reporte de fraude" en el mensaje de la compra no reconocida, porque ambas son plausibles. Para el canal de un banco propondría: queja, consulta de información, solicitud de producto, reporte de fraude, bloqueo o pérdida de tarjeta, felicitación. Ventaja: categorías nuevas sin reentrenar ni etiquetar; desventajas: modelo grande (~0,6 B parámetros), lento, y precisión menor que un clasificador supervisado cuando sí hay datos.

**Paso 4 — ¿Transformer o BoW?** En mi trabajo los textos son descripciones de tickets, logs y documentación técnica: vocabulario marcado y poca ironía, así que BoW/TF-IDF resuelve la mayoría de la clasificación temática. El costo real de la GPU es menos el precio por hora que la operación (despliegue, escalado, latencia p99); solo se justifica si la mejora de precisión cambia una decisión de negocio. Si el 95 % se resuelve con BoW, diseñaría un sistema en cascada: BoW por defecto y, cuando su probabilidad esté por debajo de un umbral o el texto tenga negación detectada, pasar el caso al Transformer.

**Reflexiones finales.**
1. GloVe: un vector por tipo; BETO: un vector por aparición, construido con la oración entera.
2. Tokenizar, inferir, formatear. Permite probar un modelo nuevo en minutos.
3. Para 5.000 tweets/día con necesidad de explicar: cascada BoW + Transformer, con el Transformer solo para los casos dudosos y un registro de las palabras que pesaron en cada decisión del modelo clásico.
4. Para afinar: datos etiquetados del propio banco, una cabeza de clasificación sobre BETO, GPU y validación por clase; lo hacemos en el lab de SFT.
