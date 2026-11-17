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