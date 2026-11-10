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

## Trade-offs de modelo y costo (borrador para discutir con el equipo)

1. **`gpt-5-mini` frente a `gpt-5-nano` para clasificar la intención.** Las cinco intenciones salieron correctas con `gpt-5-mini`, pero cada turno tarda entre 2.3 s y 5.7 s y genera hasta 691 tokens de salida. Un modelo más chico (`gpt-5-nano`, disponible en el mismo recurso) debería bajar latencia y costo de salida; el riesgo es clasificar peor los casos ambiguos, como "¿Cómo me llamo?" o "¿Y eso lo puedo hacer desde la app?". Propuesta: medir `gpt-5-nano` con las mismas conversaciones y aceptarlo solo si la intención coincide en todas.

2. **`MAX_TURNS=10` frente a `MAX_TURNS=4`.** Cada turno reenvía el historial completo, así que `prompt_tokens ≈ 380 + Σ (mensaje + respuesta)` de los turnos guardados. Con respuestas de varios cientos de tokens, 10 turnos pueden multiplicar varias veces la entrada de una conversación larga, mientras que 4 turnos la acotan. El costo mensual escala con `conversaciones × turnos promedio × prompt_tokens`. Propuesta: usar `MAX_TURNS=4` para atención y FAQ, donde las consultas suelen ser cortas, y validar que no se pierda contexto necesario.
