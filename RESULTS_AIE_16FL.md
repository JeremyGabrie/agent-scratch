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

## Sesión 6 — Tools del MCP en el chat

Dominio: `support`. MCP: el mock (`http://127.0.0.1:8200/mcp`) y el compartido (`bank-mcp`,
`https://ca-mcp-server.icybush-2ea2dfc1.eastus2.azurecontainerapps.io/mcp`, con `MCP_SCOPE` y token de
`az login`).

### Tools de tu dominio

| MCP | Tools que lista `dev/mcp/mcp_tools.py` |
|---|---|
| Mock | 3 tools: `find_branches` (consulta: district, service), `get_request_status` (consulta: request_id), `update_contact_details` (acción sensible: customer_id, email, phone) |
| Compartido | Las mismas 3 tools, con los mismos parámetros: `find_branches`, `get_request_status`, `update_contact_details` |

Con el mock y `DOMAIN=loans`, el mismo comando lista 3 tools de `loans`. En el compartido, `get_request_status
request_id=REQ-6001` devolvió "Reposición de tarjeta", `in_progress`, y `find_branches district=Miraflores`
devolvió la Agencia Miraflores. La primera llamada al compartido respondió "El servicio del banco no
responde; intenta de nuevo en unos minutos" y al reintentar funcionó.

### Conversación en `dev/chat.py` (paso 12)

Agente con Foundry (`gpt-5-mini`), Azure AI Search (`idx-team-10`) y el mock MCP.

| Prueba | Mensaje | Tool pedida (`→`) | Qué pasó | Primer texto / respuesta completa (ms) |
|---|---|---|---|---|
| Consulta de tu dominio | Soy CUS-1001, ¿dónde hay una agencia en Miraflores? | `find_branches(district=Miraflores)` | Respondió con la Agencia Miraflores, Calle Ficticia 456, lunes a viernes 9:00–18:00, caja y plataforma: los datos de la tool | 19133 / 19635 |
| Acción confirmada | Soy CUS-1001, actualiza mi correo a ana.demo@example.com (y después: "Sí, confirmo el cambio") | `update_contact_details(customer_id=CUS-1001, email=ana.demo@example.com, phone=None)` | **NO SE EJECUTA, pendiente de aprobación.** El agente dijo que lo solicitó y que queda pendiente de revisión por un asesor; no dijo que ya se hizo. Lo pidió en el primer mensaje, porque el cliente ya lo estaba pidiendo, y otra vez al confirmar | 22402 / 24629 (confirmación: 22382 / 22661) |
| Sin tool que la resuelva | ¿Cuál es el saldo de mi cuenta de ahorros? | ninguna | Respondió que no puede consultar saldos desde aquí y sugirió la app, la banca por internet o la banca por teléfono (01) 555-0200, citando `channels-and-hours.html` | 9948 / 10239 |
| Tool de otro dominio | `uv run python dev/mcp/mcp_tools.py simulate_installment amount=20000 term_months=24` | `simulate_installment` | `Error de la tool: Unknown tool: 'simulate_installment'`: para `support` esa tool no existe, en el mock y en el compartido | — |

Con el MCP compartido (paso 14), el mismo agente arrancó con `MCP: https://ca-mcp-server…/mcp · 3 tools`:

| Mensaje | Tool pedida (`→`) | Qué pasó | Primer texto / respuesta completa (ms) |
|---|---|---|---|
| Soy CUS-1001, ¿en qué estado está mi solicitud REQ-6001? | `get_request_status(request_id=REQ-6001)` | "Su solicitud REQ-6001 está en evaluación. Última actualización: 24/10/2026", con los datos de la tool | 13926 / 14109 |
| Soy CUS-1001, actualiza mi correo a ana.demo@example.com, confirmo el cambio | `update_contact_details(...)` | NO SE EJECUTA, pendiente de aprobación; el agente lo explicó así | 24381 / 24698 |

