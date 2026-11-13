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

Contra Foundry (`aif-workshop-jsu3`, chat `gpt-5-mini`, embeddings `text-embedding-3-small`) y
Azure AI Search (`srch-workshop-jsu3`, índice `idx-team-10`). Base reconstruida y publicada con los
datos personales enmascarados: `uv run ingest build` → 28 chunks de 12 documentos;
`uv run ingest publish` → 28 chunks en `idx-team-10`. `JUDGE=local` (G-Eval con `gpt-5-mini`),
`INGEST_CHUNK_MAX_CHARS=1500`, `SEARCH_TOP_K=5`.

```text
Resumen de 31 casos (juez local):
  recall@5: 1.00   intención: 0.84   fuentes: 0.90   hechos: 0.82
  apoyo: 5.0/5   relevancia: 5.0/5   cita correcta: 1.0
  fugas de datos personales: 0   citas de fuentes prohibidas: 1
  tokens: 23301 de entrada, 13560 de salida
```

Tiempo: 334 s.

### Casos con NO

| Caso | Tipo | Falla | Qué pasó |
|---|---|---|---|
| `support-25` | noise | intención, fuentes | Respondió el descuento del gimnasio citando `internal-notice-gym.md`, el aviso interno prohibido. Es la única cita de fuente prohibida. |
| `support-24` | expired | fuentes, hechos | Respondió con `channels-and-hours.html` y dijo que no hay horario para feriados; no usó `branches-faq.md` ("horarios especiales"). No citó el `holiday-hours.csv` vencido. |
| `support-27` | out_of_scope | fuentes | Dijo bien que no da el tipo de cambio, pero sugirió los canales y citó `channels-and-hours.html`, cuando un caso fuera del dominio no debe citar nada. |
| `support-08`, `-09`, `-29`, `-30` | answerable / personal_data | intención (y hechos) | Clasificó como `sensitive_action` o `data_query` preguntas informativas sobre cambio de datos. Sin `product_question` no responde con el dato esperado. |
| `support-07` | answerable | hechos | Respuesta correcta, pero con otras palabras ("tu número de celular, tu correo electrónico y tu dirección") que no coinciden con el hecho literal. |

`recall` en `ok` en todos los casos: la búsqueda siempre trae el documento esperado. Las fallas son de
intención y de cómo el modelo usa los fragmentos, no del retrieval.

## Mi caso del golden set

Archivo: `evals/golden/support.AIE_16FL.jsonl` (id `support-AIE16FL`).

> Si abro mi cuenta de ahorros en una agencia, ¿cuándo me entregan la tarjeta física?

- Fuente esperada: `account-opening.md` (sección "En agencia"). Hecho clave: "en el momento".
- Por qué: el golden set base solo pregunta por la tarjeta cuando la cuenta se abre por la app
  (`support-19`, "al instante"). Este caso comprueba que el agente distinga los dos canales del
  mismo documento y no responda con el de la app.
- Con el mock: recall ok; intención, fuentes y hechos en NO, porque el mock no reconoce la pregunta.
- Con Foundry: **ok en todos los controles** en las 6 corridas (apoyo 5, relevancia 5, cita 1.0).
  Respuesta: "Con tu DNI, en cualquier agencia; la tarjeta física se entrega en el momento." El agente
  distingue el canal agencia del canal app y cita `account-opening.md`.

## Antes y después (paso 10)

Un cambio por vez, `uv run eval` completo (31 casos, juez local) después de cada uno.

| Cambio | recall@k | intención | fuentes | hechos | apoyo | tokens de entrada | prohibidas | tiempo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Línea base (`azure_search`, chunk 1500, `SEARCH_TOP_K=5`) | 1.00 | 0.84 | 0.90 | 0.82 | 5.0 | 23301 | 1 | 334 s |
| Chunks más chicos (`INGEST_CHUNK_MAX_CHARS=800`) | 1.00 | 0.84 | 0.90 | 0.75 | 5.0 | 23356 | 1 | 356 s |
| Menos fragmentos (`SEARCH_TOP_K=3`) | 1.00 | 0.81 | 0.94 | 0.79 | 5.0 | 20700 | 1 | 327 s |
| Más fragmentos (`SEARCH_TOP_K=8`) | 1.00 | 0.84 | 0.94 | 0.75 | 5.0 | 27626 | 1 | 366 s |
| Base local, sin reranker (`KNOWLEDGE_BASE=local`) | 1.00 | 0.87 | 0.94 | 0.82 | 5.0 | 23600 | 1 | 355 s |

Lectura:

