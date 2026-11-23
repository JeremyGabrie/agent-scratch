# Resultados AIE-30RS

## Sesión 5 — Comparar los dos jueces

Mismo golden set (3x casos), mismo agente (`gpt-5-mini`), dos jueces.

- Juez local (G-Eval): `data/eval/support-20261113-150810.json`
- Juez azure_evaluation (decision-1): `data/eval/support-20261113-155127.json`

| Métrica | G-Eval (`JUDGE=local`) | decision-1 (`azure_evaluation`) |
|---|---|---|
| Apoyo (1–5) | 5.0/5| .0/5 |
| Relevancia (1–5) | 5.0/5 | 2.0/5 |
| Cita correcta (0–1) | 1.0 | 0.2 |
| Tokens (entrada / salida) | 686,794 | 297,9 |
| Tiempo de la corrida | 333s | 218s |

### ¿Las notas de apoyo y de cita correcta van en la misma dirección?

Tanto la cita de apoyo y cita corren al máximo, es decir van a la misma direccion de G-eval 5

### ¿Cuánto tardó cada corrida?

- Local (G-Eval): 333 segundos.
- azure_evaluation (decision-1): 218 segundos

### Casos donde no coinciden

Abriendo el detalle de G-Eval en el reasoning se observa que en relevancia coinciden ambos a 5

### Conclusión

Respecto a decision-1 es rápido y da probabilidades pero no da el detalle a comparacion de G-Eval es más lento pero da el detalle de porque falla

## Sesión 6 — Tools del MCP en el chat

Dominio: support. MCP: el mock (`http://127.0.0.1:8200/mcp`) y, si ya tienes `MCP_URL`, el compartido (`bank-mcp`).

### Tools de tu dominio

| MCP | Tools que lista `dev/mcp/mcp_tools.py` |
|---|---|
| Mock | 3 tools: find_branches (consulta: district, service), get_request_status (consulta: request_id), update_contact_details (acción sensible: customer_id, email, phone) |
| Compartido | Las mismas 3 tools, con los mismos parámetros: find_branches, get_request_status, update_contact_details |

### Conversación en `dev/chat.py` (paso 12)

| Prueba | Mensaje | Tool pedida (`→`) | Qué pasó | Primer texto / respuesta completa (ms) |
|---|---|---|---|---|
| Consulta de tu dominio | Soy CUS-1001, ¿dónde hay una agencia en Miraflores? | find_branches(district=Miraflores)| La Agencia Miraflores, Calle Ficticia 456, lunes a viernes 9:00–18:00, caja y plataforma: los datos de la tool | 19133 / 19635 |
| Acción confirmada | Soy CUS-1001, actualiza mi correo a ana.demo@example.com (y después: "Sí, confirmo el cambio")| update_contact_details(customer_id=CUS-1001, email=ana.demo@example.com, phone=None)| NO SE EJECUTA, pendiente de aprobación. | 22402 / 24629 (confirmación: 22382 / 22661)|
| Sin tool que la resuelva | ¿Cuál es el saldo de mi cuenta de ahorros? | ninguna | no puede consultar saldos desde aquí y sugirió la app, la banca por internet o la banca por teléfono (01) 555-0200, citando channels-and-hours, el cual esta llamando del corpus de nuestro dominio support.html | 9948 / 10239 |
| Tool de otro dominio | uv run python dev/mcp/mcp_tools.py simulate_installment amount=20000 term_months=24| simulate_installment| Error de la tool: Unknown tool: 'simulate_installment': para support esa tool no existe, en el mock y en el compartido | — |

### ¿El modelo inventó algún dato cuando ninguna tool lo resolvía?

No. Cuando preguntaron por el saldo, el agente no llamó a ninguna tool porque el dominio support no ofrece esa consulta. En su lugar, indicó que no podía verificarlo y recomendó los canales oficiales, con referencia a channels-and-hours.html. Para ubicar una agencia sí usó find_branches; el cambio de correo quedó esperando aprobación

