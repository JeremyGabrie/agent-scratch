| Mensaje | Intención | latency_ms | prompt_tokens | completion_tokens |
|---|---|---:|---:|---:|
| Hola, ¿cómo estás? | greeting | 2959 | 381 | 110 |
| ¿Y eso lo puedo hacer desde la app? | product_question | 5498 | 429 | 540 |
| ¿En qué estado está mi solicitud? | data_query | 3530 | 521 | 464 |
| Quiero actualizar mi número de celular | sensitive_action | 7449 | 600 | 760 |
| ¿A cuánto está el dólar hoy? | out_of_scope | 5025 | 776 | 271 |

## Comparación: gpt-5-mini vs. gpt-5-nano

En las ejecuciones registradas, `gpt-5-nano` tardó **7599 ms**, mientras que `gpt-5-mini` tardó **3530 ms**: en esta muestra, nano tomó **4069 ms más** (aproximadamente **2,15 veces** el tiempo de mini). Nano también generó más tokens de respuesta (**712 vs. 464**), lo que puede influir en la latencia.

**Conclusión:** con esta muestra no hay evidencia de una ventaja de latencia de nano; mini fue más rápido en la ejecución observada. Para elegir el modelo de clasificación, conviene probar ambos con las mismas consultas y medir latencia y exactitud sobre un conjunto etiquetado. La calidad no se puede determinar solo con estos logs.

## Efecto de `MAX_TURNS` en costo e historial

En la conversación de prueba con `MAX_TURNS=4`, el usuario indicó su nombre al inicio (“hola soy jeremy”), pero en la quinta respuesta el agente contestó que no podía ver su nombre. Esto es consistente con que el historial anterior haya quedado fuera del contexto disponible; bajar el límite puede afectar la continuidad y hacer que el agente pierda datos que el usuario ya proporcionó.

**Conclusión:** `MAX_TURNS=4` mostró un posible costo menor por menor contexto, pero también una pérdida concreta de continuidad en la quinta respuesta. Con los datos actuales no se puede afirmar cuánto se ahorra al mes ni si el ahorro compensa ese efecto.

## Enrutamiento por intención: `gpt-5-nano` y `gpt-5-mini`

**Recomendación:** comparar ambas configuraciones con las mismas conversaciones etiquetadas. Medir exactitud por intención, errores especialmente en `sensitive_action`, latencia total y tokens/costo por conversación. Mantener el enrutamiento híbrido solo si nano cumple el umbral de calidad y produce un ahorro medible; si no, usar mini para clasificar o responder esas intenciones.

## Comparación del tamaño de chunks

| Tamaño máximo | Chunks generados |
|---:|---:|
| 250 caracteres | 30 |
| 1500 caracteres | 28 |

Con el límite de **250 caracteres** se obtuvieron 30 chunks; con **1500 caracteres**, 28. En este corpus la diferencia fue de 2 chunks, porque el chunker también organiza el contenido por secciones y no depende únicamente del límite de caracteres.

**Qué se gana con chunks más pequeños:** cada fragmento tiende a tratar un tema más específico, lo que puede mejorar la precisión al recuperar información relevante para una pregunta concreta.

**Qué se pierde:** al dividir más el contenido, una regla y su excepción pueden quedar en fragmentos distintos. Si se recupera solo uno, puede faltar contexto y la respuesta quedar incompleta.

**Conclusión:** un tamaño menor favorece la precisión temática y uno mayor conserva más contexto en cada fragmento. Además de contar chunks, conviene evaluar las respuestas recuperadas, sobre todo cuando dependen de reglas, excepciones o condiciones.

## Preguntas de evaluación para `support`

