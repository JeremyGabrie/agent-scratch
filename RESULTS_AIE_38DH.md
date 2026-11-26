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

## Sesión 4 · Retrieval

Agente con RAG contra Foundry (`gpt-5-mini`, embeddings `text-embedding-3-small`), en streaming. Primero con la base local (Qdrant + BM25 + RRF) y después con Azure AI Search (`srch-workshop-jsu3`, índice `idx-team-10`, búsqueda híbrida y reranker semántico). Las cinco preguntas van en una misma conversación, en este orden. Fecha: 2026-11-13.

### Las cinco preguntas (`SEARCH_TOP_K=5`)

| Tipo | Pregunta | Fuentes en local | Fuentes en AI Search | ¿Fuente correcta? |
|---|---|---|---|---|
| regla del corpus | ¿Qué requisitos necesito para abrir una cuenta de ahorros? | account-opening.md (Requisitos, Por la aplicación, En agencia) | account-opening.md (Requisitos) | sí, en ambas |
| seguimiento | ¿y eso lo puedo hacer desde la app? | account-opening.md (Por la aplicación), app-faq.md (¿Puedo abrir una cuenta desde la app?) | las mismas dos, en orden inverso | sí: el rewrite entendió "eso" como abrir la cuenta |
| término exacto | ¿Qué es la validación biométrica? | service-glossary.md (Validación biométrica) | service-glossary.md (Validación biométrica) | sí, en ambas |
| documento vencido | ¿Qué decía la FAQ de 2023 sobre el horario de las agencias? | branches-faq.md (vigente) | branches-faq.md (vigente) | sí: `general-faq-2023.md` no aparece en ninguna |
| fuera del corpus | ¿A cuánto está el dólar hoy? | ninguna, `out_of_scope` | ninguna, `out_of_scope` | sí, en ambas |

| Pregunta | Primer texto / respuesta completa, local (ms) | Primer texto / respuesta completa, AI Search (ms) |
|---|---:|---:|
| requisitos | 8355 / 8507 | 6625 / 6760 |
| seguimiento | 10664 / 10854 | 11502 / 11515 |
| término exacto | 8429 / 8552 | 10418 / 10426 |
| documento vencido | 10413 / 10547 | 9669 / 9800 |
| fuera del corpus | 9323 / 9450 | 15931 / 16065 |

**¿Mejoró con el reranker?** En la pregunta de requisitos, sí: AI Search devolvió solo el fragmento de requisitos, y la respuesta quedó más precisa y más corta. En las demás las fuentes fueron las mismas. La latencia no cambia de forma consistente entre las dos bases: la domina el modelo, no la búsqueda.

### Observaciones

- **El streaming casi no se nota con `gpt-5-mini`.** El primer texto llega 100 a 200 ms antes que la respuesta completa, porque el modelo razona antes de escribir (de 376 a 1786 tokens de salida para respuestas de una o dos frases). Con el mock, el primer texto llegó en 179 ms y la respuesta completa en 688 ms. Para que el streaming sirva hay que bajar el razonamiento o usar un modelo sin él. Queda pendiente para la sesión 5.
- **El filtro de vigencia funciona, pero el modelo atribuye mal.** En la pregunta del documento vencido, la búsqueda solo trajo la FAQ vigente. Aun así, la respuesta dice "En la FAQ de 2023 decía…", repitiendo el año de la pregunta. El dato es correcto (es el horario vigente), pero la frase es falsa. Habría que reforzar en el prompt que no afirme de qué versión sale un dato.
- **El rewrite agrega una llamada al modelo en cada turno con historial**, y así se ve en el log (`llm SearchQuery`). Suma latencia y tokens.

### `SEARCH_TOP_K`

Base local; las mismas dos primeras preguntas.

| `SEARCH_TOP_K` | Tokens de entrada (requisitos / seguimiento) | Fuentes citadas en "requisitos" | ¿Falta información? |
|---:|---:|---|---|
| 2 | 590 / 904 | Requisitos, app-faq | sí: no menciona la apertura en agencia |
| 5 | 710 / 1080 | Requisitos, Por la aplicación, En agencia | no |
| 10 | 933 / 1311 | Requisitos, En agencia, Por la aplicación | no |