### Conclusión

El agente identifica los datos del mensaje, como `CUS-1001` y `REQ-6001`, y selecciona la tool adecuada según su descripción. En streaming, muestra cada llamada (`→`) antes de responder. Las acciones sensibles quedan pendientes de aprobación y no se envían al MCP hasta ser aprobadas. Para usar el MCP compartido, basta configurar `MCP_URL` —con `/mcp` al final— y `MCP_SCOPE` en `.env`; no hay que modificar el agente ni las tools. La primera respuesta tarda más, entre 10 y 25 segundos, porque cada paso con tools requiere otra llamada al modelo. Como mejoras, conviene contemplar fallas temporales del banco simulado y clasificar las preguntas sin una tool adecuada como `out_of_scope` o `product_question`.

## Sesión 7 — Skills, memoria de trabajo y Agent Framework

Dominio: `support`. La misma conversación con los dos runtimes (paso 7).

| | `react` | `agent_framework` |
|---|---|---|
| Tools pedidas en la consulta | find_branches(district=Miraflores) | find_branches(district=Miraflores) |
| La acción sensible quedó **NO SE EJECUTA** | Sí: update_contact_details(customer_id=CUS-1001, email=ana.demo@example.com, phone=None), pendiente de aprobación | Sí: la misma llamada, pendiente de aprobación |
| Pregunta de memoria respondida sin `→` | “La dirección de la Agencia Miraflores (BRN-02) es Calle Ficticia 456”. | “La dirección de la Agencia Miraflores (BRN-02) es Calle Ficticia 456”. |
| Primer texto (ms) | 30982 | 34876 |
| Respuesta completa (ms) | 31124 | 35037|
| Tokens (entrada / salida) |2680 / 489| 2680 / 493 |

### ¿La skill frenó la tool de otro dominio?

*Mensaje:* “Bloquea mi tarjeta CRD-2001” .
*Respuesta:* En ambos runtimes, los registros no muestran una llamada `→ block_card`: el agente explicó que no podía bloquear tarjetas desde ese canal y derivó al bloqueo desde la app —que puede tardar hasta 24 horas— o al teléfono (01) 555-0200. Esto es un caso de **tool no disponible**, no de una acción ejecutada ni de una llamada pendiente de aprobación. La causa es el filtrado por capas: `block_card` pertenece a `cards`, el MCP compartido filtra las tools por dominio y la skill activa de `support` solo permite `find_branches`, `get_request_status` y `update_contact_details`. Como `block_card` no está en el conjunto de tools expuesto al agente para esta conversación, el modelo no puede seleccionarla ni iniciar el flujo de aprobación. La respuesta mantiene la separación de dominios y orienta al cliente hacia canales que sí pueden gestionar el bloqueo.

### Diferencias entre los dos runtimes

- *Comportamiento:* no se observaron diferencias funcionales. Ambos runtimes solicitaron las mismas tools con los mismos argumentos, dejaron la acción sensible pendiente de aprobación, respondieron la pregunta de memoria y rechazaron la solicitud del dominio ajeno.
- *Tokens y latencia:* los tokens de entrada fueron casi iguales, coherente con que `ChatService` prepara los mensajes en ambos casos y el runtime conduce las iteraciones de tools. La consulta tardó 31 s con `react` y 35 s con `agent_framework`; los demás turnos estuvieron entre 12 y 34 s. Con estas mediciones, la diferencia de cuatro segundos no demuestra una ventaja de rendimiento de un runtime: puede estar dentro de la variabilidad de `gpt-5-mini`.
- *Memoria de trabajo (`react`):* en tres corridas se observaron resultados distintos. En la primera, el MCP compartido estaba frío y `find_branches` falló con “El servicio del banco no responde”; al no haber dirección disponible en memoria, el agente volvió a consultar la tool. En la segunda, la dirección sí estaba guardada —el resultado de la tool se conserva recortado a 600 caracteres y la sesión tenía 8 mensajes, por debajo del límite de 20—, pero el modelo respondió que los fragmentos no la contenían. En la tercera, respondió correctamente sin llamar a la tool. Esto apunta a dos factores distintos: disponibilidad temporal del MCP y variabilidad del modelo al recuperar información de la memoria. Como el harness entrega los mismos datos a ambos runtimes, estas corridas no muestran por sí solas una diferencia atribuible al runtime.