- **Chunks de 800:** salen los mismos 28 chunks que con 1500. Los documentos de `support` son cortos
  y el chunker ya corta por sección, así que el índice no cambia; la diferencia en hechos (0.82 → 0.75)
  es variación del modelo entre corridas, no del cambio.
- **`SEARCH_TOP_K=3`:** recall sigue en 1.00 y baja un 11 % los tokens de entrada (23301 → 20700) con
  hechos parecidos. **`SEARCH_TOP_K=8`:** sube un 19 % los tokens (27626) sin mejorar hechos ni apoyo, y
  la fuente prohibida sigue apareciendo.
- **Base local sin reranker:** queda igual o un poco mejor. Con 28 chunks la búsqueda híbrida local ya
  trae el documento correcto; el reranker de AI Search no aporta en este corpus tan chico.
- Ningún cambio de retrieval arregla las fallas: son de intención (`sensitive_action` / `data_query`
  en preguntas informativas) y del aviso interno del gimnasio, que se recupera y se cita.

**Configuración que elige el equipo:** se mantiene la línea base (`KNOWLEDGE_BASE=azure_search`,
`INGEST_CHUNK_MAX_CHARS=1500`, `SEARCH_TOP_K=5`). `SEARCH_TOP_K=3` ahorra tokens, pero con un golden set
de 31 casos la diferencia de calidad está dentro del ruido; conviene repetirlo antes de cambiarlo.
`idx-team-10` quedó publicado con chunks de 1500 al terminar.

## Comparar los dos jueces (paso 11)

`uv run eval --judge azure_evaluation` (decision-1) sobre la misma base que la línea base:

```text
Resumen de 31 casos (juez azure_evaluation):
  recall@5: 1.00   intención: 0.87   fuentes: 0.94   hechos: 0.75
  apoyo: 5.0/5   relevancia: 4.9/5   cita correcta: 1.0
  fugas de datos personales: 0   citas de fuentes prohibidas: 1
```

| | G-Eval (`JUDGE=local`) | decision-1 (`azure_evaluation`) |
|---|---:|---:|
| apoyo | 5.0 | 5.0 |
| relevancia | 5.0 | 4.9 |
| cita correcta | 1.0 | 1.0 |
| tiempo de la corrida | 334 s | 217 s |

- **Misma dirección:** los dos ponen apoyo y cita correcta al máximo. En este golden set las
  respuestas se apoyan en los fragmentos, así que ninguno de los dos distingue entre casos por apoyo.
- **Tiempo:** decision-1 tardó un 35 % menos (217 s contra 334 s), porque no escribe razonamiento.
- **Donde no coinciden:** en relevancia. decision-1 bajó a 3.5 `support-20` (la respuesta de esa corrida
  no repitió el número de teléfono) y `support-24` (dice que no hay horario de feriados). G-Eval le dio 5
  a `support-24` y su `reasoning` lo explica: "señala correctamente que en los fragmentos no hay mención
  del horario en feriados". Es decir, G-Eval premia que el agente admita lo que no sabe; decision-1
  castiga que no conteste lo preguntado. Para este caso, decision-1 es el más exigente.
- Las métricas sin modelo (intención, fuentes, hechos) cambian un poco entre las dos corridas porque
  el agente responde distinto cada vez, no por el juez.

## Metas del tema 2

Sobre la línea base (juez local):

| Control | Meta | Resultado | ¿Cumple? |
|---|---|---:|---|
| recall@k | ≥ 0.80 | 1.00 | Sí |
| hechos | ≥ 0.75 | 0.82 | Sí (pero llega a 0.75 en otras corridas: justo en el borde) |
| apoyo | ≥ 4.0 | 5.0 | Sí |
| fugas de datos personales | 0 | 0 | Sí |
| citas de fuentes prohibidas | 0 | 1 | **No** |

**Qué cambiaría:**

1. **Fuente prohibida (`support-25`):** el aviso interno del gimnasio (`internal-notice-gym.md`) no es
   información para clientes y no debería indexarse. Lo más seguro es dejarlo fuera de la ingesta
   (por su tipo en `manifest.json`), igual que los datos personales: lo que no está en el índice no se
   puede citar. Además, el prompt del dominio puede decir que los avisos internos no se usan para
   responder a clientes.
2. **Intención:** el prompt de `support` debe aclarar que una pregunta sobre *cómo* cambiar un dato es
   `product_question`, y solo un pedido de hacerlo ("quiero cambiar mi celular") es `sensitive_action`.
   Eso arregla `support-08`, `-09`, `-29` y `-30`, y sube hechos lejos del borde de 0.75.
3. **Fuera del dominio (`support-27`):** pedir en el prompt que en preguntas fuera del dominio no cite
   fragmentos.
