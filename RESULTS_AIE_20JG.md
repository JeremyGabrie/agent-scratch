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

## Sesión 6 · Tools del MCP en el chat

Las pruebas del dominio `support` se realizaron con el mock local (`http://127.0.0.1:8200/mcp`) y con el MCP compartido `bank-mcp`, desplegado en Azure.

### Tools disponibles en `support`

| MCP | Tools | Parámetros |
|---|---|---|
| Mock local | `find_branches` (consulta), `get_request_status` (consulta), `update_contact_details` (acción sensible) | `district`, `service`; `request_id`; `customer_id`, `email`, `phone` |
| Compartido (`bank-mcp`) | `find_branches` (consulta), `get_request_status` (consulta), `update_contact_details` (acción sensible) | `district`, `service`; `request_id`; `customer_id`, `email`, `phone` |

El MCP compartido devolvió las tres herramientas para el dominio `support`:

```text
https://ca-mcp-server.icybush-2ea2dfc1.eastus2.azurecontainerapps.io/mcp · support · 3 tools

find_branches           consulta         district, service
get_request_status      consulta         request_id
update_contact_details  acción sensible  customer_id, email, phone
```

### Pruebas en `dev/chat.py` (paso 12)

| Prueba | Mensaje | Tool solicitada | Resultado | Primer texto / respuesta completa (ms) |
|---|---|---|---|---:|
| Consulta de agencia | ¿Dónde hay una agencia en Miraflores? | `find_branches(district=Miraflores)` | La herramienta encontró la Agencia Miraflores, ubicada en Calle Ficticia 456, y devolvió información sobre su horario y los servicios disponibles. | 18 280 / 18 565 |
| Actualización de datos | Soy CUS-1001, actualiza mi correo a ana.demo@example.com | `update_contact_details(customer_id=CUS-1001, email=ana.demo@example.com, phone=None)` | La solicitud quedó en `pendiente_aprobacion`. El agente indicó que el cambio requiere la aprobación de un asesor y una validación mediante un código enviado al correo anterior; por eso, el dato no se modificó durante la conversación. | 17 757 / 18 095 |
| Consulta sin tool disponible | ¿Cuál es el saldo de mi cuenta de ahorros? | Ninguna | El agente clasificó la consulta como `out_of_scope`. Indicó que no podía consultar el saldo desde ese canal y orientó al usuario a la app, la banca por internet, la banca telefónica o una agencia. | 11 318 / 11 618 |

### Pruebas directas del mock

**Consulta de agencias**

```text
find_branches district=Miraflores
```

La llamada se ejecutó correctamente y devolvió la Agencia Miraflores. El tiempo registrado fue de **21 387 ms** hasta el primer texto y **21 554 ms** para completar la respuesta.

**Validación de un identificador inválido**

```text
customer_id = ABC
```

El agente rechazó el identificador porque no cumple el formato `CUS-####`. La actualización no se ejecutó y se explicó que el cambio de correo o teléfono requiere validación y aprobación. El tiempo fue de **11 223 ms** para el primer texto y **11 829 ms** para la respuesta completa.

**Acceso a una tool de otro dominio**

También se comprobó el aislamiento por dominio del mock. `simulate_installment` pertenece a `loans`; al intentar invocarla con `DOMAIN=support` desde `dev/mcp/mcp_tools.py`, el mock respondió:

```text
Unknown tool: 'simulate_installment'
```

Con esto se confirmó que el mock no expone desde `support` una herramienta registrada para otro dominio.

### Respuesta cuando no hay una tool disponible

En la consulta sobre el saldo, el agente no inventó un monto ni presentó información financiera sin respaldo. Reconoció que no tenía una herramienta para consultar ese dato y derivó al usuario a los canales correspondientes. El control por dominio también evitó que el mock aceptara `simulate_installment`, que pertenece a `loans`.

### Conclusión

Las pruebas permitieron comprobar el funcionamiento de las herramientas de `support` tanto en el mock local como en el MCP compartido. `find_branches` respondió con información de la agencia; `update_contact_details` respetó el flujo de aprobación y no modificó los datos sin la validación requerida; y las consultas que no contaban con una herramienta se derivaron a los canales adecuados.

