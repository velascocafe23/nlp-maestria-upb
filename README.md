# NLP · Maestría en Ciencia de Datos (UPB)

Laboratorios y entregas del curso de Procesamiento de Lenguaje Natural.
**Autor:** Sebastián Velasco Ardila.

| # | Entrega | Carpeta | Entorno | Estado |
|---|---|---|---|---|
| 1 | Lab 1 · Preprocesamiento, N-grams y embeddings | [`semana-1/lab1-embeddings`](semana-1/lab1-embeddings) | Colab (CPU) | en curso |
| 2 | Lab 3 · Transformers y HuggingFace | [`semana-1/lab3-transformers`](semana-1/lab3-transformers) | Colab (CPU) | en curso |
| 3 | Lab · Embeddings contextuales y Transformers (semana 2) | [`semana-2/lab-transformers`](semana-2/lab-transformers) | Colab (T4) | en curso |
| 4 | Lab · Continued Pretraining con SmolLM2 | [`extras/cpt-smollm2`](extras/cpt-smollm2) | Colab (T4) | **entregada** (ejecutado en T4, resultados en ENTREGA.md) |
| 5 | Lab · Supervised Fine-tuning con BETO | [`extras/sft-beto`](extras/sft-beto) | Colab (T4) | Parte B resuelta, pendiente de ejecución |
| 6 | Lab · Agentes con Strands + Reto 07 | [`semana-3/agentes-strands`](semana-3/agentes-strands) | local, API de OpenAI | reto implementado, pendiente de corrida |

Cada carpeta tiene el material y un `ENTREGA.md` con lo que se hizo, los resultados y las reflexiones.
Los notebooks traen un botón para abrirlos en Google Colab.

## Cómo reproducir

- **Notebooks (entregas 1 a 5):** abrir en Colab, elegir el entorno indicado (CPU o T4) y ejecutar todo.
- **Agentes (entrega 6):** ver [`semana-3/agentes-strands/README.md`](semana-3/agentes-strands/README.md). Requiere un `.env` con `OPENAI_API_KEY` (nunca se sube al repo).
