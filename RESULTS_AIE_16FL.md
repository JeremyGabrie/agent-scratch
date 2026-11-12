# Resultados · Sesión 5 · Calidad del RAG (AIE_16FL)

Dominio: `support`. Rama: `s5_AIE_16FL`, creada desde `equipo-10` (= `t2-s4`).

## Pruebas

`uv run pytest` → **86 passed**.

## Datos personales fuera del índice (paso 3)

`uv run ingest build` → 28 chunks de 12 documentos. En `data/chunks/support.json` quedaron 2 datos
enmascarados (`[DNI]` / `[TARJETA]`) y ningún DNI de 8 dígitos. La única coincidencia del patrón
`(?<![.\d])\d{8}\b` es el `id` (UUID) de un chunk, que no es un dato personal.

## Prueba con el mock (paso 8)

Con `dev/mock_foundry.py` y `KNOWLEDGE_BASE=local`. Los números no significan nada: el mock clasifica
por palabras clave del dominio `fraud` y no entiende las preguntas de `support`; solo prueban el flujo.

| Corrida | Casos | recall@5 | intención | fuentes | hechos | apoyo | relevancia | cita | fugas | prohibidas |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `uv run eval --limit 6` (G-Eval) | 6 | 1.00 | 0.00 | 0.00 | 0.00 | 4.0 | 4.0 | 0.8 | 0 | 0 |
| `uv run eval --limit 2 --judge azure_evaluation` | 2 | 1.00 | 0.00 | 0.00 | 0.00 | 2.0 | 2.0 | 0.2 | 0 | 0 |
| `uv run eval` (G-Eval) | 31 | 1.00 | 0.10 | 0.10 | 0.00 | 4.0 | 4.0 | 0.8 | 0 | 0 |

## Línea base (S5)

Pendiente: correr `uv run ingest build`, `uv run ingest publish` y `uv run eval` contra Foundry y
AI Search (`idx-team-10`) con el `.env` del equipo, y copiar aquí el resumen.

## Mi caso del golden set

Archivo: `evals/golden/support.AIE_16FL.jsonl` (id `support-AIE16FL`).

> Si abro mi cuenta de ahorros en una agencia, ¿cuándo me entregan la tarjeta física?

- Fuente esperada: `account-opening.md` (sección "En agencia"). Hecho clave: "en el momento".
- Por qué: el golden set base solo pregunta por la tarjeta cuando la cuenta se abre por la app
  (`support-19`, "al instante"). Este caso comprueba que el agente distinga los dos canales del
  mismo documento y no responda con el de la app.
- Con el mock: recall ok; intención, fuentes y hechos en NO, porque el mock no reconoce la pregunta.
  Pendiente ver cómo le va con Foundry.

## Antes y después (paso 10)

Pendiente, contra Foundry. Un cambio por vez y `uv run eval` completo después de cada uno.

| Cambio | recall@5 | hechos | apoyo | tokens de entrada | fuentes prohibidas |
|---|---:|---:|---:|---:|---:|
| Línea base (`INGEST_CHUNK_MAX_CHARS=1500`, `SEARCH_TOP_K=5`) | | | | | |
| Chunks más chicos (`INGEST_CHUNK_MAX_CHARS=800`) | | | | | |
| Menos fragmentos (`SEARCH_TOP_K=3`) | | | | | |
| Más fragmentos (`SEARCH_TOP_K=8`) | | | | | |
| Base local, sin reranker (`KNOWLEDGE_BASE=local`) | | | | | |

## Comparar los dos jueces (paso 11)

Pendiente: `uv run eval --judge azure_evaluation` con el deployment decision-1 y comparar con la
corrida de `JUDGE=local` (dirección de apoyo y cita correcta, tiempo de cada corrida, casos donde no
coinciden).

## Metas del tema 2

| Control | Meta | Resultado |
|---|---|---|
| recall@k | ≥ 0.80 | pendiente (Foundry) |
| hechos | ≥ 0.75 | pendiente (Foundry) |
| apoyo | ≥ 4.0 | pendiente (Foundry) |
| fugas de datos personales | 0 | 0 con el mock |
| citas de fuentes prohibidas | 0 | 0 con el mock |