Además, la validación de `customer_id = ABC` confirmó el control de formato y la llamada a `simulate_installment` mostró que el mock restringe el acceso a las herramientas del dominio configurado. En conjunto, los resultados muestran que el agente utiliza las tools disponibles y evita ejecutar acciones o consultas que no están habilitadas para `support`.
## Sesión 7 — Skills, memoria de trabajo y Agent Framework

Dominio: `support`. Se ejecutó la misma prueba desde `dev/chat.py` con los dos runtimes: primero `react` y después `agent_framework`. En ambas ejecuciones se consultó una agencia, se intentó iniciar una actualización de datos, se probó una herramienta de otro dominio y se preguntó por la dirección de la agencia para comprobar si el agente podía recuperar ese dato de la conversación.

La secuencia de cada ejecución fue la siguiente:

- **`react`:** consulta de agencia en Miraflores → solicitud de actualización de contacto para `CUS-1001` → intento de simulación de cuota → consulta de saldo → pregunta por la dirección de la agencia.
- **`agent_framework`:** consulta de agencia en Miraflores → solicitud de actualización de contacto para `CUS-1001` → intento de simulación de cuota → pregunta por la dirección de la agencia → consulta sobre una devolución por cobro indebido.

### Comparación de los dos runtimes

| | `react` | `agent_framework` |
|---|---|---|
| Tool ejecutada para consultar la agencia | `find_branches(district=Miraflores)` | `find_branches(district=Miraflores)` |
| Resultado de la consulta | Encontró la Agencia Miraflores (`BRN-02`), ubicada en Calle Ficticia 456. Indicó el horario de lunes a viernes de 9:00 a 18:00 y los servicios de caja y plataforma. | Devolvió la misma agencia (`BRN-02`), dirección, horario y servicios. |
| Solicitud de actualización de contacto | No se llamó a `update_contact_details`. El agente pidió que se indicara si se quería cambiar el correo o el celular y que se proporcionara el nuevo dato. Explicó que lo repetiría para confirmarlo antes de continuar. | Tampoco se llamó a `update_contact_details`. Solicitó el dato que se quería cambiar y explicó que no aplicaría la actualización sin la confirmación correspondiente. |
| Intento de usar `simulate_installment` | No se ejecutó ninguna tool. La consulta se clasificó como `out_of_scope` y el agente indicó que no podía simular cuotas desde ese canal. | No se ejecutó ninguna tool. La consulta se clasificó como `out_of_scope` y el agente orientó a la app, la web, una agencia o banca telefónica. |
| Consulta de saldo | Respondió que no podía consultar el saldo desde ese canal y orientó a los canales de atención. | No se realizó esta consulta en la segunda ejecución. |
| Pregunta de memoria | Respondió sin una nueva llamada (`→`): “La dirección de la Agencia Miraflores (BRN-02) es Calle Ficticia 456”. | También respondió sin una nueva llamada (`→`): “La dirección de la Agencia Miraflores (BRN-02) es Calle Ficticia 456”. |
| Consulta adicional | No se realizó una consulta adicional. | Ante la solicitud de devolución por cobro indebido, respondió que no podía tramitarla desde el chat y explicó los canales disponibles y los datos de la operación que se solicitan para presentar el reclamo. No ejecutó ninguna tool ni realizó una devolución. |

### Tiempos y tokens registrados

Los valores corresponden a cada mensaje de las consolas. Se muestran por separado para mantener la relación entre cada tiempo, el runtime y la respuesta observada.

| Prueba | `react`: primer texto / respuesta completa (ms) | Tokens entrada / salida | `agent_framework`: primer texto / respuesta completa (ms) | Tokens entrada / salida |
|---|---:|---:|---:|---:|
| `find_branches` | 14 020 / 14 190 | 2630 / 503 | 14 458 / 14 607 | 2630 / 503 |
| Solicitud de actualización de contacto | 14 235 / 14 506 | 1833 / 1315 | 16 034 / 16 951 | 1833 / 1301 |
| `simulate_installment` | 11 266 / 11 449 | 2068 / 1119 | 15 025 / 15 187 | 2040 / 1296 |
| Consulta de saldo | 13 903 / 14 122 | 2201 / 1353 | — | — |
| Pregunta por la dirección de la agencia | 11 770 / 11 788 | 2433 / 877 | 10 430 / 10 447 | 2241 / 664 |
| Devolución por cobro indebido | — | — | 30 115 / 30 418 | 2303 / 3687 |