- Con 2 se pierde información: el fragmento "En agencia" no entra al contexto.
- Con 10, cada turno cuesta un 21 % a 31 % más de tokens de entrada que con 5, y la respuesta es la misma. El modelo no citó fuentes que no vinieran al caso, pero recibió fragmentos que no usó.
- **Decisión: `SEARCH_TOP_K=5`.** Es el valor más chico que no pierde información en estas preguntas. El corpus de `support` tiene secciones cortas, así que 5 fragmentos cubren una pregunta y su contexto cercano.

## Sesión 5 · Calidad del RAG

Golden set de `support` (30 casos de `evals.zip`, más mi caso), agente contra Foundry (`gpt-5-mini`) y Azure AI Search (`idx-team-10`), `SEARCH_TOP_K=5`, chunks de 1500 caracteres con datos personales enmascarados (`DNI [DNI]`: ningún número de 8 dígitos en `data/chunks`). Fecha: 2026-11-13.

### Línea base (S5)

```
Resumen de 30 casos (juez local):
  recall@5: 1.00   intención: 0.83   fuentes: 0.90   hechos: 0.74
  apoyo: 5.0/5   relevancia: 5.0/5   cita correcta: 1.0
  fugas de datos personales: 0   citas de fuentes prohibidas: 1
  tokens: 22629 de entrada, 13458 de salida
```

Qué hay detrás de los casos en NO:

| Casos | Qué pasó | Tipo de falla |
|---|---|---|
| support-07, 09, 13, 29, 30 | La respuesta da el dato correcto con otras palabras: "su celular, su correo electrónico y su dirección", "ser cliente por 6 meses", "en una agencia". `key_facts` exige el texto literal. | Falso negativo de la métrica: el modelo parafrasea. |
| support-08 | Explica el código al dato anterior parafraseado y lo clasifica como `sensitive_action`. | Paráfrasis más intención. |
| support-08, 09 | "¿Cómo se confirma el cambio de mi celular?" sale como `sensitive_action`. Es una pregunta informativa, no un pedido de cambio. | Intención: el prompt no separa preguntar *cómo* se cambia un dato de *pedir* el cambio. |
| support-29, 30 | Preguntas sobre los casos de ejemplo clasificadas como `data_query`. | Intención: zona gris entre consultar un caso y preguntar por un producto. |
| support-24 (expired) | No encontró "horarios especiales" para la banca por teléfono en feriados, y citó `channels-and-hours.html`. | Hecho faltante: el dato está en `branches-faq.md`, que no se recuperó. |
| **support-25 (noise)** | "¿Qué descuento tienen los colaboradores en el gimnasio?" se respondió desde `internal-notice-gym.md`, con 20 % de descuento. | **Fuente prohibida.** El aviso interno está indexado y la pregunta coincide palabra por palabra. |
| support-27 (out_of_scope) | No da el tipo de cambio, pero cita los canales para consultarlo. | Cita fuentes en una pregunta fuera de alcance. |

### Mi caso del golden set

`evals/golden/support.AIE_38DH.jsonl`: `support-AIE38DH`, de tipo `follow_up`. Primero el cliente pregunta "¿Qué necesito para abrir una cuenta de ahorros?" y después "¿Y eso lo puedo hacer desde la app?". Se espera `account-opening.md` o `app-faq.md` y el dato "10 minutos". Están prohibidos el aviso del gimnasio y la FAQ de 2023.

- **Por qué lo elegí:** es la pregunta de seguimiento que el corpus de `support` anuncia como reto ("¿y eso lo puedo hacer desde la app?"). "Eso" solo se entiende con el historial, así que el caso prueba el rewrite. Además, la misma frase existe como título en `app-faq.md` y puede atraer la búsqueda por palabras hacia la FAQ equivocada. El golden set base solo tiene 3 casos de seguimiento, y ninguno es este.
- **Cómo le fue:** pasó en todo: recall, intención, fuentes, hechos, apoyo 5.0 y cita 1.0.

### Antes y después (31 casos, un cambio por vez)

| Configuración | recall | intención | fuentes | hechos | apoyo | prohibidas | tokens de entrada | tiempo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **AI Search, `SEARCH_TOP_K=5`, chunk 1500 (equipo)** | **1.00** | **0.84** | **0.94** | **0.79** | **5.0** | **1** | **23 723** | 328 s |
| `SEARCH_TOP_K=3` | 1.00 | 0.84 | 0.94 | 0.75 | 5.0 | 1 | 20 912 (−12 %) | 331 s |
| `SEARCH_TOP_K=8` | 1.00 | 0.84 | 0.94 | 0.79 | 5.0 | 1 | 27 996 (+18 %) | 336 s |
| Base local, sin reranker | 0.96 | 0.90 | 0.90 | 0.86 | 5.0 | 1 | 24 001 | 318 s |
| Base local, chunk 800 | 0.96 | 0.84 | 0.94 | 0.82 | 5.0 | 1 | 23 914 | 326 s |

