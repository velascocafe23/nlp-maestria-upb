# Entrega 5 · Lab SFT: Supervised Fine-tuning de BETO para sentimiento

**Autor:** Sebastián Velasco Ardila · **Entorno:** Google Colab (GPU T4)
**Notebook:** [`lab_sft_beto.ipynb`](lab_sft_beto.ipynb) ([abrir en Colab](https://colab.research.google.com/github/velascocafe23/nlp-maestria-upb/blob/main/05-sft-beto/lab_sft_beto.ipynb))

## Qué se hizo

- **Parte A (guiada):** baseline con BETO congelado (mean pooling + regresión logística) y SFT de `BertForSequenceClassification` sobre tweets en español (5 epochs, lr 2e-5); F1 macro de ambos y análisis de errores.
- **Parte B (reto, pasos 12–16):** el mismo patrón con sentimiento financiero (`nojedag/financial_phrasebank_multilingual`, español), con cabeza fresca sobre BETO base, mismos hiperparámetros, F1 macro y el **baseline opcional** replicado. Añadí una tabla con los cuatro F1 (baseline y SFT, tweets y finanzas), la evolución por epoch y los ejemplos que el SFT corrigió.

### Verificación de etiquetas (lo que el enunciado pide revisar)

El dataset financiero codifica `labels` como `ClassLabel` con nombres `["neutral", "positive", "negative"]`, es decir **0 = neutral, 1 = positivo, 2 = negativo**. Los tweets usan **0 = negativo, 1 = neutral, 2 = positivo**. No coinciden. Para la red da igual (la cabeza es nueva), pero el diccionario `LABELS`, los `target_names` del reporte y el análisis de errores habrían quedado cruzados. El notebook lee los nombres del propio dataset, construye el reordenamiento (`{0:1, 1:2, 2:0}`) y lo aplica antes de construir los `DataLoader`s; imprime dos ejemplos por clase como comprobación a ojo. Además, `lang` también es `ClassLabel` (entero), así que el filtro usa `str2int("es")` en vez de comparar con el string.

## Resultados

_(se completan con la corrida en T4)_

| Dominio | Train | Test | F1 baseline | F1 SFT | Ganancia |
|---|---|---|---|---|---|
| Tweets (Parte A) | | | | | |
| Financiero (Parte B) | | | | | |

Reporte por clase (financiero): _(pegar)_. Ejemplos corregidos por el SFT: _(n)_; dañados: _(n)_.

## Reflexión final (paso 17)

_Borrador a confirmar con los números._

- **Tweets vs. financiero.** Espero un F1 claramente **mayor** en el dominio financiero, incluso con baseline: las frases de prensa económica son explícitas ("las ventas cayeron un 12 %"), hay más datos de entrenamiento y la clase neutral está bien definida (hechos sin valoración). Los tweets tienen ironía, jerga y una clase neutral difusa. El ruido de la traducción automática puede costar algunos puntos, pero no debería invertir el orden.
- **Baseline vs. SFT.** La ganancia del SFT debería ser **menor** en finanzas que en tweets: si las representaciones congeladas de BETO ya separan bien las clases (F1 baseline alto), queda menos margen. En tweets el baseline parte bajo porque el registro informal está lejos del corpus de preentrenamiento de BETO, y afinar el encoder aporta más.
- **Etiquetas.** El mapeo no coincide (ver arriba). Es el tipo de error que no produce excepción: el entrenamiento converge, la accuracy sube, y solo el reporte por clase o una lectura de ejemplos revela que "negativo" significaba neutral. La regla que me llevo: leer `features` antes de entrenar y nunca asumir que dos datasets comparten convención.
- **CPT + SFT juntos.** Primero CPT adapta el modelo al **lenguaje** del dominio (vocabulario, registro) sin necesitar etiquetas; luego SFT usa los pocos ejemplos etiquetados para la **tarea**. El orden inverso desperdiciaría las etiquetas, porque el CPT posterior movería los pesos que el SFT ajustó, y arrancar el SFT desde un modelo que ya "habla" el dominio converge más rápido y con menos datos.
- **Cuándo preferir el baseline.** Con pocos ejemplos etiquetados (cientos), sin GPU, o cuando el riesgo de sobreajuste y la necesidad de reentrenar seguido pesan más que unos puntos de F1: extraer embeddings una vez y entrenar una regresión logística cuesta segundos y es fácil de auditar.
