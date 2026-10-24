---
name: anti-overengineering
description: Keep implementation proportional to the requested feature. Use when choosing between a direct change and new abstractions, dependencies, layers, or refactors.
---

# Solución proporcional

- Reutiliza el patrón y stack existentes. Prefiere una función o componente directo si resuelve la necesidad actual; añade una abstracción cuando haya responsabilidades distintas o repetición real que lo justifique.
- No conviertas una corrección en una migración, framework, microservicio, sistema de plugins o refactor general. No añadas paquetes por comodidad si las capacidades disponibles bastan.
- Mantén validación, errores y seguridad necesarios; menos código no justifica una solución frágil. Separa lógica y UI cuando aporta claridad, sin exigir una carpeta por cada capa.
- Decide según el uso real y los requisitos explícitos. No diseñes capacidades futuras hipotéticas. Para una tarea sencilla ejecuta directamente; para una dependencia compleja explica brevemente el motivo y acota el trabajo.