### ¿La skill frenó una tool de otro dominio?

Sí. En los dos runtimes se probó `simulate_installment amount=20000 term_months=24`, que corresponde al dominio `loans` y no forma parte de las herramientas disponibles para `support`. En ninguno de los registros aparece una llamada `→ simulate_installment`: el agente clasificó la consulta como `out_of_scope` y explicó que no podía realizar la simulación desde ese canal. Por tanto, no se ejecutó una herramienta de otro dominio.

### ¿La memoria de trabajo permitió recuperar la información de la agencia?

Sí. Después de consultar `find_branches`, se preguntó “¿Cuál era la dirección de la agencia?”. En ambas ejecuciones el agente respondió con Calle Ficticia 456 e identificó la Agencia Miraflores (`BRN-02`), sin volver a invocar `find_branches`. Esto muestra que pudo utilizar la información obtenida al inicio de la conversación para responder el seguimiento.

La consulta de saldo se realizó únicamente en `react`. En ese caso el agente reconoció que no tenía una herramienta para consultar información financiera y no inventó un monto. En `agent_framework` se probó en su lugar una consulta sobre una devolución por cobro indebido; el agente explicó cómo iniciar el reclamo, pero no lo tramitó ni llamó a una herramienta.

### Diferencias entre los dos runtimes

- Ambos consultaron la agencia con `find_branches` y recuperaron su dirección sin volver a llamar al MCP.
- Ninguno inició la actualización de contacto porque faltaba el dato nuevo. Tampoco ejecutaron `simulate_installment`, que pertenece a `loans`.
- Los tiempos fueron similares en las consultas compartidas. Estas dos ejecuciones no son suficientes para determinar qué runtime es más rápido.
- Las pruebas adicionales fueron distintas: `react` consultó el saldo y `agent_framework` respondió sobre una devolución por cobro indebido.

### Conclusión

Los dos runtimes respetaron las herramientas disponibles para `support` y recuperaron correctamente la dirección de la agencia desde el contexto de la conversación. También evitaron ejecutar operaciones que no podían resolver desde ese dominio.
## Sesión 8 — Aprobación humana, validación y reintentos

Dominio: `support` (paso 6).

| Caso | Runtime | Mensaje | Qué pasó | Resultado o ID |
|---|---|---|---|---|
| Aprobar | `agent_framework` | `Soy CUS-1001, actualiza mi correo a ana.demo@example.com`. Luego: `Sí, realiza la actualización de mi correo`. Asesor: `s`. | El agente pidió confirmar el cambio y, después de la confirmación, solicitó `update_contact_details`. La acción quedó pendiente y no se ejecutó antes de la aprobación. Al responder `s`, la tool devolvió los datos del cliente con el correo solicitado. El agente informó que la solicitud quedó registrada para procesamiento y que el cambio aún no estaba aplicado. Se observó el mismo flujo exitoso en dos solicitudes. | `call-56df59af` y `call-115af2ef`. Cliente `CUS-1001`; correo `ana.demo@example.com`. |
| Rechazar | `react` | `Soy CUS-1001, actualiza mi correo a ana.demo@example.com`. Luego: `Sí, realiza la actualización de mi correo`. Asesor: `n`. | La acción `update_contact_details` quedó pendiente de aprobación. Al responder `n`, el asesor rechazó la solicitud; el agente indicó que no se ejecutó. | `call_xyucF8aewQOEWvjZnUBF3A7F`. Estado: `rejected`. |
| Error de negocio (`CUS-9999`) | `agent_framework` y `react` | `Soy CUS-9999, ¿qué comisiones me cobraron?` | No se validó el error de negocio porque la consulta de comisiones no corresponde a las tools del dominio `support`. En `agent_framework` terminó como `out_of_scope`; en `react`, como `data_query`. En los logs no aparece una invocación de tool para esta consulta. | Sin ID. Prueba pendiente con una tool del dominio `support`. |
| Input inválido | `agent_framework` y `react` | `Mi número de cliente es 1001, cambia mi correo a ana.demo@example.com`. | `agent_framework` solicitó confirmar que el código correcto era `CUS-1001`; después de la confirmación se generó la acción pendiente y fue aprobada. `react` pidió ingresar el código en formato `CUS-1001` y confirmar la operación; la conversación terminó antes de invocar la tool. En ambos casos el modelo pidió aclarar el dato, por lo que no se observó un argumento inválido llegando a la validación JSON Schema. | `agent_framework`: `call-115af2ef` (solicitud posterior aprobada). `react`: sin ID; no se invocó la tool. |