### Conclusión

Para ambiar de runtime se configura mediante `AGENT_RUNTIME`; en estas pruebas, `react` y `agent_framework` mostraron el mismo comportamiento funcional. La selección de tools por dominio y la aprobación de acciones sensibles se mantienen en el agente y en la configuración MCP: la skill de `support` impidió que se invocara una tool de `loans` o `cards`, mientras que la actualización de contacto sí quedó pendiente de aprobación. La memoria de trabajo pudo responder la dirección sin repetir la llamada a `find_branches`, aunque las tres corridas con `react` mostraron que la recuperación puede variar y que una caída temporal del MCP afecta qué información queda disponible.

## Sesión 8 — Aprobación humana, validación y reintentos

Dominio: `support (paso 6).

| Caso | Runtime | Mensaje | Qué pasó | Resultado o ID |
|---|---|---|---|---|
| Aprobar | `agent_framework` | Soy CUS-1001, actualiza mi correo a roxanasoto@example.com. Repondo con: Sí y por ultimo confirmo que realice la actualización de mi correo. Asesor: s | El agente pidió confirmar el cambio y dejó la acción pendiente; no se ejecutó antes de la aprobación. Al responder `s`, solicitó `update_contact_details`; la tool devolvió los datos del cliente y el agente informó que la solicitud quedó registrada para procesamiento, pero que el cambio aún no estaba aplicado. | call-35163948 y call-115af2ef. Cliente CUS-1001; correo roxanasoto@example.com.|
| Rechazar | `react` | Soy CUS-1001, actualiza mi correo a roxansoto@example.com. Respondo con: Sí y por ultimo no confirmo la actualización de mi correo. Asesor: n.| La llamada a `update_contact_details` quedó pendiente de aprobación. Cuando el asesor respondió `n`, rechazó la solicitud y el agente confirmó que la acción no se ejecutó. | call_OpgjP9xeFaX0klEOg7ulvWo4. Estado: rejected.|
| Error de negocio (`CUS-9999`) | `agent_framework` y `react` | Soy CUS-9999, ¿qué comisiones me cobraron? | No se pudo validar el manejo de errores de negocio: la consulta de comisiones no corresponde a ninguna tool del dominio `support`. `agent_framework` clasificó la solicitud como `out_of_scope`, mientras que `react` la clasificó como `data_query`.| Sin ID. Prueba pendiente con una tool del dominio `support`. |
| Input inválido | `agent_framework` | Mi número de cliente es 1001, cambia mi correo a roxanasoto@example.com | El modelo no llamó a la tool: leyó el patrón ^CUS-\d{4}$ y pidió confirmar "¿Su código de cliente es CUS-1001?". La validación se dio con JSON Schema (test_invalid_arguments_never_reach_the_mcp) es la red de seguridad cuando el modelo falla.| `agent_framework`: `call-d39b37d1` (solicitud posterior aprobada). `react`: sin ID |

### La trayectoria en el log

`Agent Framework`
INFO agent.application.chat_service: trayectoria c7f568aa-6294-4a7c-a3f9-1aa3dcdb676b: sin tools → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria c7f568aa-6294-4a7c-a3f9-1aa3dcdb676b: update_contact_details pending_approval → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria c7f568aa-6294-4a7c-a3f9-1aa3dcdb676b: decisión del asesor → update_contact_details ok
INFO agent.application.chat_service: trayectoria c7f568aa-6294-4a7c-a3f9-1aa3dcdb676b: sin tools → respuesta out_of_scope
INFO agent.application.chat_service: trayectoria c7f568aa-6294-4a7c-a3f9-1aa3dcdb676b: sin tools → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria c7f568aa-6294-4a7c-a3f9-1aa3dcdb676b: update_contact_details pending_approval → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria c7f568aa-6294-4a7c-a3f9-1aa3dcdb676b: decisión del asesor → update_contact_details ok

`React`
INFO agent.application.chat_service: trayectoria 4d86711d-0c3f-46c8-aeea-3cf237fa3aee: sin tools → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria 4d86711d-0c3f-46c8-aeea-3cf237fa3aee: update_contact_details pending_approval → respuesta sensitive_action
INFO agent.application.chat_service: trayectoria 4d86711d-0c3f-46c8-aeea-3cf237fa3aee: decisión del asesor → update_contact_details rejected
INFO agent.application.chat_service: trayectoria 4d86711d-0c3f-46c8-aeea-3cf237fa3aee: sin tools → respuesta data_query
INFO agent.application.chat_service: trayectoria 4d86711d-0c3f-46c8-aeea-3cf237fa3aee: sin tools → respuesta sensitive_action

### ¿Algo se ejecutó sin que lo aprobaras?

No, todo fue con previa aprobacion. En ambos runtimes, `update_contact_details` quedó inicialmente en estado `pending_approval`. En `agent_framework`, la tool se ejecutó después de que el asesor respondió `s` y aprobó la solicitud. En `react`, tras responder `n`, la solicitud pasó a `rejected` y no se ejecutó. Por tanto, no se observó ninguna acción sin aprobación.

### Conclusión

Las pruebas muestran que el control humano se mantiene en ambos runtimes y que la acción sensible no se envía al MCP antes de la decisión del asesor. En `agent_framework`, las dos solicitudes de actualización de `CUS-1001` quedaron primero en `pending_approval`; tras responder `s`, las trayectorias registraron la decisión como `ok` y la tool devolvió los datos de la solicitud. El agente comunicó que el cambio quedó registrado para procesamiento, sin afirmar que el correo ya estuviera actualizado. En `react`, la trayectoria registró `pending_approval` y luego `rejected` tras responder `n`; la tool no se ejecutó. Esto confirma el flujo esperado en estas ejecuciones, aunque no sustituye pruebas sistemáticas de todos los caminos de aprobación.

La entrada `1001` tampoco ejercitó la validación de un argumento inválido en el servidor: el agente pidió aclarar o corregir el identificador a `CUS-1001` antes de llamar a la tool. Por ello, no se puede concluir a partir de este caso que el rechazo de formato de JSON Schema haya sido probado. La consulta de comisiones para `CUS-9999` no validó un error de negocio del MCP. No había una tool de comisiones disponible en el dominio `support` y no se registró ninguna invocación; además, los runtimes clasificaron la misma solicitud de forma distinta (`out_of_scope` en `agent_framework` y `data_query` en `react`). Para cubrir ese escenario, falta probar un error de negocio mediante una tool de `support` y evaluar por separado la tolerancia a fallos de conexión con las pruebas automatizadas previstas.

La evidencia apunta a que la seguridad del flujo no depende del runtime: ambos conducen las tools mediante el mismo `ChatService`, que filtra las disponibles según la skill, valida los argumentos contra el JSON Schema antes de llamar al MCP y convierte una acción sensible en `pending_approval`. Solo la decisión explícita `approve` llega a ejecutar la tool; `reject` registra el rechazo sin invocarla. Esto coincide con las trayectorias observadas: dos aprobaciones completadas con `agent_framework` y un rechazo en `react`. El runtime cambia cómo se orquesta el ciclo, no la política de negocio ni la compuerta de aprobación.