### ¿El modelo inventó algún dato cuando ninguna tool lo resolvía?

No. Ante "¿Cuál es el saldo de mi cuenta de ahorros?" no pidió ninguna tool (no hay una de saldos en
`support`) y no dio un monto: dijo que no puede consultarlo y mandó al cliente a los canales, con datos
del corpus (`channels-and-hours.html`). Las respuestas con tool usaron solo lo que devolvió la tool
(dirección y horario de la agencia, estado y fecha de REQ-6001). Un detalle: en esa respuesta clasificó
la intención como `data_query`, aunque no la pudo resolver.

### Conclusión

El agente ya decide solo qué tool pedir: sacó `CUS-1001` y `REQ-6001` del mensaje, eligió la tool por
su descripción y mostró cada `→` antes de la respuesta en stream. Las acciones sensibles nunca llegan
al MCP: quedan pendientes de aprobación y el modelo lo dice sin dar la acción por hecha. Pasar del mock
al MCP compartido fue solo cambiar `MCP_URL` y `MCP_SCOPE` en el `.env` (la URL lleva `/mcp` al final);
el agente y las tools no cambiaron. Lo más lento es la primera respuesta: entre 10 y 25 segundos, porque
cada vuelta con tools es otra llamada a un modelo que razona. A mejorar: el compartido tuvo una falla
pasajera del banco simulado, y la intención de las preguntas sin tool debería ser `out_of_scope` o
`product_question`.

## Sesión 7 — Skills, memoria de trabajo y Agent Framework

Dominio: `support`. La misma conversación con los dos runtimes (paso 7), contra Foundry (`gpt-5-mini`),
Azure AI Search (`idx-team-10`) y el MCP compartido. Skill `support`: `get_request_status`, `find_branches`,
`update_contact_details`, `max_tool_rounds: 4`.

Mensajes, en orden: "Soy CUS-1001, ¿dónde hay una agencia en Miraflores?" · "Soy CUS-1001, actualiza mi
correo a ana.demo@example.com" · "Sí, confirmo el cambio" · "¿Cuál era la dirección de la agencia?" ·
"¿Cuál es el saldo de mi cuenta de ahorros?" · "Bloquea mi tarjeta CRD-2001".

| | `react` | `agent_framework` |
|---|---|---|
| Tools pedidas en la consulta | `find_branches(district=Miraflores)` | `find_branches(district=Miraflores, service=None)` |
| La acción sensible quedó **NO SE EJECUTA** | Sí: `update_contact_details(customer_id=CUS-1001, email=ana.demo@example.com)` después del "Sí, confirmo"; el agente dijo que quedó pendiente de aprobación de un asesor | Sí: la misma tool, después del "Sí, confirmo"; "La solicitud quedó pendiente de aprobación por un asesor" |
| Pregunta de memoria respondida sin `→` | Sí: "La dirección de la Agencia Miraflores es Calle Ficticia 456." | Sí: "La dirección de la Agencia Miraflores (BRN-02) es Calle Ficticia 456." |
| Primer texto (ms) | 12920 (consulta) | 11428 (consulta) |
| Respuesta completa (ms) | 13098 (consulta) | 11556 (consulta) |
| Tokens (entrada / salida) | 2698 / 620 (consulta) | 2702 / 622 (consulta) |

Los tiempos y tokens son del turno de la consulta. En el resto de la conversación los dos quedaron
parecidos: acción confirmada 17499 / 17784 ms (`react`) y 17786 / 17935 ms (`agent_framework`); pregunta de
memoria 13339 / 13383 ms y 11263 / 11449 ms.

Primera corrida con `react`: el banco simulado detrás del MCP estaba en frío y `find_branches` respondió
"El servicio del banco no responde; intenta de nuevo en unos minutos". Como ese turno no trajo datos, la
pregunta de memoria volvió a pedir `find_branches` (lo que anticipa la guía en Problemas frecuentes). La
tabla es de la segunda corrida, con el servicio ya despierto.