| Tipo | Pregunta | Qué debe pasar |
|---|---|---|
| Regla del corpus | ¿Cuánto tardan en emitirse las constancias y cartas? | Responde que tardan 2 días hábiles y cita `request-status.html`. |
| Seguimiento | **Turno 1:** ¿Puedo abrir una cuenta desde la app? **Turno 2:** ¿Qué necesito para hacerlo? | Entiende que el seguimiento se refiere a abrir la cuenta desde la app; indica los requisitos (ser mayor de 18 años, DNI vigente, celular y correo propios) y la validación biométrica. Cita `account-opening.md` y/o `app-faq.md`. |
| Término exacto | ¿Qué significa validación biométrica? | Explica que es una verificación de identidad con el rostro o la huella y cita `service-glossary.md`. |
| Documento vencido | ¿Cuál es el horario actual de atención en agencias? | Responde de lunes a viernes de 9:00 a 18:00 y sábados de 9:00 a 13:00; cita `branches-faq.md`. No presenta como vigente el horario de `general-faq-2023.md`, vencido el 31-12-2024. |
| Fuera del corpus | ¿A cuánto está el dólar hoy? | Clasifica como `out_of_scope` y responde que no puede determinarlo con la información disponible, sin citar fuentes del corpus. |

## Resultados de evaluación de `support`

**Configuración:** recuperación con `top_k=5`.

| Pregunta | Intención | Latencia primer texto (ms) | Latencia completa (ms) | Tokens entrada | Tokens salida | Resultado |
|---|---|---:|---:|---:|---:|---|
| ¿Cuánto tardan en emitirse las constancias y cartas? | `product_question` | 9306 | 9342 | 718 | 233 | Correcto: 2 días hábiles. Cita `request-status.html`. |
| ¿Puedo abrir una cuenta desde la app? | `product_question` | 11324 | 11447 | 966 | 944 | Correcto: apertura en unos 10 minutos con DNI y validación biométrica; tarjeta digital al instante. Cita `app-faq.md` y `account-opening.md`. |
| ¿Qué significa validación biométrica? | `product_question` | 10280 | 10298 | 1044 | 815 | Correcto: verificación de identidad mediante el rostro o la huella. Cita `service-glossary.md`. |
| ¿Cuál es el horario actual de atención en agencias? | `product_question` | 10628 | 10759 | 1160 | 925 | Correcto: lunes a viernes de 9:00 a 18:00, sábados de 9:00 a 13:00; domingos y feriados no atienden. Cita `branches-faq.md`. |
| ¿A cuánto está el dólar hoy? | `out_of_scope` | 11573 | 11713 | 1269 | 1012 | Clasificación correcta; responde que no ofrece cotizaciones en tiempo real y orienta a canales del banco. Sin fuentes citadas. |

Las cinco consultas obtuvieron la intención esperada y, cuando correspondía, una fuente pertinente del corpus. La consulta fuera de alcance no citó fuentes. En esta muestra, el primer texto tardó entre **9306 y 11573 ms** y la respuesta completa entre **9342 y 11713 ms**; estas mediciones son observaciones de una ejecución, no una comparación estadística.

## Comparación de `top_k`: 2, 5 y 10

Se compararon las dos preguntas con resultados disponibles para los tres valores. Los tokens de entrada dependen de la ejecución, así que las diferencias son las observadas en estas muestras.

| Pregunta | Tokens de entrada (`top_k=2`) | `top_k=5` | `top_k=10` | Diferencia 10 vs. 2 | Diferencia 10 vs. 5 |
|---|---:|---:|---:|---:|---:|
| ¿Cuánto tardan en emitirse las constancias y cartas? | 593 | 718 | 966 | +373 | +248 |
| ¿Puedo abrir una cuenta desde la app? | 826 | 966 | 1189 | +363 | +223 |

Con `top_k=2`, la respuesta sobre el plazo fue correcta, pero también apareció `requirements-by-procedure.pdf`, que trata los requisitos de una constancia y no aporta al plazo de emisión. En la pregunta sobre abrir una cuenta, `top_k=2` devolvió solo `app-faq.md`; `top_k=5` y `top_k=10` devolvieron también `account-opening.md`, con información complementaria. En estos resultados de `top_k=10` no se observan fuentes ajenas al tema: las fuentes citadas respaldan las respuestas.

