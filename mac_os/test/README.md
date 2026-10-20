# Entrada central de pruebas

Esta carpeta centraliza la ejecución y las pruebas entre módulos según
[las convenciones de arquitectura](../doc/architecture-conventions.md#pruebas-por-módulo-y-entrada-central).
Cada módulo será dueño de su carpeta `test/`; aquí no se duplican sus casos.

Pendiente: trasladar las suites existentes y conectar un ejecutor central que propague los fallos de
Node, Cargo y Python. Hasta entonces, usar los comandos de [pruebas](../doc/testing.md). La existencia de
esta carpeta no acredita que la orquestación ya esté implementada.