### ¿La skill frenó la tool de otro dominio?

Mensaje: "Bloquea mi tarjeta CRD-2001". Respuesta (`react`): "No puedo bloquear tarjetas desde este canal.
Puede hacerlo desde la app (disponible 24/7), llamar a nuestra línea (01) 555-0200 — lun-sáb 8:00-20:00 — o
acudir a una agencia." Con `agent_framework`, lo mismo. En ninguno de los dos hubo una línea `→`:
`block_card` no está en la skill de `support` ni el MCP la muestra para ese dominio, así que el modelo no
la tiene. Intención `out_of_scope`, sin inventar un bloqueo.

### Diferencias entre los dos runtimes

- **Comportamiento:** el mismo. Las mismas tools, la acción sensible NO SE EJECUTA en los dos, la memoria
  de trabajo responde sin volver a consultar y el stream llega en pedazos (los eventos `→` antes del texto).
- **Argumentos de la tool:** Agent Framework manda también los opcionales vacíos (`service=None`,
  `phone=None`); el ciclo propio solo los que el modelo llenó. El MCP los acepta igual.
- **Tiempo y tokens:** muy parecidos (diferencias de 1 a 2 s y de pocos tokens), porque los dos llaman al
  mismo deployment de Foundry; lo que más pesa es que `gpt-5-mini` razona antes de escribir.
- **Respuestas:** Agent Framework mencionó el código interno de la agencia (`BRN-02`); `react`, no. Es
  variación del modelo, no del runtime.
- **Confirmación antes de la acción:** con los dos, el modelo repitió el correo y pidió el "sí" antes de
  pedir `update_contact_details`, como dice el paso 3 de la skill. En la sesión 6, sin skill, la pedía
  apenas el cliente la mencionaba.

### Conclusión

Cambiar de runtime fue una línea del `.env` (`AGENT_RUNTIME`) y el agente se comportó igual: las reglas
viven en `ChatService` (la skill, la lista blanca, `_run` con la aprobación) y el framework solo conduce el
turno. La skill se notó en dos cosas: el modelo confirma el dato antes de la acción sensible y no ve tools
de otros dominios. La memoria de trabajo permite responder "¿cuál era la dirección?" sin volver a llamar al
MCP, pero depende de que el primer turno haya traído los datos: si la tool falló, el modelo vuelve a
consultar. Queda `AGENT_RUNTIME=agent_framework` en el `.env` para la sesión 8. A mejorar: el banco detrás
del MCP compartido tarda en despertar, y el primer mensaje del día puede fallar.

## Sesión 8 — Aprobación humana, validación y reintentos

Dominio: `support` (paso 6). Foundry (`gpt-5-mini`), Azure AI Search (`idx-team-10`) y el MCP compartido.

