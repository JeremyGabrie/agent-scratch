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