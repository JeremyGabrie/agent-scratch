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
