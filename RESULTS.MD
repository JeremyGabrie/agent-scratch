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