**Elección del equipo: `top_k=5`.** En las muestras disponibles, recupera fuentes pertinentes y suficientes para ambas respuestas. Frente a `top_k=2`, aporta la fuente complementaria sobre apertura de cuenta; frente a `top_k=10`, conserva las fuentes relevantes observadas con 248 y 223 tokens de entrada menos por turno, respectivamente. Es un balance razonable entre contexto recuperado y costo; conviene reevaluarlo si cambian el corpus o las preguntas.

## Comparación: búsqueda local (`top_k=5`) vs. Azure AI Search

| Pregunta | Fuentes en local (`top_k=5`) | Fuentes en AI Search | ¿Mejoró frente al resultado local? | Respuesta completa (local / AI Search) |
|---|---|---|---|---:|
| ¿Cuánto tardan en emitirse las constancias y cartas? | `request-status.html` | `request-status.html` | **Sí, en latencia:** 475 ms más rápida (9342 → 8867 ms). Misma fuente y respuesta correcta. | 9342 / 8867 ms |
| ¿Puedo abrir una cuenta desde la app? | `app-faq.md`, `account-opening.md` | `app-faq.md`, `account-opening.md` | **Sí, en latencia:** 2443 ms más rápida (11447 → 9004 ms). Conserva ambas fuentes pertinentes y la respuesta incluye la disponibilidad inmediata de la tarjeta digital. | 11447 / 9004 ms |
| ¿Qué significa validación biométrica? | `service-glossary.md` | `service-glossary.md` | **Sí, levemente en latencia:** 436 ms más rápida (10298 → 9862 ms). Misma fuente y definición correcta, expresada más concisamente. | 10298 / 9862 ms |
| ¿Cuál es el horario actual de atención en agencias? | `branches-faq.md` | `channels-and-hours.html` | **Mixto:** AI Search recuperó una fuente directamente pertinente sobre canales y horarios, pero la respuesta omitió que domingos y feriados no atienden; además tardó 68 ms más (10759 → 10827 ms). | 10759 / 10827 ms |
| ¿A cuánto está el dólar hoy? | Sin fuentes | Sin fuentes | **No aplica al reranker:** se clasificó como `out_of_scope` en ambos casos. Azure respondió 4611 ms más rápido (11713 → 7102 ms). | 11713 / 7102 ms |

**Balance:** frente a la ejecución local con `top_k=5`, Azure AI Search fue más rápido en tres de las cuatro preguntas dentro del corpus y mantuvo respuestas y fuentes pertinentes en esas consultas; en la de horarios cambió a una fuente relevante, pero la respuesta perdió el detalle de domingos y feriados. La pregunta fuera del corpus también fue más rápida, aunque no permite evaluar el reranker. Estos son resultados observados de ejecuciones individuales: muestran mejoras en algunos turnos, pero no aíslan cuánto de la diferencia se debe al reranker frente a Azure AI Search u otras variaciones entre ejecuciones.

## Comparación de cambios de retrieval (referencia AIE_16FL)

La siguiente comparación corresponde a las corridas de 31 casos de AIE_16FL compartidas aparte. Se
mantiene separada de las métricas AIE_20JG de 30 casos y de su evaluación individual.

| Cambio | Configuración / ejecución | Recall@5 | Intención | Fuentes | Hechos | Apoyo / 5 | Tokens de entrada | Citas prohibidas | Tiempo |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Línea base | Azure AI Search; chunks 1500; `SEARCH_TOP_K=5` | 1.00 | 0.84 | 0.90 | 0.82 | 5.0 | 23,301 | 1 | 334 s |
| Chunks más chicos | `$env:INGEST_CHUNK_MAX_CHARS = "800"`; `uv run ingest build`; `uv run ingest publish` | 1.00 | 0.84 | 0.90 | 0.75 | 5.0 | 23,356 | 1 | 356 s |
| Menos fragmentos | `$env:SEARCH_TOP_K = "3"`; volver a ejecutar la evaluación | 1.00 | 0.81 | 0.94 | 0.79 | 5.0 | 20,700 | 1 | 327 s |
| Más fragmentos | `$env:SEARCH_TOP_K = "8"`; volver a ejecutar la evaluación | 1.00 | 0.84 | 0.94 | 0.75 | 5.0 | 27,626 | 1 | 366 s |
| Base local, sin reranker | `uv run ingest publish --target local`; `$env:KNOWLEDGE_BASE = "local"` | 1.00 | 0.87 | 0.94 | 0.82 | 5.0 | 23,600 | 1 | 355 s |

