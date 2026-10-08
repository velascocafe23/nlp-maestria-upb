# Extra · Lab CPT: Continued Pretraining de SmolLM2-135M

**Autor:** Sebastián Velasco Ardila · **Entorno:** Google Colab (GPU Tesla T4) · **Ejecutado:** 7 de octubre de 2026
**Notebook:** [`lab_cpt_smollm2.ipynb`](lab_cpt_smollm2.ipynb) ([abrir en Colab](https://colab.research.google.com/github/velascocafe23/nlp-maestria-upb/blob/main/extras/cpt-smollm2/lab_cpt_smollm2.ipynb)) — ejecutado de principio a fin, sin errores, con las salidas guardadas.

## Qué se hizo

- **Parte A (guiada):** CPT de `SmolLM2-135M` con tweets en español (3 epochs, lr 5e-5, chunks de 128 tokens), perplexity antes y después sobre el split `test`.
- **Parte B (reto, pasos 11–15):** el mismo patrón con el corpus financiero `nojedag/financial_phrasebank_multilingual`, filtrado a español, partiendo del **modelo base recargado**. Reutilicé `tokenize_corpus`, `calcular_perplexity` y `generar`, y mantuve los mismos hiperparámetros de la Parte A para que la única diferencia entre las dos adaptaciones sea el corpus.
- **Extras:** generación "antes vs. después" con la misma semilla para los prompts financieros; medición del **olvido cruzado** (perplexity del modelo financiero sobre el holdout de tweets, paso 15b); tabla resumen de las dos adaptaciones (15c).

Un detalle del dataset que el hint del enunciado no advierte: `lang` no es un string sino un `ClassLabel` (entero, `es` = 3). Filtrar con `x["lang"] == "es"` devuelve 0 filas sin error. En el notebook el código le pregunta al dataset el id de `"es"` (`features["lang"].str2int`) y un `assert` protege contra un filtro vacío.

## Resultados

| Dominio | Frases | Chunks train | Chunks holdout | PPL antes | PPL después | Reducción |
|---|---|---|---|---|---|---|
| Tweets (Parte A) | 1 839 | 456 | 218 | 106,05 | 51,84 | 51,1 % |
| Financiero (Parte B) | 4 089 | 1 575 | 679 | 49,20 | 21,76 | 55,8 % |

Pérdida de entrenamiento del CPT financiero: 3,78 → 3,06 (promedio del epoch 3), bajando de forma sostenida; en tweets la pérdida se estanca en ~3,93 desde el epoch 2.

**Olvido cruzado (15b).** Perplexity sobre el holdout de **tweets**: modelo base 106,05 · tras CPT con tweets 51,84 · **tras CPT financiero 78,32** (−26,1 % respecto al base).

**Generación financiera, antes → después** (misma semilla):

- *El Banco de la República decidió* → antes: "ser alcune personas que ha entre todo el mundo…" · después: "adquirir el 25,0 millones en donde parece una comunidad más liderativa que sus cuestiones con las empresas…"
- *Las acciones de Ecopetrol* → antes: "se han cumplido con la siguiente actividad: - El proceso desarrollado…" · después: "Estados Unidos deben tener en el conjunto que se encuentra al 2015, esta publicación tiene su valor del $48."
- *La inflación en Colombia* → antes: "1980–2065 (in Spanish). Universidad de Valencia. p. 473-ISBN…" · después: "5.08 % , el total de almacenamiento ahora recuperado sucede ."

Nota sobre la Parte A: el mensaje del paso 8 dice "Cambio relativo: +51.1% (negativo = mejoró)"; la fórmula del lab calcula `(antes − después)/antes`, así que el signo positivo **sí** es mejora. Es un error de texto del material, no del resultado.

## Reflexión final (paso 16)

**Tweets vs. financiero: ¿dónde bajó más la perplexity?** En términos relativos el financiero bajó un poco más (55,8 % vs. 51,1 %), pero la diferencia de partida es la más reveladora: el modelo base ya estaba más cómodo con el texto financiero (49 de perplexity) que con los tweets (106). SmolLM2 fue preentrenado sobre web y texto educativo, y la prosa de prensa económica, aun traducida, se parece a eso; los tweets, con jerga, insultos y ortografía libre, son un dominio lejano. Tres factores explican que el financiero se adapte mejor: el corpus es **3,5 veces más grande** (1 575 chunks vs. 456), es **más homogéneo** (frases cortas y formales de un mismo género) y el holdout se parece mucho al train. En tweets la pérdida se estanca en ~3,93 desde el segundo epoch: con 456 chunks el modelo ya vio todo lo que había que ver.

**Estilo generado.** El cambio de registro es visible aunque la coherencia factual siga siendo pobre, como corresponde a un modelo de 135M. Antes del CPT los prompts financieros derivaban a referencias bibliográficas, listas o incluso código Java (Parte A); después aparecen cifras con formato de prensa ("25,0 millones", "5.08 %", "$48"), años y vocabulario corporativo ("adquirir", "empresas", "valor"). El CPT no le enseñó qué decidió el Banco de la República, le enseñó cómo suena una frase que lo cuenta: vocabulario **y** registro, que es lo que el CPT puede dar.

**Partir del modelo base.** Entrenar el financiero encima del modelo ya adaptado a tweets habría mezclado dos efectos: lo que aporta el corpus financiero y lo que arrastra el de tweets. La perplexity "antes" del financiero no habría sido 49,20 sino la de un modelo ya movido, y la comparación 51 % vs. 56 % no tendría sentido porque las dos adaptaciones no habrían arrancado del mismo punto.

**¿Hubo olvido catastrófico?** Aquí el resultado contradijo mi expectativa, y vale la pena decirlo. Esperaba que el modelo financiero empeorara en tweets; en cambio **mejoró**: de 106,05 a 78,32. La explicación más plausible es que, para un modelo preentrenado sobre todo en inglés, 1 575 chunks de español formal enseñan sobre todo **español** (morfología, concordancia, palabras frecuentes), y eso transfiere a cualquier texto en español, tweets incluidos. Con un modelo base ya fuerte en español, o con muchos más epochs sobre el corpus estrecho, el olvido sí aparecería; con tres epochs y un modelo que partía con poco español, la adaptación al dominio todavía es, en buena parte, adaptación al idioma. Que la mejora en tweets por CPT financiero (−26 %) sea la mitad de la que da el CPT con los propios tweets (−51 %) muestra que el resto sí es específico del dominio.

**En producción.** Para un modelo experto en lenguaje financiero haría CPT mezclando el corpus del dominio con una fracción de texto general en español (replay), con learning rate más bajo o LoRA, y midiendo la perplexity fuera del dominio en cada checkpoint, como hizo el paso 15b, para detectar el olvido cuando empiece a aparecer y no suponerlo. CPT vale la pena cuando el dominio tiene vocabulario y registro propios que el modelo base no cubre y hay un corpus de millones de tokens disponible. Si el problema es de conocimiento factual actualizado (qué pasó con la tasa esta semana), RAG es más barato y verificable; y si solo hace falta tono o formato, prompting basta.
