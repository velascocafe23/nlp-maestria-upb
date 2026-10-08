# Semana 1 · Lab 1: Preprocesamiento, N-grams y Word Embeddings

**Autor:** Sebastián Velasco Ardila · **Entorno:** Google Colab (CPU)
**Notebook:** [`lab1_embeddings.ipynb`](lab1_embeddings.ipynb) ([abrir en Colab](https://colab.research.google.com/github/velascocafe23/nlp-maestria-upb/blob/main/semana-1/lab1-embeddings/lab1_embeddings.ipynb))

## Qué se hizo

Ejecuté el notebook guiado completo: pipeline de limpieza, los tres tipos de tokenización, representaciones clásicas (one-hot, BoW, TF-IDF, OOV), un modelo de lenguaje de bigramas con suavizado de Laplace, y embeddings GloVe (similitud, analogías, PCA y auditoría de sesgo de género).

Dos ajustes al material original, documentados en el encabezado del notebook:

1. El notebook traía **dos versiones** de los experimentos 3.1 a 3.4 (one-hot, BoW/TF-IDF, clasificador, OOV). Dejé la segunda, que es la corregida, y eliminé la primera.
2. La celda de tokenización hacía `from tokenizers import AutoTokenizer`; esa clase vive en `transformers`, así que el bloque de BPE caía al `except` y mostraba un "~8 tokens" aproximado. Con el import corregido el Tipo 3 corre de verdad sobre `bert-base-multilingual-cased`.

## Resultados observados

_(se completan con la salida de la ejecución; ver celdas del notebook)_

- Tokenización de `"El banco BBVA Colombia reportó utilidades en el trimestre"`: por palabras = 9 tokens, por caracteres = 58, BPE = _(n)_. Palabras como `reportaron`, `bancolombia` y `fintech` se parten en subpalabras.
- Clasificador de sentimiento con 28 frases: baseline (clase mayoritaria) _(x)_, BoW + LogReg _(x)_, TF-IDF + LogReg _(x)_.
- Perplejidad del bigrama: oración financiera vs. "el perro come pizza en el parque": _(x)_ vs. _(x)_.
- Analogía `king - man + woman` → _(top-1)_; sesgo de género: profesiones orientadas a "man" _(lista)_ y a "woman" _(lista)_.

## Reflexiones

**Reflexión 1 — ¿Cuándo no quitar acentos?** Cuando la tilde carga significado o identidad. En NER, "Bogotá" o "Peñalosa" son parte del nombre y quitar la tilde puede romper la coincidencia con una base de entidades. En español la tilde distingue palabras (`el`/`él`, `si`/`sí`, `término`/`terminó`): para análisis de sentimiento, "esto sí funciona" y "esto si funciona" no son lo mismo. También conviene conservarlas si el modelo downstream es un Transformer entrenado con texto acentuado (BETO), porque su vocabulario espera las tildes. Quitarlas tiene sentido solo cuando el corpus viene inconsistente (chats, tweets) y el objetivo es un modelo de bolsa de palabras.

**Reflexión 2 — "desistimiento" fuera de vocabulario.**
1. Con tokenización por palabras el término es `<UNK>`: el buscador no lo distingue de cualquier otra palabra desconocida y la consulta pierde justo la palabra más informativa.
2. Con BPE se parte en subpalabras (`desist`, `##imiento`, por ejemplo); el modelo conserva la raíz y la relaciona con "desistir" y con otros sustantivos en `-miento`. La búsqueda degrada con gracia en lugar de fallar.
3. Por caracteres conviene cuando el dominio tiene mucha ortografía irregular o códigos (números de radicado, siglas, citas de artículos como "art. 174 CGP") y el vocabulario de subpalabras no los cubre; el costo es secuencias largas y más cómputo.

**Reflexión 3.5 — Limitaciones de BoW.** El clasificador funciona porque el dataset es pequeño y las palabras polares son explícitas. BoW ignora el orden, así que "no lo recomiendo" y "lo recomiendo" comparten casi todo el vector; con negación, ironía o jerga el rendimiento cae. Además cada palabra es una dimensión independiente: "pésimo" y "horrible" no se parecen para el modelo aunque sean sinónimos.

**Reflexión 3.6 — OOV.** El porcentaje de OOV crece con la distancia temporal y de dominio entre el corpus de entrenamiento y el de uso ("fintech", "nequi", "criptomoneda" no existían en el vocabulario de 2024). Mitigaciones: reentrenar el vectorizador periódicamente, usar subpalabras (BPE), o pasar a embeddings preentrenados sobre corpus grandes y recientes.

**Reflexión 3 — Perplejidad.** Una perplejidad alta para "el perro come pizza en el parque" dice que el modelo aprendió la distribución de **noticias financieras**, no del español: los bigramas de esa oración casi no aparecen en el corpus. No es que la oración sea "mala", es que está fuera de dominio. Bonus: con P = 0 en un solo bigrama, la probabilidad de la oración es 0, el logaritmo es −∞ y la perplejidad se vuelve infinita; el suavizado de Laplace reparte una masa pequeña a los bigramas no vistos para que eso no ocurra.

**Reflexión final.**
1. *N-grams vs. embeddings:* prefiero un N-gram cuando necesito latencia mínima y cero dependencias (autocompletado en un teclado, detección de idioma, corrección en un sistema embebido), cuando el corpus es pequeño y muy específico, o cuando debo explicar cada predicción con conteos auditables.
2. *Embeddings estáticos:* en noticias financieras "banco" (entidad) y "banco" (asiento) comparten vector, igual que "acción" (bursátil vs. acto) e "interés" (tasa vs. curiosidad). Un clasificador de sentimiento recibe una señal mezclada y puede asignar polaridad por el sentido equivocado; el problema se agrava en titulares cortos, donde hay poco contexto que compense.
3. *Auditoría antes de desplegar CVs:* medir la diferencia de similitud de cada rol con términos de género (como en el Experimento 8), evaluar la tasa de selección por grupo demográfico sobre un conjunto de CVs con nombres y pronombres intercambiados (test de contrafactuales), reportar métricas desagregadas (precisión, recall y tasa de falsos negativos por grupo) y documentar todo en una model card. Si el sesgo supera un umbral, aplicar debiasing o cambiar la representación.
4. *Gancho semana 2:* BERT calcula el vector de cada palabra **en función de las demás palabras de la oración** mediante atención: "banco" cerca de "depositar" y "banco" cerca de "parque" terminan en regiones distintas del espacio. El lab de la semana 2 lo muestra midiendo la similitud coseno entre los dos "banco".
