# Resultados · AIE-38DH (Equipo 10, dominio `support`)

## Sesión 2 · Servicio IA

Mediciones contra Microsoft Foundry (`aif-workshop-jsu3`, deployment `gpt-5-mini`, modelo `gpt-5-mini-2025-08-07`), autenticación Entra ID (`az login`), `MAX_TURNS=10`. Cada mensaje en una sesión nueva. Fecha: 2026-11-10.

| Mensaje | Intención | latency_ms | prompt_tokens | completion_tokens |
|---|---|---:|---:|---:|
| Hola, buenos días | `greeting` | 2267 | 382 | 103 |
| ¿Y eso lo puedo hacer desde la app? | `product_question` | 4890 | 388 | 476 |
| ¿En qué estado está mi solicitud? | `data_query` | 5643 | 386 | 616 |
| Quiero actualizar mi número de celular | `sensitive_action` | 5668 | 385 | 691 |
| ¿A cuánto está el dólar hoy? | `out_of_scope` | 5379 | 386 | 398 |

Memoria por sesión (paso 8.1):

| Turno | Mensaje | Intención | latency_ms | prompt_tokens | completion_tokens |
|---|---|---|---:|---:|---:|
| 1 | Hola, me llamo Ana | `greeting` | 4385 | 384 | 123 |
| 2 | ¿Cómo me llamo? | `out_of_scope` | 3690 | 440 | 420 |
| 1 (sesión nueva) | ¿Cómo me llamo? | `out_of_scope` | 6071 | 383 | 730 |

Fallas tipadas (paso 8.3): `FOUNDRY_TIMEOUT_S=0.01` → `504 (timeout)`; sin sesión de Azure → `502 (upstream)`.

### Observaciones

- El system prompt de `support` cuesta unos 380 tokens de entrada en cada llamada: es el piso de `prompt_tokens`.
- `prompt_tokens` crece con el historial: el segundo turno de la misma sesión pasó de 384 a 440.
- `completion_tokens` (103 a 730) es mucho mayor que el texto visible de varias respuestas, lo que sugiere que incluye tokens de razonamiento de `gpt-5-mini`. La salida domina el costo y la latencia.
- La latencia va de 2.3 s a 6.1 s y sube con `completion_tokens`.

## Evaluación de trade-offs y decisiones

### Método

