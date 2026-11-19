# Resultados · AIE_20JG (dominio `support`)

## Sesión 2 · Servicio IA

### Mediciones por mensaje

| Mensaje | Intención | latency_ms | prompt_tokens | completion_tokens |
|---|---|---:|---:|---:|
| Hola, ¿cómo estás? | `greeting` | 2959 | 381 | 110 |
| ¿Y eso lo puedo hacer desde la app? | `product_question` | 5498 | 429 | 540 |
| ¿En qué estado está mi solicitud? | `data_query` | 3530 | 521 | 464 |
| Quiero actualizar mi número de celular | `sensitive_action` | 7449 | 600 | 760 |
| ¿A cuánto está el dólar hoy? | `out_of_scope` | 5025 | 776 | 271 |

### Evaluación de trade-offs y decisiones

#### Trade-off 1: `gpt-5-mini` frente a `gpt-5-nano`

En la comparación registrada, `gpt-5-nano` tardó **7599 ms** y `gpt-5-mini`, **3530 ms**. Nano demoró **4069 ms más**, es decir, alrededor de **2,15 veces** el tiempo de mini. También generó más tokens de respuesta (**712 frente a 464**).

En esta muestra, mini fue más rápido. Los datos no permiten afirmar que nano clasifique mejor o peor, porque para eso habría que revisar la exactitud de ambos modelos sobre las mismas consultas etiquetadas.

**Decisión:** no se justifica elegir nano por una supuesta ventaja de velocidad. La comparación favorece a mini en latencia; la calidad de clasificación debe valorarse con un conjunto común de preguntas y no solo con estos registros.

#### Trade-off 2: `MAX_TURNS=4` frente al historial completo

En la prueba con `MAX_TURNS=4`, el usuario dijo su nombre al inicio (“hola soy jeremy”), pero en la quinta respuesta el agente indicó que no podía verlo. El resultado muestra que, al limitar el historial, un dato compartido al comienzo puede quedar fuera del contexto que recibe el modelo.

El límite más bajo reduce la cantidad de historial disponible, pero en esta conversación afectó la continuidad. No se registraron mediciones suficientes para calcular un ahorro mensual ni para determinar si compensaría esa pérdida de contexto.

**Conclusión:** en esta prueba, `MAX_TURNS=4` no conservó información relevante de los primeros turnos. La reducción del historial puede contener el tamaño del contexto, pero también puede hacer que el agente pierda datos que el usuario ya había proporcionado.

#### Enrutamiento por intención: `gpt-5-nano` y `gpt-5-mini`

Para el enrutamiento por intención, lo importante es que una clasificación equivocada no active una búsqueda innecesaria ni permita tratar una acción sensible como una consulta normal. Con los datos actuales, no hay una ventaja clara que justifique incorporar nano al flujo. La comparación entre modelos debe considerar la exactitud por intención —en especial `sensitive_action`— junto con la latencia y los tokens por conversación. Hasta contar con esa comparación, los resultados observados respaldan mantener mini.

## Sesión 3 · Ingesta

### Tamaño de chunk

| Tamaño máximo | Chunks generados | Qué cambia |
|---:|---:|---|
| 250 caracteres | 30 | Genera dos chunks más que la configuración de 1500 caracteres. |
| 1500 caracteres | 28 | Mantiene los fragmentos organizados por secciones del corpus. |

Con un máximo de **250 caracteres** se generaron 30 chunks y con **1500 caracteres**, 28. La diferencia fue de solo dos fragmentos porque el chunker también respeta la separación por secciones del corpus; el límite de caracteres no es el único factor.

Los chunks pequeños dejan cada fragmento más enfocado y pueden ayudar a recuperar un tema concreto. A cambio, una regla y su excepción podrían quedar separadas. Los chunks más grandes conservan mejor el contexto, aunque pueden incluir información adicional que no siempre se necesita para responder.

En este corpus, la diferencia en cantidad de chunks fue reducida. Por eso, además de contar fragmentos, la comparación debe considerar si la respuesta recupera todos los datos necesarios, especialmente cuando una condición depende de una excepción.

