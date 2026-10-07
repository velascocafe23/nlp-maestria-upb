# Entrega 6 · Agentes con Strands + Reto 07: ¿de verdad necesitas un agente?

**Autor:** Sebastián Velasco Ardila · **Entorno:** local (Python 3.10+), API de OpenAI (`gpt-5.6-luna` vía `OpenAIResponsesModel`)

## Contenido

| Carpeta | Qué es | Estado |
|---|---|---|
| `00-setup` … `06-multiagente` | Módulos guiados del laboratorio (modelo + system prompt, agent loop, `@tool`, varias herramientas, memoria, agente como herramienta) | ejecutados |
| `07-reto/` | **El reto.** `reto.py` (dominio propio, tres arquitecturas, banco de casos), `ANALISIS.md` (informe), `resultados.csv` (corrida reportada) | ver abajo |
| `07-reto/ejemplo-inventario/` | La plantilla original del reto y el CSV de ejemplo del inventario, conservados como referencia | — |

## El reto en una línea

Asistente de reservas para apartamentos turísticos en Armenia, Quindío, resuelto con (A1) reglas en código sin LLM, (A2) un agente con cinco herramientas y (A3) un orquestador con tres especialistas; mismo esquema Pydantic, 10 casos en seis categorías, 3 repeticiones. El análisis completo, con hipótesis previas, tablas y recomendación, está en [`07-reto/ANALISIS.md`](07-reto/ANALISIS.md).

## Cómo reproducir

```bash
cd 06-agentes-strands
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # y poner OPENAI_API_KEY=sk-...
cd 07-reto
python reto.py --solo-a1        # baseline, sin API: corre en milisegundos
python reto.py                  # experimento completo: 90 corridas, ~15 min
```

Los datos del dominio (catálogo, calendario, políticas) viven en memoria dentro de `reto.py`: el experimento no depende de internet más allá de la API del modelo.
