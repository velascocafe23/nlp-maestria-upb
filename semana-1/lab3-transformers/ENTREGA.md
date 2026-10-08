# Semana 1 · Lab 3: Transformers y HuggingFace en Español

**Autor:** Sebastián Velasco Ardila · **Entorno:** Google Colab (CPU)
**Notebook:** [`lab3_transformers.ipynb`](lab3_transformers.ipynb) ([abrir en Colab](https://colab.research.google.com/github/velascocafe23/nlp-maestria-upb/blob/main/semana-1/lab3-transformers/lab3_transformers.ipynb))

## Qué se hizo

Ejecuté el notebook guiado completo: demostración de la limitación de GloVe (un vector por palabra), pipelines de HuggingFace para sentimiento (`pysentimiento/robertuito-sentiment-analysis`) y NER (`mrm8488/bert-spanish-cased-finetuned-ner`), embeddings contextuales con BETO sobre la palabra "banco" en dos oraciones, y el esqueleto conceptual de fine-tuning con LoRA.

## Resultados observados

_(se completan con la salida de la ejecución)_

- Similitud coseno entre los dos "banco" de BETO: _(x)_ (con GloVe sería 1.000).
- `banco(financiero) ~ dinero` = _(x)_; `banco(parque) ~ parque` = _(x)_.
- Sentimiento: _(n)_ de 10 tweets clasificados como esperaba; casos dudosos: _(…)_.
- NER: entidades bien detectadas _(…)_; partidas o confundidas _(…)_.

## Reflexiones

**Reflexión 1 — Estáticos vs. contextuales.** Un único vector por palabra obliga a promediar todos los sentidos de "banco", "gato" o "vela" en un mismo punto; el resultado no representa bien ninguno. Para elegir el sentido el modelo necesita el contexto de la oración (las palabras vecinas y su orden). Las analogías de Word2Vec/GloVe demuestran que el espacio captura relaciones **entre palabras**, pero siguen operando sobre un vector fijo por tipo, así que no pueden separar dos usos de la misma forma escrita.

**Reflexión 2a — Transformer vs. modelo clásico.**
1. El Transformer acierta donde hay negación o contraste ("no vuelvo a comprar nunca más", "aún no lo he abierto" como neutro) porque atiende al orden; BoW ve "comprar" y "abierto" como palabras sueltas.
2. Prefiero TF-IDF + LogReg cuando necesito explicar la predicción (auditoría, regulación), cuando no hay GPU y el volumen es alto, o cuando la tarea es temática con vocabulario marcado y el F1 ya es suficiente.
3. Un modelo preentrenado con tweets genéricos puede fallar con la jerga, los productos y la ironía de **mi** dominio; sin validarlo con una muestra etiquetada propia no sé cuánto confiar en él, y sus errores son silenciosos.

**Reflexión 2b — NER.** "Banco de la República" es difícil porque "República" se parece a un lugar y el nombre es compuesto; el modelo tiende a partirlo o etiquetarlo como LOC. Usaría NER para leer contratos y extraer partes y montos, para monitorear noticias de competidores y para enlazar menciones de clientes en PQRs con la base de datos. BoW no sirve porque la tarea es **secuencial**: hay que etiquetar cada token según su posición y sus vecinos, no contar palabras del documento.

**Reflexión 3 — Embeddings contextuales.** La similitud es < 1 porque cada capa de atención recombina el vector de "banco" con los de las palabras que lo rodean; la información sale de esos vecinos ("depositar", "dinero" vs. "senté", "parque"). Como features para un clasificador usaría el mean pooling del `last_hidden_state` (o el `[CLS]` si el modelo está afinado) y entrenaría una regresión logística encima: es exactamente el baseline del lab de SFT.

**Reflexión 4 — Fine-tuning y LoRA.**
1. Entrenar < 1 % de los parámetros funciona porque la adaptación a una tarea nueva ocupa un subespacio de bajo rango: los pesos preentrenados ya saben el idioma y solo hace falta un ajuste pequeño en las proyecciones de atención.
2. Con cinco clientes, cinco adaptadores de pocos MB sobre un mismo modelo base son más baratos de guardar, servir y versionar que cinco copias de 440 MB; además se pueden cargar y descargar en caliente.
3. No vale la pena afinar cuando un pipeline preentrenado ya cumple la métrica objetivo sobre mis propios datos, cuando tengo muy pocos ejemplos etiquetados, o cuando la tarea cambia tan rápido que no hay tiempo de reentrenar (ahí conviene prompting o zero-shot).

**Reflexiones finales.**
1. GloVe da a "banco" un punto fijo; BERT da un punto por aparición, calculado con la oración completa.
2. Un pipeline tokeniza, pasa por el modelo y formatea la salida; eso quita el 90 % del código repetitivo y permite probar un modelo en minutos.
3. Para 500 tweets al día con necesidad de interpretar, usaría una combinación: TF-IDF + LogReg como modelo principal (explicable, barato) y el Transformer como segunda opinión para los casos de baja confianza o con negación.
4. Para afinar con datos propios haría falta un conjunto etiquetado (unos cientos a miles de ejemplos), una GPU modesta, una cabeza de clasificación sobre el encoder y un bucle de entrenamiento con validación; con LoRA el costo baja aún más. Es exactamente lo que se hace en el lab de SFT con BETO.