## Sesión 4 · Retrieval

Agente con recuperación RAG y `top_k=5`. Se evaluaron preguntas de reglas del corpus, seguimiento conversacional, términos exactos, vigencia documental y consultas fuera del corpus. También se comparó la búsqueda local con Azure AI Search.

### Las cinco preguntas de evaluación (`top_k=5`)

| Tipo | Pregunta | Resultado esperado |
|---|---|---|
| Regla del corpus | ¿Cuánto tardan en emitirse las constancias y cartas? | Responde que tardan 2 días hábiles y cita `request-status.html`. |
| Seguimiento | **Turno 1:** ¿Puedo abrir una cuenta desde la app? **Turno 2:** ¿Qué necesito para hacerlo? | Entiende que el seguimiento se refiere a abrir la cuenta desde la app; indica los requisitos (ser mayor de 18 años, DNI vigente, celular y correo propios) y la validación biométrica. Cita `account-opening.md` y/o `app-faq.md`. |
| Término exacto | ¿Qué significa validación biométrica? | Explica que es una verificación de identidad con el rostro o la huella y cita `service-glossary.md`. |
| Documento vencido | ¿Cuál es el horario actual de atención en agencias? | Responde de lunes a viernes de 9:00 a 18:00 y sábados de 9:00 a 13:00; cita `branches-faq.md`. No presenta como vigente el horario de `general-faq-2023.md`, vencido el 31-12-2024. |
| Fuera del corpus | ¿A cuánto está el dólar hoy? | Clasifica como `out_of_scope` y responde que no puede determinarlo con la información disponible, sin citar fuentes del corpus. |

### Resultados de evaluación

**Configuración:** recuperación con `top_k=5`.

| Pregunta | Intención | Primer texto (ms) | Respuesta completa (ms) | Tokens de entrada | Tokens de salida | Resultado |
|---|---|---:|---:|---:|---:|---|
| ¿Cuánto tardan en emitirse las constancias y cartas? | `product_question` | 9306 | 9342 | 718 | 233 | Correcto: 2 días hábiles. Cita `request-status.html`. |
| ¿Puedo abrir una cuenta desde la app? | `product_question` | 11324 | 11447 | 966 | 944 | Correcto: apertura en unos 10 minutos con DNI y validación biométrica; tarjeta digital al instante. Cita `app-faq.md` y `account-opening.md`. |
| ¿Qué significa validación biométrica? | `product_question` | 10280 | 10298 | 1044 | 815 | Correcto: verificación de identidad mediante el rostro o la huella. Cita `service-glossary.md`. |
| ¿Cuál es el horario actual de atención en agencias? | `product_question` | 10628 | 10759 | 1160 | 925 | Correcto: lunes a viernes de 9:00 a 18:00, sábados de 9:00 a 13:00; domingos y feriados no atienden. Cita `branches-faq.md`. |
| ¿A cuánto está el dólar hoy? | `out_of_scope` | 11573 | 11713 | 1269 | 1012 | Clasificación correcta; responde que no ofrece cotizaciones en tiempo real y orienta a canales del banco. Sin fuentes citadas. |

En las cinco consultas se obtuvo la intención esperada. Las preguntas que dependían del corpus se respondieron con la fuente correspondiente y la consulta del dólar quedó fuera del alcance, sin citas. El primer texto apareció entre **9306 y 11573 ms** y las respuestas completas tardaron entre **9342 y 11713 ms**. Son tiempos de las ejecuciones registradas y sirven como referencia de esta prueba, no como una medición estadística.

### Observaciones

Las preguntas que tenían respuesta en el corpus recuperaron documentos pertinentes. La consulta sobre el dólar se clasificó como `out_of_scope` y el agente indicó que no podía ofrecer una cotización en tiempo real, sin citar documentos que no correspondían.

En algunas preguntas hubo poca diferencia entre el primer texto y la respuesta completa. En otras, el tiempo fue mayor; al tratarse de ejecuciones individuales, los valores permiten describir lo ocurrido en la prueba, pero no establecer una tendencia general.

