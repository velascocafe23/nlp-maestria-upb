# Entrega 4 · Lab CPT: Continued Pretraining de SmolLM2-135M

**Autor:** Sebastián Velasco Ardila · **Entorno:** Google Colab (GPU T4)
**Notebook:** [`lab_cpt_smollm2.ipynb`](lab_cpt_smollm2.ipynb) ([abrir en Colab](https://colab.research.google.com/github/velascocafe23/nlp-maestria-upb/blob/main/04-cpt-smollm2/lab_cpt_smollm2.ipynb))

## Qué se hizo

- **Parte A (guiada):** CPT de `SmolLM2-135M` con tweets en español (3 epochs, lr 5e-5, chunks de 128 tokens), perplexity antes y después sobre el split `test`.
- **Parte B (reto, pasos 11–15):** el mismo patrón con el corpus financiero `nojedag/financial_phrasebank_multilingual`, filtrado a español, partiendo del **modelo base recargado**. Reutilicé `tokenize_corpus`, `calcular_perplexity` y `generar`, y mantuve los mismos hiperparámetros de la Parte A para que la única diferencia entre las dos adaptaciones sea el corpus.
- **Extras:** generación "antes vs. después" con la misma semilla para los prompts financieros; medición del **olvido cruzado** (perplexity del modelo financiero sobre el holdout de tweets, paso 15b); tabla resumen de las dos adaptaciones (15c).

Un detalle del dataset que el hint del enunciado no advierte: `lang` no es un string sino un `ClassLabel` (entero, `es` = 3). Filtrar con `x["lang"] == "es"` devuelve 0 filas sin error. En el notebook el código le pregunta al dataset el id de `"es"` (`features["lang"].str2int`) y un `assert` protege contra un filtro vacío.

## Resultados

_(se completan con la corrida en T4)_

| Dominio | Chunks train | Chunks holdout | PPL antes | PPL después | Reducción |
|---|---|---|---|---|---|
| Tweets (Parte A) | | | | | |
| Financiero (Parte B) | | | | | |

Olvido cruzado: perplexity en tweets del modelo financiero = _(x)_ frente a _(x)_ del modelo base (_(±x %)_).

Generación financiera (prompt → después del CPT): _(pegar 3 ejemplos)_.

## Reflexión final (paso 16)

_Borrador a confirmar con los números._

- **Tweets vs. financiero.** Espero que la perplexity financiera **parta más alta** (SmolLM2 fue preentrenado mayoritariamente en inglés y el corpus financiero es español formal, traducido automáticamente) y que **baje más en términos relativos**, por dos razones: el corpus financiero es más homogéneo (frases de prensa económica con vocabulario repetitivo) y el holdout se parece mucho al train, mientras los tweets son ruidosos (hashtags, menciones, ortografía libre) y un modelo pequeño con tres epochs no alcanza a modelar esa variedad. Si la reducción financiera resulta menor, la explicación más probable es el tamaño del corpus en español tras el filtro.
- **Estilo generado.** Las muestras tras el CPT financiero deberían sonar a titular de prensa económica (sujeto institucional, verbos en pasado, cifras y porcentajes), frente al registro corto e informal de los tweets de la Parte A. El CPT cambia vocabulario **y** registro, aunque la coherencia factual siga siendo pobre: es un modelo de 135M que no sabe qué decidió el Banco de la República, solo cómo suena una frase que lo dice.
- **Partir del modelo base.** Entrenar el financiero encima del modelo ya adaptado a tweets habría mezclado dos efectos: lo que aporta el corpus financiero y lo que arrastra el de tweets (y su olvido). La perplexity "antes" habría sido la de un modelo ya movido, y la comparación tweets-vs-financiero dejaría de ser entre pares.
- **Olvido catastrófico.** El extra 15b lo mide: si la perplexity en tweets del modelo financiero sube respecto al base, el CPT estrecho costó capacidad fuera del dominio. Es el precio de adaptar sin mezclar datos generales.
- **En producción.** Para un modelo experto en lenguaje financiero haría CPT **mezclando** el corpus del dominio con una fracción de texto general en español (replay) y con learning rate más bajo o LoRA, para no perder el español general; luego SFT para la tarea concreta. CPT vale la pena cuando el dominio tiene vocabulario y registro propios que el modelo base no cubre y hay un corpus de millones de tokens; si el problema es de conocimiento factual actualizado (qué pasó con la tasa esta semana), RAG es más barato y verificable; y si solo hace falta tono o formato, prompting basta.
