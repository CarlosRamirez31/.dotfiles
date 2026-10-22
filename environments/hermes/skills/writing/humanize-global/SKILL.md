---
name: humanize-global
description: Revisa y adapta la redacción a una voz natural o a las muestras del usuario sin cambiar hechos, citas ni referencias.
version: 1.1.0
author: Hermes Academic Writer
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [writing, editing, spanish, humanizer]
    category: writing
    related_skills: [humanizer]
---

# Humanize global skill

Revisa la presentación lingüística de la respuesta final. No añade información, no elimina condiciones y no intenta engañar detectores. La fuente de referencia se conserva en `references/humanizer_original.md` bajo licencia MIT.

## When to use

Esta skill se carga automáticamente. Aplícala al último borrador de respuestas normales y al paso HUMANIZE de un trabajo académico.

## Prerequisites

No requiere dependencias. Para una validación determinista opcional, usa `terminal` con `scripts/validate_rewrite.py`.

## How to run

1. Termina primero el contenido y los hechos.
2. En trabajos académicos, busca muestras legibles en `academic/writing_samples`. Si existen, selecciona hasta tres comparables y crea internamente un perfil de estilo basado en rasgos observables; no copies su contenido.
3. Identifica y congela código, comandos, rutas, URLs, citas, bibliografía, DOI, números, porcentajes, fechas, nombres propios, productos, identificadores, fórmulas y texto que el usuario pidió conservar.
4. Reescribe únicamente la prosa no protegida.
5. Compara borrador y resultado. Si cambió un hecho o una pieza protegida, restaura el original.

## Quick reference

- Conserva significado, alcance, incertidumbre y tono solicitado.
- Reduce muletillas, grandilocuencia, repeticiones, encabezados innecesarios y transiciones mecánicas.
- Varía el ritmo solo cuando mejora la lectura.
- Mantén tecnicismos necesarios y el idioma de la conversación.
- Una muestra del usuario tiene prioridad sobre reglas generales de estilo.
- Sin muestras, usa variación natural compatible con el género y el nivel solicitados; no agregues informalidad artificial.

## Procedure

1. Marca patrones artificiales en conjunto; una palabra aislada no prueba nada. Revisa especialmente aperturas repetidas, párrafos con la misma forma, enumeraciones innecesarias, conclusiones obvias y conectores usados de manera mecánica.
2. Si hay muestras, reproduce tendencias generales de registro, ritmo, persona gramatical, densidad y organización. No copies frases distintivas ni errores de las muestras.
3. Redacta un primer pase natural con verbos directos y detalles ya presentes.
4. Haz un segundo pase preguntando internamente: "¿Qué todavía suena mecánico?", "¿Este párrafo cumple una función concreta?" y "¿Cambió algún hecho, nombre, número, fecha, cita o referencia?".
5. Corrige el párrafo completo cuando un reemplazo local deje una frase forzada.
6. Devuelve únicamente la versión final cuando otra skill invoque esta en modo embebido.

## Pitfalls

- No simplifiques términos académicos o técnicos solo por ser formales.
- No elimines reservas reales, limitaciones, contradicciones ni advertencias.
- No inventes experiencias personales, opiniones, autores o contexto.
- No alteres citas textuales ni referencias para que "suenen mejor".
- No agregues errores deliberados, anécdotas falsas, opiniones atribuidas al usuario ni recursos orientados a engañar detectores.

## Verification

La revisión pasa únicamente si todo elemento protegido aparece sin cambios y no hay afirmaciones nuevas. Para archivos, ejecuta:

```text
python ${HERMES_SKILL_DIR}/scripts/validate_rewrite.py original.txt reescrito.txt
```