### Comparación de `SEARCH_TOP_K`

Se compararon las dos preguntas con resultados disponibles para los tres valores. Los tokens de entrada dependen de la ejecución, así que las diferencias son las observadas en estas muestras.

| Pregunta | Tokens de entrada (`top_k=2`) | `top_k=5` | `top_k=10` | Diferencia 10 vs. 2 | Diferencia 10 vs. 5 |
|---|---:|---:|---:|---:|---:|
| ¿Cuánto tardan en emitirse las constancias y cartas? | 593 | 718 | 966 | +373 | +248 |
| ¿Puedo abrir una cuenta desde la app? | 826 | 966 | 1189 | +363 | +223 |

- Con `top_k=2`, la respuesta sobre el plazo fue correcta, pero también apareció `requirements-by-procedure.pdf`, que trata los requisitos de una constancia y no aporta al plazo de emisión.
- En la pregunta sobre abrir una cuenta, `top_k=2` devolvió solo `app-faq.md`; `top_k=5` y `top_k=10` devolvieron también `account-opening.md`, con información complementaria.
- En estos resultados de `top_k=10` no se observan fuentes ajenas al tema: las fuentes citadas respaldan las respuestas.

**Elección del equipo: `top_k=5`.** En las muestras disponibles, recupera fuentes pertinentes y suficientes para ambas respuestas. Frente a `top_k=2`, aporta la fuente complementaria sobre apertura de cuenta; frente a `top_k=10`, conserva las fuentes relevantes observadas con 248 y 223 tokens de entrada menos por turno, respectivamente. Es un balance razonable entre contexto recuperado y costo; conviene reevaluarlo si cambian el corpus o las preguntas.

### Búsqueda local frente a Azure AI Search

| Pregunta | Fuentes en local (`top_k=5`) | Fuentes en AI Search | Resultado frente a local | Respuesta completa (local / AI Search) |
|---|---|---|---|---:|
| ¿Cuánto tardan en emitirse las constancias y cartas? | `request-status.html` | `request-status.html` | **Sí, en latencia:** 475 ms más rápida (9342 → 8867 ms). Misma fuente y respuesta correcta. | 9342 / 8867 ms |
| ¿Puedo abrir una cuenta desde la app? | `app-faq.md`, `account-opening.md` | `app-faq.md`, `account-opening.md` | **Sí, en latencia:** 2443 ms más rápida (11447 → 9004 ms). Conserva ambas fuentes pertinentes y la respuesta incluye la disponibilidad inmediata de la tarjeta digital. | 11447 / 9004 ms |
| ¿Qué significa validación biométrica? | `service-glossary.md` | `service-glossary.md` | **Sí, levemente en latencia:** 436 ms más rápida (10298 → 9862 ms). Misma fuente y definición correcta, expresada más concisamente. | 10298 / 9862 ms |
| ¿Cuál es el horario actual de atención en agencias? | `branches-faq.md` | `channels-and-hours.html` | **Mixto:** AI Search recuperó una fuente directamente pertinente sobre canales y horarios, pero la respuesta omitió que domingos y feriados no atienden; además tardó 68 ms más (10759 → 10827 ms). | 10759 / 10827 ms |
| ¿A cuánto está el dólar hoy? | Sin fuentes | Sin fuentes | **No aplica al reranker:** se clasificó como `out_of_scope` en ambos casos. Azure respondió 4611 ms más rápido (11713 → 7102 ms). | 11713 / 7102 ms |

**Balance:** Azure AI Search terminó antes en tres de las cuatro preguntas que sí dependían del corpus. En esas consultas mantuvo fuentes pertinentes; en la de horarios recuperó `channels-and-hours.html`, pero la respuesta dejó fuera el detalle de domingos y feriados. La consulta del dólar también fue más rápida, aunque no sirve para medir el reranker porque se resolvió como `out_of_scope`. Como se comparan ejecuciones individuales, las diferencias de tiempo no se pueden atribuir únicamente al buscador o al reranker.

## Sesión 5 · Calidad del RAG