Notas para leer la tabla:

- **Chunk 800 no cambia nada en `support`:** salen los mismos 28 chunks que con 1500, porque ninguna sección supera 800 caracteres. Lo corrí en la base local para no reemplazar el índice compartido del equipo con una prueba. Entre "local 1500" y "local 800" el índice es el mismo, y aun así la intención varía 0.06 y los hechos 0.04. **Ese es el ruido de una corrida a otra del modelo:** diferencias de ese tamaño no indican mejora ni empeoramiento.
- **El reranker de AI Search sí aporta recall:** con la base local se pierde support-21 ("¿Y cuándo se aplica el cambio?"), que trae `contact-details-update.docx` en lugar de `request-status.html`. AI Search lo encuentra.
- **`SEARCH_TOP_K=3`** ahorra un 12 % de entrada, pero los hechos bajan a 0.75, justo en el límite de la meta. **`SEARCH_TOP_K=8`** cuesta un 18 % más sin mejorar nada.

**Decisión del equipo: AI Search con reranker, `SEARCH_TOP_K=5` y chunk 1500.** Es la única configuración con recall 1.00 que cumple la meta de hechos sin pagar tokens de más. Es la que queda en `.env` y en el índice.

### Los dos jueces (paso 11)

| Juez | apoyo | relevancia | cita correcta | tiempo de la corrida |
|---|---:|---:|---:|---:|
| G-Eval (`JUDGE=local`, `gpt-5-mini`) | 5.0 | 4.8 | 1.0 | 328 s |
| decision-1 (`--judge azure_evaluation`) | 5.0 | 4.9 | 1.0 | 207 s (−37 %) |

- Las notas de apoyo y de cita correcta van en la misma dirección. Los dos jueces le dan el máximo a las respuestas que tienen fuentes, y en este corpus no hubo casos donde se contradijeran.
- decision-1 es un 37 % más rápido. Por eso sirve como compuerta antes de desplegar, mientras que G-Eval queda para entender por qué falla un caso, gracias a su `reasoning`.
- Cuando todo sale 5.0, el juez no distingue configuraciones. En este dominio las diferencias aparecen en recall, intención y hechos, no en apoyo.

### Metas del tema 2

| Control | Meta | Resultado (configuración del equipo) | ¿Se cumple? |
|---|---|---:|---|
| recall@k | ≥ 0.80 | 1.00 | sí |
| hechos | ≥ 0.75 | 0.79 | sí, con poco margen |
| apoyo | ≥ 4.0 | 5.0 | sí |
| fugas de datos personales | 0 | 0 | sí |
| citas de fuentes prohibidas | 0 | 1 | **no** |

Qué cambiaría para cumplir todo:

1. **Fuente prohibida (support-25).** `internal-notice-gym.md` tiene `doc_type: notice` en el manifest. Propuesta: no indexar los documentos `notice` en `ingest build`, porque un aviso interno no es conocimiento para clientes. Así la pregunta del gimnasio queda sin contexto y sale `out_of_scope`. Es una regla del dominio y la decide el equipo.
2. **Hechos con poco margen.** La mayoría de los NO son paráfrasis correctas. Hay dos caminos: pedir en el prompt que copie los datos clave tal como aparecen en el fragmento (plazos, montos, canales), o que el golden set acepte variantes. Prefiero el prompt, porque al cliente le sirve el dato literal del documento.
3. **Intención en preguntas "cómo".** Agregar al prompt de `support` que preguntar *cómo* se actualiza un dato es `product_question`, y solo pedir el cambio es `sensitive_action`. Esto corrige support-08 y support-09, y es clave para el tema 3, donde `sensitive_action` exige aprobación humana.
4. **Chunker para el Gate T2.** Un chunk por pregunta en las FAQ, para corregir el anidamiento por el salto de `#` a `###` que vi en la sesión 3. En recall no se nota (ya está en 1.00), pero deja limpias las secciones que se citan.
