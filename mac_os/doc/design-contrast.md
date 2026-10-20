# Verificación de contraste de la propuesta

Cálculo sobre design-tokens.json: sRGB linealizado, luminancia relativa y (Lmayor + 0.05)/(Lmenor + 0.05).
Se compara el valor completo antes de redondear la tabla a tres decimales. Colores opacos y uniformes.
Umbral de texto normal 4.5:1: [WCAG](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
Bordes/foco se comprueban con objetivo interno 3:1. Divisores son decorativos y no delimitan controles.
No verifica renderizado, tamaños, VoiceOver, estados deshabilitados ni accesibilidad completa.

| Tema  | Par                    | Contraste | Mínimo | Resultado |
| ----- | ---------------------- | --------- | ------ | --------- |
| light | text / background      | 15.464:1  | 4.5:1  | Cumple    |
| light | text / surface         | 16.463:1  | 4.5:1  | Cumple    |
| light | text / raised          | 14.634:1  | 4.5:1  | Cumple    |
| light | secondary / background | 6.410:1   | 4.5:1  | Cumple    |
| light | secondary / surface    | 6.824:1   | 4.5:1  | Cumple    |
| light | secondary / raised     | 6.066:1   | 4.5:1  | Cumple    |
| light | primary / background   | 5.976:1   | 4.5:1  | Cumple    |
| light | primary / surface      | 6.362:1   | 4.5:1  | Cumple    |
| light | primary / raised       | 5.656:1   | 4.5:1  | Cumple    |
| light | success / background   | 6.059:1   | 4.5:1  | Cumple    |
| light | success / surface      | 6.450:1   | 4.5:1  | Cumple    |
| light | success / raised       | 5.733:1   | 4.5:1  | Cumple    |
| light | warning / background   | 6.131:1   | 4.5:1  | Cumple    |
| light | warning / surface      | 6.527:1   | 4.5:1  | Cumple    |
| light | warning / raised       | 5.802:1   | 4.5:1  | Cumple    |
| light | danger / background    | 6.175:1   | 4.5:1  | Cumple    |
| light | danger / surface       | 6.574:1   | 4.5:1  | Cumple    |
| light | danger / raised        | 5.844:1   | 4.5:1  | Cumple    |
| light | onPrimary / primary    | 6.362:1   | 4.5:1  | Cumple    |
| light | border / surface       | 3.915:1   | 3:1    | Cumple    |
| light | border / raised        | 3.480:1   | 3:1    | Cumple    |
| light | focus / surface        | 6.362:1   | 3:1    | Cumple    |
| light | focus / raised         | 5.656:1   | 3:1    | Cumple    |
| dark  | text / background      | 16.617:1  | 4.5:1  | Cumple    |
| dark  | text / surface         | 14.647:1  | 4.5:1  | Cumple    |
| dark  | text / raised          | 12.229:1  | 4.5:1  | Cumple    |
| dark  | secondary / background | 9.328:1   | 4.5:1  | Cumple    |
| dark  | secondary / surface    | 8.222:1   | 4.5:1  | Cumple    |
| dark  | secondary / raised     | 6.865:1   | 4.5:1  | Cumple    |
| dark  | primary / background   | 8.526:1   | 4.5:1  | Cumple    |
| dark  | primary / surface      | 7.515:1   | 4.5:1  | Cumple    |
| dark  | primary / raised       | 6.274:1   | 4.5:1  | Cumple    |
| dark  | success / background   | 10.116:1  | 4.5:1  | Cumple    |
| dark  | success / surface      | 8.917:1   | 4.5:1  | Cumple    |
| dark  | success / raised       | 7.445:1   | 4.5:1  | Cumple    |
| dark  | warning / background   | 11.285:1  | 4.5:1  | Cumple    |
| dark  | warning / surface      | 9.947:1   | 4.5:1  | Cumple    |
| dark  | warning / raised       | 8.304:1   | 4.5:1  | Cumple    |
| dark  | danger / background    | 9.908:1   | 4.5:1  | Cumple    |
| dark  | danger / surface       | 8.733:1   | 4.5:1  | Cumple    |
| dark  | danger / raised        | 7.292:1   | 4.5:1  | Cumple    |
| dark  | onPrimary / primary    | 8.526:1   | 4.5:1  | Cumple    |
| dark  | border / surface       | 4.308:1   | 3:1    | Cumple    |
| dark  | border / raised        | 3.597:1   | 3:1    | Cumple    |
| dark  | focus / surface        | 7.515:1   | 3:1    | Cumple    |
| dark  | focus / raised         | 6.274:1   | 3:1    | Cumple    |