El golden set de `support` se evaluó con G-Eval sobre 30 casos. Las métricas de esta sección corresponden a esa corrida de AIE_20JG. El caso que agregaste se describe aparte para que su resultado no se mezcle con los indicadores de los 30 casos.

### Línea base (30 casos)

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

### Casos a revisar

| Caso | Resultado | Observación |
|---|---|---|
| `support-07` | Hechos: NO | La regla de hechos marcó la respuesta como incorrecta, aunque G-Eval consideró que enumeraba correctamente celular, correo electrónico y dirección. |
| `support-08` | Intención y hechos: NO | Pregunta informativa sobre el cambio de celular clasificada como `sensitive_action`. |
| `support-09` | Intención y hechos: NO | Pregunta informativa sobre el cambio de correo clasificada como `sensitive_action`. |
| `support-20` | Hechos: NO; fundamentación 3, relevancia 2, cita 0.5 | No entregó el número solicitado e inventó una restricción de seguridad que no aparece en las fuentes. |
| `support-24` | Fuentes y hechos: NO | Respondió sobre el horario telefónico en vez del horario de feriados preguntado. `branches-faq.md` sí fue recuperado, pero no se citó; la fuente citada no respalda la respuesta completa. |
| `support-25` | Intención y fuentes: NO; cita prohibida | Respondió sobre un beneficio interno para colaboradores y citó `internal-notice-gym.md`. |
| `support-30` | Intención y hechos: NO | Clasificó la consulta sobre el caso de un cliente como `data_query`; G-Eval, sin embargo, calificó la respuesta como respaldada y pertinente. |

### Lectura de los resultados

El recall@k de **1.00** indica que las fuentes esperadas estuvieron disponibles en la recuperación. Por eso, los casos marcados con hechos incorrectos no apuntan a una falta general de recuperación, sino a cómo se utilizó la evidencia en la respuesta y, en algunos casos, a la clasificación de intención.

En `support-07` y `support-30`, el control automático no coincidió con la valoración de G-Eval: el juez consideró que las respuestas estaban respaldadas, aunque la regla de hechos las marcó como incorrectas. En esos casos también influye cómo el evaluador reconoce respuestas expresadas con otras palabras.

Los casos `support-24` y `support-25` muestran problemas distintos en fuentes. En `support-24`, la respuesta se apoyó en `channels-and-hours.html` y dejó fuera el horario especial de feriados, aunque `branches-faq.md` estaba entre los fragmentos recuperados. En `support-25`, sí se utilizó `internal-notice-gym.md`, que es una fuente interna y no corresponde a respuestas para clientes.

Por otro lado, `support-27` respondió la consulta fuera del dominio sin citar fuentes. Tampoco se registraron fugas de datos personales: los 30 casos tienen `personal_data_leak: false`. En conjunto, la corrida muestra una recuperación sólida; los errores detectados se concentran en la selección y uso de fuentes, en algunas clasificaciones y en la forma de evaluar paráfrasis.

### Mi caso del golden set

`evals/golden/support.AIE_20JG.jsonl`: `support-AIE20JG`, de tipo `answerable`, con `history: []`. La pregunta es: **“¿Cuánto tiempo debo ser cliente del banco y cuánto cuesta solicitar una carta de presentación bancaria?”** La intención esperada es `product_question`; la fuente que debe respaldar la respuesta es `requirements-by-procedure.pdf`. Los dos datos que debe incluir son **6 meses como cliente** y **S/ 25**. El caso no define fuentes prohibidas (`forbidden_sources: []`).

- **Por qué lo elegí:** reúne dos datos de un mismo procedimiento en una sola pregunta. Sirve para comprobar que el agente encuentre el documento de requisitos y no omita ni la antigüedad mínima ni el costo de la carta.
- **Cómo le fue:** la prueba se ejecutó correctamente. El agente respondió con los dos datos esperados y utilizó `requirements-by-procedure.pdf` como sustento. La consulta también se mantuvo dentro de la intención `product_question`.

Este caso se presenta por separado y no modifica las métricas de los 30 casos de la corrida principal.