### La trayectoria en el log

**Agent Framework**

```text
INFO agent.application.chat_service: trayectoria c33cae14-4e97-42cd-b70f-210fea179b0a: sin tools → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria c33cae14-4e97-42cd-b70f-210fea179b0a: update_contact_details pending_approval → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria c33cae14-4e97-42cd-b70f-210fea179b0a: decisión del asesor → update_contact_details ok
INFO agent.application.chat_service: trayectoria c33cae14-4e97-42cd-b70f-210fea179b0a: sin tools → respuesta out_of_scope
INFO agent.application.chat_service: trayectoria c33cae14-4e97-42cd-b70f-210fea179b0a: sin tools → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria c33cae14-4e97-42cd-b70f-210fea179b0a: update_contact_details pending_approval → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria c33cae14-4e97-42cd-b70f-210fea179b0a: decisión del asesor → update_contact_details ok
```

**React**

```text
INFO agent.application.chat_service: trayectoria f9ab3154-789d-4d11-9389-60cecfc35644: sin tools → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria f9ab3154-789d-4d11-9389-60cecfc35644: update_contact_details pending_approval → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria f9ab3154-789d-4d11-9389-60cecfc35644: decisión del asesor → update_contact_details rejected
INFO agent.application.chat_service: trayectoria f9ab3154-789d-4d11-9389-60cecfc35644: sin tools → respuesta data_query
INFO agent.application.chat_service: trayectoria f9ab3154-789d-4d11-9389-60cecfc35644: sin tools → respuesta sensitive_action
```

### ¿Algo se ejecutó sin que lo aprobaras?

No. En ambos runtimes, `update_contact_details` quedó primero en estado `pending_approval`. En `agent_framework`, la tool se ejecutó después de que el asesor respondió `s`. En `react`, la solicitud rechazada después de responder `n` quedó en estado `rejected` y no se ejecutó. No se observó una ejecución de una acción sensible sin aprobación.

### Conclusión

Se comprobó el control humano con los dos runtimes. `agent_framework` permitió aprobar dos solicitudes de actualización del correo de `CUS-1001` y recibió la respuesta del MCP; `react` permitió rechazar la solicitud sin ejecutarla. Las trayectorias registraron la acción pendiente y el resultado de la decisión del asesor.

También se comprobó que, ante el código de cliente escrito como `1001`, el agente solicitó aclararlo al formato `CUS-1001` antes de continuar. Esta interacción no demuestra por sí sola la validación de un argumento inválido directamente contra JSON Schema, porque el modelo corrigió/pidió aclarar el dato antes de llamar a la tool.

La prueba con `CUS-9999` no llegó a comprobar un error de negocio del MCP: se consultaron comisiones, una operación fuera del dominio `support`, y no se invocó ninguna tool. Queda pendiente repetir ese caso con una operación del dominio `support`, además de comprobar la tolerancia a fallos de conexión mediante los tests automatizados del paso 3.

## Sesión 9 — Despliegue en Azure

Equipo: `team-10`. Dominio: `support`.