- Agente real (`create_app`) contra Foundry, sin el mock. Mismo system prompt de `support`.
- Precios de lista de Azure (Global, USD por 1M tokens, [Azure Retail Prices API](https://prices.azure.com/api/retail/prices), noviembre 2026): `gpt-5-mini` 0.25 entrada / 2.00 salida; `gpt-5-nano` 0.05 entrada / 0.40 salida.
- Costo de un turno = `(prompt_tokens × precio_entrada + completion_tokens × precio_salida) / 1 000 000`.
- Muestra chica: 11 mensajes × 2 repeticiones por modelo (22 llamadas cada uno) y una conversación de 7 turnos por valor de `MAX_TURNS`. Sirve para decidir el tema 1; el golden set de la sesión 5 lo vuelve a medir con más casos.

### Trade-off 1: `gpt-5-mini` frente a `gpt-5-nano`

Set de 11 mensajes alineado a las definiciones de intención de `prompts/support.md`: 2 por intención, más "¿Y eso lo puedo hacer desde la app?" como caso ambiguo.

| Métrica | `gpt-5-mini` | `gpt-5-nano` |
|---|---:|---:|
| Intención correcta | **22/22 (100 %)** | 21/22 (95.5 %) |
| Intención estable entre repeticiones | sí | no ("¿A cuánto está el dólar hoy?" salió `out_of_scope` y luego `product_question`) |
| Latencia mediana | **4.6 s** | 5.2 s |
| Latencia p90 | 6.9 s | 6.4 s |
| `completion_tokens` promedio | 452 | 700 |
| Largo promedio de la respuesta visible | 356 caracteres | 239 caracteres |
| Costo promedio por turno | USD 0.00100 | **USD 0.00030** |

Lo que muestran los datos:

- `gpt-5-nano` es unas 3.3 veces más barato por turno, pero **no es más rápido**. Genera más tokens de salida (700 frente a 452) aunque su respuesta visible es más corta, así que gasta más en razonamiento interno. La latencia mediana sube de 4.6 s a 5.2 s.
- La salida es cerca del 90 % del costo en ambos modelos. La entrada (unos 387 tokens, casi todo system prompt) pesa poco.
- `gpt-5-nano` falló una vez en un caso que `gpt-5-mini` resolvió siempre: clasificó una pregunta fuera de alcance como `product_question`.

**Decisión: mantener `gpt-5-mini` como único modelo del agente en el tema 1.**

Fundamento:

1. **La intención es una decisión de enrutamiento, no un dato decorativo.** Desde el tema 2, `product_question` dispara RAG (búsqueda e índice, más llamadas y más tokens). En el tema 3, `data_query` llama tools y `sensitive_action` exige aprobación humana. Un error de clasificación cuesta más abajo en el flujo (una búsqueda inútil, o una acción sensible que no pide confirmación) que lo que se ahorra por turno.
2. **El ahorro absoluto es chico.** Con un supuesto de 10 000 conversaciones al mes y 5 turnos promedio (50 000 turnos), `gpt-5-mini` cuesta unos USD 50 al mes y `gpt-5-nano` unos USD 15. La diferencia, USD 35 al mes, no compensa perder estabilidad en la intención.
3. **`gpt-5-nano` no mejora la experiencia.** No baja la latencia, que era el otro argumento para cambiar de modelo.

Cuándo revisarla: si el golden set de la sesión 5 muestra que `gpt-5-nano` iguala la precisión de intención, o si el tráfico real multiplica el costo. Una alternativa a evaluar es bajar el esfuerzo de razonamiento de `gpt-5-mini`, ya que la latencia viene de los tokens de razonamiento y no del texto visible.

### Trade-off 2: `MAX_TURNS=10` frente a `MAX_TURNS=4`

Conversación de 7 turnos con `gpt-5-mini`: el cliente da su nombre y su objetivo en el turno 1, hace 5 preguntas de seguimiento y en el turno 7 pregunta "¿cómo me llamo y qué trámite quería hacer?".

| Turno | `prompt_tokens` con 10 | `prompt_tokens` con 4 |
|---:|---:|---:|
| 1 | 392 | 392 |
| 2 | 544 | 522 |
| 3 | 700 | 689 |
| 4 | 862 | 865 |
| 5 | 965 | 983 |
| 6 | 1063 | 937 |
| 7 | 1154 | 895 |

| Métrica | `MAX_TURNS=10` | `MAX_TURNS=4` |
|---|---:|---:|
| `prompt_tokens` totales | 5680 | 5283 (−7 %) |
| `completion_tokens` totales | 3708 | 4461 |
| Costo de la conversación | USD 0.0088 | USD 0.0102 |
| Recuerda nombre y trámite en el turno 7 | **sí**: "Te llamas Ana y querías abrir una cuenta de ahorros" | **no**: se niega a dar datos y deriva a la app |

Lo que muestran los datos:

- El recorte solo actúa desde el turno 6. Antes, ambos envían el mismo historial.
- Recortar a 4 turnos ahorró 397 tokens de entrada, unos USD 0.0001 por conversación (el 1 % del costo). La variación de los tokens de salida entre corridas fue mucho mayor que ese ahorro.
- Con 4 turnos el agente perdió el contexto que el cliente dio al inicio y respondió peor: una negativa larga en vez del dato.

**Decisión: mantener `MAX_TURNS=10`.**

Fundamento:

1. **El historial pesa poco en el costo.** En esta conversación la entrada fue cerca del 16 % del costo y la salida, el 84 %. Recortar historial ataca la parte barata.
2. **Perder contexto se nota en la calidad.** En atención al cliente el dato importante (quién es, qué trámite quiere) suele aparecer al inicio. Con 4 turnos se pierde justo cuando la conversación se alarga.
3. **10 turnos ya es un límite.** Acota el peor caso de una conversación muy larga, que es para lo que existe `MAX_TURNS`.

Cuándo revisarla: en el tema 2, cuando cada turno sume los chunks del RAG a la entrada. Ahí la entrada pesará más en el costo y conviene volver a medir.

## Sesión 3 · Ingesta

Corpus `support` (12 documentos), embeddings con `text-embedding-3-small` (1536 dimensiones) en Foundry, base vectorial Qdrant local en `data/index/support`. Fecha: 2026-11-13.

### Tamaño de chunk

| `INGEST_CHUNK_MAX_CHARS` | Chunks | Qué cambia |
|---:|---:|---|
| 1500 (valor del equipo) | 28 | Un chunk por sección. Largo entre 78 y 387 caracteres. |
| 250 | 30 | Solo se parte `holiday-hours.csv`: 1 chunk pasa a 3, y cada uno repite el encabezado de la tabla. El resto ya cabía. |

- **Qué se gana con 250:** cada pedazo de la tabla de feriados habla de menos fechas, así una pregunta por un feriado recupera un chunk más preciso.
- **Qué se pierde:** contexto. Una regla y su excepción pueden quedar en chunks distintos. En `support` casi no pasa, porque las secciones ya son cortas: la mayoría mide menos de 250 caracteres.
- **Decisión: mantener 1500.** En este corpus el tamaño de chunk casi no cambia el resultado (28 frente a 30 chunks). Lo que define la calidad es cómo se separan las preguntas, no el tamaño. En la sesión 4 se mide con preguntas reales.

### Hallazgos del corpus para el Gate T2

1. **FAQs anidadas por error.** `app-faq.md` y `branches-faq.md` saltan del título `#` a preguntas con `###`, sin un `##` entre medio. Como el chunker arma el camino de títulos por nivel, cada pregunta queda anidada bajo la anterior. Por ejemplo: `Preguntas frecuentes de la aplicación > ¿Puedo transferir desde la app? > ¿Se pueden hacer transferencias con la aplicación?`. El contenido de cada chunk es correcto, pero el camino de títulos mezcla dos preguntas distintas. Propuesta para el gate: un chunk por pregunta, con el camino `título > pregunta` sin importar el salto de nivel.
2. **Preguntas casi duplicadas.** `app-faq.md` repite la misma pregunta con otras palabras ("¿Puedo transferir desde la app?" y "¿Se pueden hacer transferencias con la aplicación?"), y `branches-faq.md` hace lo mismo con el horario. La búsqueda de la sesión 4 puede devolver los dos chunks y gastar contexto en información repetida.
3. **Versiones vencidas.** `general-faq-2023.md` vence el 2024-12-31 y repite "¿A qué hora abren las agencias?". La búsqueda tiene que filtrar por `valid_until`, o el agente puede responder con el horario viejo. `holiday-hours.csv` vence el 2025-12-31.
4. **Ruido y datos sensibles.** `internal-notice-gym.md` es ruido y no debería recuperarse nunca. `service-cases.pdf` trae datos ficticios de clientes, que se usan en la sesión 5.