| Caso | Runtime | Mensaje | Qué pasó | Resultado o ID |
|---|---|---|---|---|
| Aprobar | `agent_framework` | "Soy CUS-1001, actualiza mi correo a ana.demo@example.com" y, cuando pidió confirmar, "Sí, confírmalo" | `update_contact_details(customer_id=CUS-1001, email=ana.demo@example.com, phone=None)` quedó **NO SE EJECUTA, pendiente de aprobación** (`action_id` `call-bc56e0e7`). Como asesor respondí `s`: recién ahí se ejecutó en el MCP, y el agente dijo "He registrado la solicitud de actualización del correo… quedó para que el banco la procese; no está aplicada aún." | `resultado:` el cliente `CUS-1001` (Lucía Quispe Ramos) con `"email": "ana.demo@example.com"` |
| Rechazar | `react` | El mismo mensaje y "Sí, confírmalo" | Quedó pendiente (`action_id` `call_2BY4aZbOPJmT2KWY2miZuXQv`, el id que pone Foundry). Respondí `n`: `rechazada por el asesor`, y el agente dijo "El asesor rechazó la solicitud de cambio de correo; la acción no se ejecutó." | `{"status": "rechazada", "detail": "El asesor rechazó la acción: no se ejecutó."}` |
| Error de negocio (`REQ-9999`) | `agent_framework` | "¿En qué estado está mi solicitud REQ-9999?" (en `support` las consultas no reciben `customer_id`, así que el cliente inexistente se probó con una solicitud inexistente) | `get_request_status(request_id=REQ-9999)` respondió con error; no se reintentó y el modelo pidió verificar el código, sin `502` | `error: {"error": "La solicitud REQ-9999 no existe"}` |
| Input inválido | `agent_framework` | "Mi número de cliente es 1001, cambia mi correo a ana.demo@example.com" | El modelo no llamó a la tool: leyó el patrón `^CUS-\d{4}$` y pidió confirmar "¿Su código de cliente es CUS-1001?". La validación con JSON Schema (`test_invalid_arguments_never_reach_the_mcp`) es la red de seguridad cuando el modelo se equivoca | Sin `→`; no salió nada al MCP |

Además, en la corrida de `agent_framework` la primera consulta (`find_branches`) encontró el banco
simulado en frío: "El servicio del banco no responde; intenta de nuevo en unos minutos". Es un error de
negocio (el MCP respondió), así que no se reintentó y el agente le ofreció al cliente intentarlo de nuevo,
sin cortar el turno. La caída del MCP en sí (reintento una vez y error claro) la prueban
`test_a_query_that_fails_once_is_retried` y `test_a_query_that_keeps_failing_is_an_error_and_the_turn_goes_on`.

### La trayectoria en el log

`agent_framework` (aprobar):

```text
INFO agent.application.chat_service: trayectoria cb97d631-0e9e-4cc1-995d-69a5882b02ab: find_branches error → respuesta data_query
INFO agent.application.chat_service: trayectoria cb97d631-0e9e-4cc1-995d-69a5882b02ab: sin tools → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria cb97d631-0e9e-4cc1-995d-69a5882b02ab: update_contact_details pending_approval → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria cb97d631-0e9e-4cc1-995d-69a5882b02ab: decisión del asesor → update_contact_details ok
INFO agent.application.chat_service: trayectoria 02e09185-9a95-46d7-b376-f055b5b474b7: get_request_status error → respuesta data_query
INFO agent.application.chat_service: trayectoria 8b390977-5ff3-4bf0-a680-97d26d028515: sin tools → respuesta sensitive_action
```

`react` (rechazar):

```text
INFO agent.application.chat_service: trayectoria bbf2360c-e7dd-41a2-bc3c-a4b56d43c7ce: find_branches ok → respuesta data_query
INFO agent.application.chat_service: trayectoria bbf2360c-e7dd-41a2-bc3c-a4b56d43c7ce: sin tools → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria bbf2360c-e7dd-41a2-bc3c-a4b56d43c7ce: update_contact_details pending_approval → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria bbf2360c-e7dd-41a2-bc3c-a4b56d43c7ce: decisión del asesor → update_contact_details rejected
```

### ¿Algo se ejecutó sin que lo aprobaras?

No. Con los dos runtimes, `update_contact_details` siempre apareció primero como **NO SE EJECUTA,
pendiente de aprobación**, y su `resultado:` del MCP salió solo después de mi `s`. Con `n` no llegó al MCP:
quedó `rejected` en la trayectoria y en la memoria. Antes de la acción, el modelo pidió confirmación al
cliente (la skill de `support`), así que hubo dos filtros: el cliente confirmó y el asesor aprobó.

### Conclusión