**Qué muestran y qué mirar al probar cada cambio:**

- **Chunks de 800:** el corpus produjo los mismos 28 chunks que con 1500, así que el índice
  prácticamente no cambió. Recall, intención y fuentes quedaron iguales; la caída de hechos
  (0.82 → 0.75) no demuestra una regresión causada por chunking en una sola corrida.
- **`SEARCH_TOP_K=3`:** mantuvo recall@5 en 1.00 y usó 2,601 tokens de entrada menos que la línea
  base (aprox. 11 %). Hechos y apoyo se mantuvieron cerca, aunque la intención bajó de 0.84 a 0.81.
  Es una alternativa para repetir y comparar tokens, hechos y recall.
- **`SEARCH_TOP_K=8`:** añadió 4,325 tokens de entrada (aprox. 19 %) sin mejorar hechos ni apoyo;
  fuentes subió de 0.90 a 0.94, pero la cita prohibida continuó. Hay más contexto, no una mejora
  consistente en la respuesta.
- **Base local sin reranker:** recall y hechos igualaron la línea base; fuentes e intención fueron
  algo mayores en esta corrida. Como solo hay una corrida por configuración y también cambia el
  modo de búsqueda, no se puede atribuir esa diferencia únicamente a quitar el reranker ni concluir
  que no aporta en general.
- **Citas prohibidas:** se mantuvieron en 1 en las cinco configuraciones. Cambiar chunking o
  `SEARCH_TOP_K` no resolvió ese problema; el aviso interno debe filtrarse en la ingesta y/o
  bloquearse explícitamente en las reglas de fuentes.

La decisión reportada fue conservar la línea base (`azure_search`, chunks 1500,
`SEARCH_TOP_K=5`): `top_k=3` ahorra tokens, pero con 31 casos la diferencia de calidad observada no
es suficiente para cambiar el valor sin repetir la evaluación. Al repetir, comparar una variable a
la vez y registrar recall, hechos, tokens de entrada, citas prohibidas y tiempo.

# Resultados · Calidad del RAG (AIE_20JG)

## Resumen de la corrida

Evaluación de 30 casos del dominio `support` con el juez G-Eval. Las métricas se transcriben del
resumen de la corrida proporcionado; no se mezclan con resultados de otras sesiones.

| Métrica | Resultado |
|---|---:|
| Casos | 30 |
| Recall@k | 1.00 |
| Exactitud de intención | 0.87 |
| Fuentes correctas | 0.93 |
| Hechos correctos | 0.78 |
| Fundamentación | 4.93/5 |
| Relevancia | 4.89/5 |
| Cita correcta | 0.97 |
| Fugas de datos personales | 0 |
| Citas de fuentes prohibidas | 1 |
| Tokens de entrada | 22,584 |
| Tokens de salida | 14,294 |

## Casos a revisar

| Caso | Resultado | Observación |
|---|---|---|
| `support-07` | Hechos: NO | La regla de hechos marcó la respuesta como incorrecta, aunque G-Eval consideró que enumeraba correctamente celular, correo electrónico y dirección. |
| `support-08` | Intención y hechos: NO | Pregunta informativa sobre el cambio de celular clasificada como `sensitive_action`. |
| `support-09` | Intención y hechos: NO | Pregunta informativa sobre el cambio de correo clasificada como `sensitive_action`. |
| `support-20` | Hechos: NO; fundamentación 3, relevancia 2, cita 0.5 | No entregó el número solicitado e inventó una restricción de seguridad que no aparece en las fuentes. |
| `support-24` | Fuentes y hechos: NO | Respondió sobre el horario telefónico en vez del horario de feriados preguntado. `branches-faq.md` sí fue recuperado, pero no se citó; la fuente citada no respalda la respuesta completa. |
| `support-25` | Intención y fuentes: NO; cita prohibida | Respondió sobre un beneficio interno para colaboradores y citó `internal-notice-gym.md`. |
| `support-30` | Intención y hechos: NO | Clasificó la consulta sobre el caso de un cliente como `data_query`; G-Eval, sin embargo, calificó la respuesta como respaldada y pertinente. |

