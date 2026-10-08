# Semana 2 · Lab Transformers: embeddings contextuales, comparativa multi-modelo, atención, clustering y zero-shot

**Autor:** Sebastián Velasco Ardila · **Entorno:** Google Colab (GPU Tesla T4) · **Ejecutado:** 7 de octubre de 2026
**Notebook:** [`lab_transformers_semana2.ipynb`](lab_transformers_semana2.ipynb) ([abrir en Colab](https://colab.research.google.com/github/velascocafe23/nlp-maestria-upb/blob/main/semana-2/lab-transformers/lab_transformers_semana2.ipynb)) — ejecutado de principio a fin, sin errores, con las salidas guardadas.

## Qué se hizo

Ejecuté el notebook completo en T4, incluido el bonus de zero-shot: GloVe vs. BETO sobre "banco", pipelines de sentimiento y NER con tweets y noticias financieras colombianas, comparativa de tres modelos de sentimiento (tamaño, tiempo, accuracy, F1), visualización de atención (bertviz y heatmap), clustering de tweets con t-SNE y clasificación zero-shot con `xlm-roberta-large-xnli`.

## Resultados observados

**Estático vs. contextual.** GloVe: similitud de `bank` consigo mismo en dos contextos = **1,000** (mismo vector); `bank` se parece más a `credit` (0,70), `money` (0,57) y `loan` (0,55) que a `river` (0,33) o `bench` (0,11), y eso no cambia con la oración. BETO: similitud entre el "banco" de *"Fui al banco a sacar plata"* y el de *"Me senté en el banco del parque"* = **0,855**; cada uno se acerca a su contexto (`banco~plata` 0,81, `banco~parque` 0,85).

**Sentimiento (RoBERTuito).** 10 de 10 tweets como esperaba. El más dudoso: *"Según el DANE la inflación de este mes fue del 0,3 %"*, neutro con 0,53 frente a 0,42 negativo: el modelo asocia "inflación" con mala noticia.

**NER.** Bien: `Bancolombia`, `Banco de la Republica`, `Bolsa de Valores de Colombia`, `Grupo Nutresa`, `Avianca`, `Airbus` (ORG), `Leonardo Villar` (PER), `America Latina`, `Colombia` (LOC). Partidas en sub-tokens pese a `aggregation_strategy='simple'`: `Medell`/`##in`, `Bogo`/`##ta`, `Eco`/`##petrol`, `Ne`/`##qui` (los nombres sin tilde y las marcas nuevas no están en el vocabulario de BETO y el modelo etiqueta cada pieza por separado).

**Comparativa multi-modelo (10 tweets, etiqueta de oro propia):**

| Modelo | Tamaño (MB) | Tiempo (s) | Accuracy | F1 |
|---|---|---|---|---|
| RoBERTuito (ES, tweets) | **415** | 0,151 | **1,00** | **1,000** |
| BERT multilingüe (5★, reseñas) | 638 | **0,089** | 0,70 | 0,552 |
| RoBERTa Twitter (EN) | 476 | 0,237 | 0,50 | 0,404 |

**Atención (capa 3, cabeza 3).** `banco → Colombia` (0,20), `central → Colombia` (0,21), `Colombia → banco` (0,14), `tasa → interes` (0,22), `de → interes` (0,21). La tokenización parte `subió` en `sub`/`##io`.

**Clustering (t-SNE de embeddings BETO, mean pooling).** Tres franjas claras sin haberle dicho el sentimiento al modelo: los cuatro positivos arriba, los tres negativos en el centro, los tres neutros (Ecopetrol, Banco de la República, DANE) abajo. Ningún tweet quedó rodeado de otro color.

**Zero-shot (5 tweets, 5 categorías nuevas).** 3 de 5 aciertos. Correctos: elogio al producto (0,985), consulta de horario (0,946), requisitos de crédito (0,885). Fallos: la devolución de dinero no reconocida salió *consulta de información* (0,71) en vez de *queja de servicio* (0,18); el mensaje sospechoso pidiendo la clave salió *consulta de información* (0,69) en vez de *reporte de fraude* (0,26).

## Reflexiones

**Reflexión 1 — Estáticos vs. contextuales.** En finanzas la polisemia es la norma: "banco", "cuenta", "interés", "acción", "bono", "cartera". GloVe les da un vector único que promedia sentidos; lo vimos con `bank`, que queda más cerca de `credit` que de `river` porque en el corpus de Wikipedia domina el sentido financiero, pero esa mezcla es la misma en *"bank of the river"*. El modelo necesita el contexto sintáctico y léxico de la oración; las analogías de GloVe muestran estructura entre palabras, no resuelven dos usos de la misma forma.

**Reflexión 2a — Transformer vs. clásico.** BoW falla en *"no puedo pagar nada"* y *"no autoricé"* porque trata la negación como una palabra más; RoBERTuito les dio 0,98 y 0,84 de negativo. Aun así preferiría TF-IDF + LogReg en un banco cuando la regulación exige explicar la decisión (SARLAFT, PQRs auditables) o cuando el volumen es masivo y no hay GPU. El riesgo de usar un modelo de tweets genéricos sin validar lo mostró el tweet del DANE: 0,42 de negativo para un dato neutro, porque "inflación" en Twitter suele venir con queja. Con jerga local, nombres de productos y sarcasmo esas desviaciones crecen y nadie las ve hasta que un reporte sale mal.

**Reflexión 2b — NER.** El modelo resolvió bien "Banco de la República" (ORG, 1,00), que yo esperaba problemático; lo que falló fue más básico: partir `Medellín`, `Bogotá`, `Ecopetrol` y `Nequi` en pedazos, porque los escribimos sin tilde o son marcas nuevas que no están en el vocabulario de BETO y el agrupador no las une cuando las etiquetas de los sub-tokens difieren en confianza. Lección práctica: no quitar tildes antes de NER (justo lo contrario de lo que haríamos para BoW) y, para marcas locales, afinar o añadir un diccionario de post-proceso. Usos reales: extracción de partes y montos en contratos, monitoreo de noticias de competencia, enlace de menciones de clientes en PQRs. BoW no sirve porque la salida es una etiqueta por token en secuencia, no un conteo por documento.

**Reflexión 3 — Embeddings contextuales.** La similitud de 0,855 (no 1,0) sale de la atención: capa tras capa el vector de "banco" se recombina con los de sus vecinos, y por eso termina más cerca de "plata" en una oración y de "parque" en la otra. Que siga siendo 0,85 y no 0,3 también dice algo: BETO conserva la identidad léxica de la palabra y solo la desplaza; el contexto ajusta, no borra. Como features para un clasificador usaría el mean pooling del `last_hidden_state` con una regresión logística encima, que es exactamente el baseline de los labs de fine-tuning.

**Comparativa multi-modelo — ¿gana el más grande?** No: ganó el **más pequeño**. RoBERTuito (415 MB) sacó F1 = 1,00 porque está en el idioma y el dominio correctos; el multilingüe de reseñas (638 MB, el más grande) se quedó en 0,55 porque su noción de sentimiento viene de estrellas de producto y colapsar 5 clases a 3 pierde el matiz de los neutros; y el de Cardiff, un buen modelo en inglés, cayó a 0,40 sobre español. El tiempo fue parejo (0,09–0,24 s para 10 tweets) y el más rápido fue el multilingüe, así que aquí no hay dilema velocidad-precisión: el ajuste idioma-dominio domina todo. Para un banco que responde tweets en tiempo real priorizaría latencia solo si la diferencia de accuracy fuera de pocos puntos; con brechas de 30 y 50 puntos como estas, la precisión manda. Al colapsar 5 estrellas perdemos la intensidad (1★ y 2★ se vuelven iguales); conservaría la escala fina para priorizar las quejas más graves.

**Atención.** En la capa 3, cabeza 3, "banco" y "central" atienden ambos a "Colombia", y "Colombia" devuelve la atención a "banco": las tres palabras se enlazan como una sola entidad ("banco central de Colombia"), que es justo lo que la diapositiva de multi-head attention describe. "tasa" atiende a "interés" (0,22), otro compuesto nominal. Varias cabezas permiten capturar relaciones distintas a la vez (vecindad, sintaxis, compuestos, dependencias largas) que una sola matriz tendría que mezclar. Esa capacidad de juntar "banco" con "central" y "Colombia" es la que separa el banco financiero del banco del parque.

**Clustering.** Los colores se agruparon solos: positivos arriba, negativos en el centro, neutros abajo, y ningún punto en zona equivocada. Lo más nítido es la separación de los neutros (noticias del DANE, Ecopetrol, Banco de la República): BETO sin afinar codifica con fuerza el **registro** (noticia impersonal vs. opinión en primera persona), y dentro de la opinión también separa la polaridad. Con 10 puntos y t-SNE la forma exacta no es generalizable, pero la tendencia coincide con lo que después mide el F1 del baseline en el lab de SFT: las representaciones congeladas ya traen mucha señal.

**Zero-shot.** El modelo convierte cada categoría en una hipótesis ("Este texto es una queja de servicio") y decide por implicación con lo que aprendió en NLI. Acertó 3 de 5 y los dos fallos son instructivos: la devolución de dinero y el mensaje sospechoso fueron a *consulta de información*, que actúa como categoría "comodín" porque casi cualquier mensaje a un banco se puede leer como consulta. En el de fraude dudó (0,69 vs. 0,26), así que un umbral de confianza lo habría mandado a revisión humana. Para el canal de un banco propondría categorías más excluyentes y con verbos de acción: queja o reclamo, consulta de información, solicitud de producto, reporte de fraude o suplantación, bloqueo de tarjeta, felicitación. Ventaja: categorías nuevas sin reentrenar ni etiquetar; desventajas: modelo grande (~0,6 B parámetros), lento, y una precisión de 60 % que un clasificador supervisado con unos cientos de ejemplos superaría con facilidad.

**Paso 4 — ¿Transformer o BoW?** En mi trabajo los textos son descripciones de tickets, logs y documentación técnica: vocabulario marcado y poca ironía, así que BoW/TF-IDF resuelve la mayoría de la clasificación temática. El costo real de la GPU es menos el precio por hora que la operación (despliegue, escalado, latencia p99); solo se justifica si la mejora de precisión cambia una decisión de negocio. Si el 95 % se resuelve con BoW, diseñaría una cascada: BoW por defecto y, cuando su probabilidad esté por debajo de un umbral o el texto tenga negación detectada, pasar el caso al Transformer. Los resultados de hoy refuerzan la idea: el modelo correcto para el idioma y el dominio vale más que el modelo grande.

**Reflexiones finales.**
1. GloVe: un vector por tipo (similitud 1,000 entre dos usos); BETO: un vector por aparición (0,855), construido con la oración entera.
2. Un pipeline tokeniza, infiere y formatea; permite probar tres modelos de sentimiento en una celda, como hicimos en la comparativa.
3. Para 5 000 tweets/día con necesidad de explicar: cascada BoW + Transformer, con RoBERTuito solo para los casos dudosos o con negación, y un registro de las palabras que pesaron en cada decisión del modelo clásico.
4. Para afinar con datos del propio banco: un conjunto etiquetado de cientos a miles de tweets, una cabeza de clasificación sobre BETO, GPU y validación por clase. Es exactamente lo que hace el lab de SFT (en `extras/sft-beto`), donde el baseline con BETO congelado da F1 0,59 y el fine-tuning sube a 0,64.
