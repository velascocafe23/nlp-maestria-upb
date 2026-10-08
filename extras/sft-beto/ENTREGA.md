# Extra · Lab SFT: Supervised Fine-tuning de BETO para sentimiento

**Autor:** Sebastián Velasco Ardila · **Entorno:** Google Colab (GPU Tesla T4) · **Ejecutado:** 7 de octubre de 2026
**Notebook:** [`lab_sft_beto.ipynb`](lab_sft_beto.ipynb) ([abrir en Colab](https://colab.research.google.com/github/velascocafe23/nlp-maestria-upb/blob/main/extras/sft-beto/lab_sft_beto.ipynb)) — ejecutado de principio a fin, sin errores, con las salidas guardadas.

## Qué se hizo

- **Parte A (guiada):** baseline con BETO congelado (mean pooling + regresión logística) y SFT de `BertForSequenceClassification` sobre tweets en español (5 epochs, lr 2e-5); F1 macro de ambos y análisis de errores.
- **Parte B (reto, pasos 12–16):** el mismo patrón con sentimiento financiero (`nojedag/financial_phrasebank_multilingual`, español), con cabeza fresca sobre BETO base, mismos hiperparámetros, F1 macro y el **baseline opcional** replicado. Añadí una tabla con los cuatro F1 (baseline y SFT, tweets y finanzas), la evolución por epoch y los ejemplos que el SFT corrigió.

### Verificación de etiquetas (lo que el enunciado pide revisar)

El dataset financiero codifica `labels` como `ClassLabel` con nombres `["neutral", "positive", "negative"]`, es decir **0 = neutral, 1 = positivo, 2 = negativo**. Los tweets usan **0 = negativo, 1 = neutral, 2 = positivo**. No coinciden. Para la red da igual (la cabeza es nueva), pero el diccionario `LABELS`, los `target_names` del reporte y el análisis de errores habrían quedado cruzados. El notebook lee los nombres del propio dataset, construye el reordenamiento (`{0:1, 1:2, 2:0}`) y lo aplica antes de construir los `DataLoader`s; imprime dos ejemplos por clase como comprobación a ojo. Además, `lang` también es `ClassLabel` (entero, `es` = 3), así que el filtro usa `str2int("es")` en vez de comparar con el string.

## Resultados

| Dominio | Train | Test | Balance de clases (test) | F1 baseline | F1 SFT | Ganancia |
|---|---|---|---|---|---|---|
| Tweets (Parte A) | 1 839 | 870 | 290 / 290 / 290 | 0,593 | 0,639 | +0,046 |
| Financiero (Parte B) | 4 089 | 1 753 | neg 255 / neu 894 / pos 604 | 0,620 | **0,659** | +0,038 |

Reporte por clase del SFT financiero (accuracy 0,78):

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| negativo | 0,54 | **0,22** | 0,31 | 255 |
| neutral | 0,77 | 0,92 | 0,83 | 894 |
| positivo | 0,85 | 0,81 | 0,83 | 604 |

Evolución del SFT financiero: pérdida 0,67 → 0,18; accuracy de validación 0,763 → 0,779 (máximo 0,788 en el epoch 4). En tweets la pérdida llegó a 0,10 y la accuracy se quedó en ~0,65 desde el epoch 2: sobreajuste claro. El SFT financiero corrigió 261 frases que el baseline fallaba y dañó 118 que acertaba; en tweets corrigió 141.

## Reflexión final (paso 17)

**Tweets vs. financiero.** BETO alcanzó mejor F1 macro en el dominio financiero (0,659 vs. 0,639) y mucha mejor accuracy (0,78 vs. 0,66), como esperaba: más datos, lenguaje formal y explícito, y una clase neutral bien definida (hechos sin valoración). Pero la diferencia en F1 macro es pequeña por una razón que no anticipé: **la clase negativa financiera casi no se aprende** (recall 0,22). Dos causas se ven en los datos. Primero, el desbalance: solo 605 negativos en train frente a 2 236 neutrales, y la cabeza aprende a refugiarse en neutral. Segundo, y más interesante, el **ruido de las etiquetas**: entre los ejemplos "corregidos" por el SFT aparecen frases como "los beneficios disminuyeron un 62,3 %", "redujo 700 puestos de trabajo" o "el beneficio neto se redujo a 36 millones" etiquetadas como *neutral*. En el Financial PhraseBank original la etiqueta mide el efecto esperado sobre la acción según anotadores humanos, y la traducción automática añade frases mezcladas (tweets de `$TSLA`, `$MSFT`). El modelo aprende la convención del dataset, no la polaridad que un lector esperaría, y eso hunde la clase negativa. La lección es que el F1 macro expone lo que la accuracy esconde: un 0,78 de accuracy convive con una clase que falla cuatro de cada cinco veces.

**Baseline vs. SFT.** La ganancia fue similar en ambos dominios (+0,046 en tweets, +0,038 en finanzas) y menor de lo que anticipaba en tweets. En tweets, el SFT sobreajusta: la pérdida de entrenamiento baja a 0,10 mientras la accuracy de validación no se mueve desde el epoch 2; con 1 839 ejemplos ruidosos, cinco epochs sobran y harían falta regularización, *early stopping* o más datos. En finanzas el baseline ya partía alto (0,62) porque las representaciones congeladas separan bien positivo de neutral, y lo que el SFT añade está limitado por el ruido de la clase negativa. En ambos casos el ajuste completo del encoder aporta, pero menos de lo que la narrativa "fine-tuning siempre gana" sugiere; con estos tamaños, BETO congelado + regresión logística entrega el 90 % del resultado en segundos.

**Etiquetas.** El mapeo no coincide (ver arriba). Es el tipo de error que no produce excepción: el entrenamiento converge, la accuracy sube, y solo el reporte por clase o una lectura de ejemplos revela que "negativo" significaba neutral. La regla que me llevo: leer `features` antes de entrenar, imprimir ejemplos por clase, y nunca asumir que dos datasets comparten convención. Y una segunda, por lo visto en la Parte B: cuando una clase rinde mal, mirar los ejemplos antes de culpar al modelo; aquí el problema está en parte en las etiquetas.

**CPT + SFT juntos.** Primero CPT adapta el modelo al **lenguaje** del dominio (vocabulario, registro) sin necesitar etiquetas; luego SFT usa los pocos ejemplos etiquetados para la **tarea**. El orden inverso desperdiciaría las etiquetas, porque el CPT posterior movería los pesos que el SFT ajustó, y arrancar el SFT desde un modelo que ya "habla" el dominio converge más rápido y con menos datos. En este caso, además, el cuello de botella no es el lenguaje sino las etiquetas: antes de un CPT financiero invertiría en limpiar o re-anotar la clase negativa.

**Cuándo preferir el baseline.** Con pocos ejemplos etiquetados (cientos), sin GPU, cuando el riesgo de sobreajuste es alto (como se vio en tweets) o cuando hay que reentrenar seguido: extraer embeddings una vez y entrenar una regresión logística cuesta segundos, es fácil de auditar y aquí quedó a menos de cinco puntos del fine-tuning completo.