La aprobación humana vive en `_run` y `resolve`, no en el framework: funcionó igual con `react` y con
`agent_framework`, y el `action_id` de cada uno (el de Foundry o el `call-…` de `AgentFrameworkRuntime`)
sirvió para decidir por `POST /chat/actions`. Después de aprobar, el modelo contó solo lo que dijo el
resultado ("quedó para que el banco la procese; no está aplicada aún"), como pide `DECISION_HEADER`. El
agente no se cayó con ningún error: el banco en frío, la solicitud inexistente y el número sin formato
terminaron en una respuesta al cliente, no en un `502`. La trayectoria deja ver en una línea por turno qué
pasó. A tener en cuenta: el MCP compartido es de todos los equipos, así que aprobar el cambio de correo sí
lo cambió en el banco simulado para `CUS-1001`; y todo lo pendiente vive en memoria hasta la sesión 9.
`AGENT_RUNTIME=agent_framework` sigue en el `.env`.

## Sesión 9 — Despliegue en Azure

Equipo: `team-10`. Dominio: `support`.

| Comprobación | Resultado |
|---|---|
| Tests en el contenedor (paso 3) | `docker run --rm agent:test` → **139 passed, 5 skipped** (6.1 s). Los 5 skipped son los golden sets: `evals/` no entra en la imagen. Fuera del contenedor, `uv run pytest` dio también 139 passed, 5 skipped (antes de la sesión: 132 passed, 5 skipped); los 7 nuevos son los de `test_cosmos_store.py`. |
| Acción aprobada después de reiniciar `uvicorn` (paso 2, Cosmos DB) | **Sí.** En mi laptop, con `az login` y `COSMOS_CONTAINER=team-10`, el arranque dijo `Conversation store: Cosmos DB workshop/team-10`. `update_contact_details(customer_id=CUS-1001, email=ana.demo2@example.com)` quedó **NO SE EJECUTA, pendiente de aprobación** (`call-9004c846`) en el proceso `[14500]`. Lo detuve, levanté otro (`[18020]`) y recién ahí aprobé: `POST /chat/actions` → **200 con `resultado:`**, el cliente `CUS-1001` con el correo nuevo. La trayectoria `9609f860…` es la misma antes y después del reinicio: el historial y la acción vinieron de Cosmos DB. Hasta la sesión 8 esa decisión daba 404. |
| Imagen desplegada (`team-10/agent:<sha>`) | _Pendiente del merge a `main`._ `main` sigue en `1099c27` (5 de noviembre) y en GitHub Actions todas las corridas de `deploy-agent` son de pull request: el job `deploy` todavía no corrió. |
| Revisión activa y duración del job `deploy` | _Pendiente del merge a `main`._ |
| `/health` del agente desplegado | _Pendiente del despliegue._ |
| Respuesta con `Fuentes:` contra Azure (y su tiempo en ms) | _Pendiente del despliegue._ |
| Acción aprobada contra Azure, con su `resultado:` | _Pendiente del despliegue._ |

La imagen de producción (paso 4, `--build-arg DOMAIN=support`) arrancó con `Foundry auth provider: entra_id` y se detuvo con
`RuntimeError: KNOWLEDGE_BASE=azure_search requiere SEARCH_ENDPOINT y SEARCH_INDEX en .env.` (código de salida 1): el fail-fast
esperado sin Azure. Dentro de `/app` solo está `.venv` (sin `tests/`, `dev/` ni `data/`) y corre como el usuario `app`, sin privilegios.

### Qué pone Azure y qué pone la imagen

- **La imagen** (`ENV` del stage `runtime`, revisado con `docker image inspect`): `DOMAIN`, `FOUNDRY_AUTH_PROVIDER`, `KNOWLEDGE_BASE`,
  `AGENT_RUNTIME`, más `PATH` y `PYTHONUNBUFFERED`. El `CMD` copia `AZURE_OPENAI_ENDPOINT` a `FOUNDRY_ENDPOINT`.