## Diagnóstico según los criterios de revisión

1. **`recall` en NO:** no hay casos aplicables con `recall: false`. El resumen da recall@k de 1.00.
   `support-25`, `support-27` y `support-28` tienen `recall: null` por ser ruido o fuera de alcance;
   no son fallos de búsqueda. No se justifica cambiar chunking ni `SEARCH_TOP_K` por esta corrida.
2. **Recall OK y hechos en NO:** ocurre en `support-07`, `support-08`, `support-09`, `support-20`,
   `support-24` y `support-30`. La fuente esperada sí se recuperó, así que el problema apunta al uso
   de la evidencia y, en `support-08`, `-09` y `-30`, también a la intención. Revisar prompt/contexto
   antes que chunking o `SEARCH_TOP_K`. En `support-07` y `support-30`, G-Eval contradice el control
   automático; conviene validar también la regla de evaluación.
3. **Fuentes NO en `expired` o `noise`:** sucede en `support-24` (`expired`) y `support-25`
   (`noise`), pero por motivos distintos. En `support-25` sí se citó la fuente interna prohibida
   `internal-notice-gym.md`; debe excluirse de la ingesta (y comprobarse el filtro de fuentes).
   En `support-24`, `forbidden_cited` es `false`: no citó una fuente marcada como prohibida, pero citó
   `channels-and-hours.html` en lugar de `branches-faq.md`, que sí estaba entre los fragmentos
   recuperados. Es un fallo de selección de evidencia/cita, no evidencia de que se haya citado el
   documento vencido.
4. **FUGA:** el resumen registra 0 y los 30 casos tienen `personal_data_leak: false`. No se detectaron
   fugas en esta corrida; no hay una redacción concreta que corregir por este criterio.

Como resultado fuera del dominio, `support-27` respondió correctamente sin citar fuentes. La
prioridad de corrección es retirar el aviso interno del índice y mejorar el prompt/contexto para
intención y selección de evidencia; los resultados no señalan un problema de recall.

## Alcance

Este informe refleja exclusivamente el JSON de 30 casos de AIE_20JG. La configuración de ejecución,
el tiempo total y los resultados de otras corridas no estaban incluidos en los datos proporcionados.

## Resultado del caso individual · `support-AIE20JG`

Esta evaluación de un solo caso se registra por separado y no se suma a las métricas de la corrida
anterior de 30 casos.

| Métrica | Resultado |
|---|---:|
| Casos | 1 |
| Recall@k | 1.00 |
| Exactitud de intención | 1.00 |
| Fuentes correctas | 1.00 |
| Hechos correctos | 1.00 |
| Fundamentación | 5.0/5 |
| Relevancia | 5.0/5 |
| Cita correcta | 1.00 |
| Fugas de datos personales | 0 |
| Citas de fuentes prohibidas | 0 |
| Tokens de entrada | 722 |
| Tokens de salida | 173 |

| Pregunta | Respuesta | Fuente citada | Resultado |
|---|---|---|---|
| Si abro una cuenta de ahorros en una agencia, ¿cuándo me entregan la tarjeta física? | La tarjeta física se entrega en el momento. | `account-opening.md` | Correcto en intención, fuentes y hechos; G-Eval: fundamentación 5, relevancia 5 y cita 1. |

El caso verifica que el agente distinga la apertura en agencia de la apertura por la app y responda
con el plazo correcto para la tarjeta física.
