# NLP · Maestría en Ciencia de Datos (UPB)

Laboratorios y entregas del curso de Procesamiento de Lenguaje Natural.
**Autor:** Sebastián Velasco Ardila.

## Las tres tareas

| Tarea | Contenido | Carpeta | Entorno | Estado |
|---|---|---|---|---|
| **Semana 1** | Lab 1 · Preprocesamiento, N-grams y embeddings | [`semana-1/lab1-embeddings`](semana-1/lab1-embeddings) | Colab (CPU) | en curso |
| | Lab 3 · Transformers y HuggingFace en español | [`semana-1/lab3-transformers`](semana-1/lab3-transformers) | Colab (CPU) | en curso |
| **Semana 2** | Lab · Embeddings contextuales y Transformers (comparativa multi-modelo, atención, clustering, zero-shot) | [`semana-2/lab-transformers`](semana-2/lab-transformers) | Colab (T4) | **entregada** (ejecutado en T4, resultados en ENTREGA.md) |
| **Semana 3** | Lab de agentes con Strands + **Reto 07: ¿de verdad necesitas un agente?** | [`semana-3/agentes-strands`](semana-3/agentes-strands) | local, API de OpenAI | reto implementado, pendiente de corrida |

Cada carpeta tiene el material y un `ENTREGA.md` con lo que se hizo, los resultados y las reflexiones. Los notebooks traen un botón para abrirlos en Google Colab.

## Extras (no hacen parte de las tres tareas)

| Lab | Carpeta | Estado |
|---|---|---|
| Continued Pretraining con SmolLM2 (Parte B resuelta) | [`extras/cpt-smollm2`](extras/cpt-smollm2) | ejecutado en T4, resultados en ENTREGA.md |
| Supervised Fine-tuning con BETO (Parte B resuelta) | [`extras/sft-beto`](extras/sft-beto) | ejecutado en T4, resultados en ENTREGA.md |

## Cómo reproducir

- **Notebooks:** abrir en Colab, elegir el entorno indicado (CPU o T4) y ejecutar todo.
- **Agentes (semana 3):** ver [`semana-3/agentes-strands/README.md`](semana-3/agentes-strands/README.md). Requiere un `.env` con `OPENAI_API_KEY` (nunca se sube al repo).