- **Azure** (según `devops/DESPLIEGUE.md`; las pone Terraform en `ca-agent-chat-10`): `AZURE_OPENAI_ENDPOINT`, `AZURE_CLIENT_ID`,
  `TEAM_ID`, `APPLICATIONINSIGHTS_CONNECTION_STRING`, `COSMOS_ENDPOINT`, `COSMOS_DATABASE`, `COSMOS_CONTAINER`, `SEARCH_ENDPOINT`,
  `SEARCH_INDEX`, `MCP_URL`, `MCP_SCOPE` y `KEY_VAULT_URI`. Falta confirmarlas en la Container App con
  `az containerapp show ... --query "properties.template.containers[0].env[].name"`.

Ninguna es una api key ni una contraseña: son endpoints, nombres de recursos y el client id de la identidad administrada.

### Problemas que encontraste y cómo los resolviste

- **El MCP compartido en frío.** En el primer intento (`call-904d5ee8`) aprobé sin reiniciar y la tool respondió
  `El servicio del banco no responde`. Es un error de negocio y la acción aprobada no se reintenta. Repetí con el MCP ya despierto,
  ahora reiniciando `uvicorn` entre el pedido y la aprobación, y salió `resultado:`.
- **El modelo cuenta más de lo que pasó.** Con ese error dijo que la solicitud "quedó registrada para que el banco la procese", y
  antes de llamar a la tool, cuando solo pedía confirmación, dijo "He registrado la solicitud". Es el mismo punto débil de
  `DECISION_HEADER` que anoté en la sesión 8.
- **`az login` en la laptop.** `az login` fallaba con `ConnectionResetError(10054)` al listar los tenants desde la red corporativa;
  con `az login --tenant <id del tenant de la ficha>` entró directo a la suscripción del workshop.
- **`.env` en otra copia del repo.** El clon de esta sesión no tenía `.env` (`Falta FOUNDRY_ENDPOINT`); copié el de la sesión 6
  y pasé `COSMOS_ENDPOINT`, `COSMOS_DATABASE` y `COSMOS_CONTAINER` como variables de entorno al levantar `uvicorn`.

- **Sin acceso a `upstream`.** Tomé `.github/workflows/deploy-agent.yaml` y `devops/` de la rama del capitán (`s9_AIE_20JG`) y
  comprobé que son idénticos a los que trajo `s9_AIE_38DH`: es la copia del template, sin ediciones. `git status --short` mostró
  lo esperado: `M deploy-agent.yaml`, `A devops/DESPLIEGUE.md`, `M devops/Dockerfile`.
- **Golden sets saltados.** Los 5 tests de `test_golden_sets.py` piden el `evals.zip` de la plataforma (sesión 5), que no se
  versiona. Por eso local da 139 passed, 5 skipped, y no los 144 passed de la guía.
- **Docker detrás de un proxy con inspección TLS.** Construí las imágenes en un entorno cuya salida a internet pasa por un proxy
  con su propio certificado. Usé una copia temporal del `Dockerfile` que solo agrega ese certificado al stage `base`; el
  `Dockerfile` del repo no cambió.
- **Sin despliegue todavía.** Los pasos 7 y 8 dependen del merge del capitán a `main`; hasta entonces `ca-agent-chat-10` no tiene
  la imagen del agente.

### Conclusión

El historial y la acción pendiente pasan a Cosmos DB con otra implementación del puerto `ConversationStore`, sin tocar
`ChatService`; los tests de la API siguen en memoria y nunca tocan Cosmos. La imagen de producción no trae `.env` ni `data/`: la
imagen fija lo que no cambia entre entornos, Azure pone los endpoints y la identidad administrada, y sin AI Search la imagen se
detiene en vez de arrancar a medias. En mi laptop ya se vio: una
acción pendiente sobrevivió al reinicio de `uvicorn` y se aprobó en otro proceso. Por indicación del profesor, este PR solo trae
`RESULTS_AIE_16FL.md`. Falta el despliegue real: cuando el capitán haga el merge a `main`, completo la imagen, la revisión y las
pruebas contra Azure.