| Comprobación | Resultado |
|---|---|
| Tests en el contenedor (paso 3) | 139 passed, 5 skipped en 8.17 s |
| Acción aprobada después de reiniciar `uvicorn` (paso 2, Cosmos DB) | La acción pendiente sobrevivió al reinicio. El primer intento contra MCP falló porque el servicio bancario estaba frío. En una nueva solicitud, la aprobación fue procesada; el servicio informó que quedaba registrada para procesamiento, sin confirmar la aplicación final del cambio. |
| Imagen desplegada (`team-10/agent:<sha>`) | `team-10/agent:0502ef3b36d2b076f33345b1ccf7a66ff340f3c0` |
| Revisión activa y duración del job `deploy` | `ca-agent-chat-10--0000002`, estado `RunningAtMaxScale`. Job `deploy` exitoso, aproximadamente 1 min 56 s. |
| `/health` del agente desplegado | `ok`, con autenticación de Entra ID. |
| Respuesta con `Fuentes:` contra Azure (y su tiempo en ms) | 3 referencias recuperadas. Primer texto: 8544 ms; respuesta completa: 8770 ms. |
| Acción aprobada contra Azure, con su `resultado:` | `update_contact_details` quedó pendiente de aprobación. Tras la aprobación del asesor, MCP devolvió `resultado` y el agente confirmó la actualización. Se omiten datos personales del cliente. |

### Qué pone Azure y qué pone la imagen

**Variables configuradas por Azure (solo nombres):**

`APPLICATIONINSIGHTS_CONNECTION_STRING`, `AZURE_CLIENT_ID`, `AZURE_OPENAI_ENDPOINT`, `COSMOS_CONTAINER`, `COSMOS_DATABASE`, `COSMOS_ENDPOINT`, `FOUNDRY_PROJECT_ENDPOINT`, `KEY_VAULT_URI`, `MCP_SCOPE`, `MCP_URL`, `SEARCH_ENDPOINT`, `SEARCH_INDEX`, `TEAM_ID`.

**Variables y configuración de la imagen:**

`DOMAIN=support`, `FOUNDRY_AUTH_PROVIDER=entra_id`, `KNOWLEDGE_BASE=azure_search`, `AGENT_RUNTIME=agent_framework`. Puerto de aplicación: `8000`. La imagen utiliza `AZURE_OPENAI_ENDPOINT` como alternativa para `FOUNDRY_ENDPOINT`.

### Problemas que encontraste y cómo los resolviste

- La versión inicial de `dev/chat.py` no incorporaba autenticación para Azure. Se actualizó desde la referencia `t4-s9` para utilizar `AGENT_SCOPE`, `DefaultAzureCredential` y validar `/health`.
- La primera petición desde el cliente sin autenticación produjo un error HTTP cuyo cuerpo vacío provocó `JSONDecodeError`. Se corrigió al utilizar la versión del cliente con token Bearer y manejo de errores.
- Durante la prueba de persistencia con Cosmos DB, el primer intento contra MCP después del reinicio falló porque el servicio bancario estaba frío. Se repitió la solicitud y se obtuvo respuesta del MCP.
- La consulta sobre seguimiento de solicitudes recuperó estados y plazos, pero las fuentes disponibles no especificaron el procedimiento exacto ni los datos requeridos para consultar el estado.
- La reconciliación entre `main` y `equipo-10` presentó conflictos de código y pruebas. Se conservaron las implementaciones consolidadas del equipo y se verificaron nuevamente las 144 pruebas.

### Conclusión

Se completó el despliegue del agente `support` en Azure mediante GitHub Actions. Los jobs `test` y `deploy` finalizaron correctamente; la imagen se publicó en ACR y la revisión `ca-agent-chat-10--0000002` alcanzó el estado `RunningAtMaxScale`.

Se verificó el acceso autenticado mediante Entra ID, el endpoint `/health`, la recuperación de fuentes desde Azure AI Search y el flujo de aprobación humana de una acción sensible mediante el MCP compartido.

También se comprobó la persistencia del estado pendiente en Cosmos DB después de reiniciar `uvicorn`. La primera operación posterior encontró el servicio bancario frío, por lo que se documentó esa incidencia sin asumir que la solicitud había sido aplicada.

Las 144 pruebas locales y las validaciones del pipeline quedaron aprobadas. El trabajo de código se integró en `main`; queda pendiente el PR de resultados de esta sesión.
