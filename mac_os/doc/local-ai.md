# IA local: coste, licencias y gestión

No hace falta un LLM ni Ollama. Se evalúan modelos especializados. «Gratis» significa que una licencia permite el uso previsto sin coste por inferencia, no ausencia de consumo de CPU, batería, almacenamiento o mantenimiento. Revisar licencia de código y pesos por cada versión antes de redistribuir; no hay una aprobación general de todos los modelos.

| Candidato              | Uso                                      | Decisión inicial                                                                                                                          |
| ---------------------- | ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| RNNoise                | Reducción de ruido                       | Primer motor a probar por integración nativa; no identifica al propietario de la voz.                                                     |
| DeepFilterNet          | Reducción de ruido alternativa           | Comparación posterior de calidad/latencia; no añadir ambos al instalador sin necesidad.                                                   |
| nomo-pvad + ERes2NetV2 | Probabilidad de voz objetivo por bloques | Experimental; requiere evaluar entorno Python/PyTorch aislado o conversión viable a runtime nativo. No asumir conversión ONNX automática. |

[nomo-pvad](https://github.com/tuya/nomo-pvad) declara Apache-2.0 para código y atribuciones de sus pesos, modelo principal de aproximadamente 35 MB, descarga adicional para el registro y bloques de 160 ms. Detecta presencia del hablante, no entrega una separación limpia de dos voces superpuestas. Esa granularidad ya impone latencia antes de sumar buffers e inferencia.

[RNNoise](https://github.com/xiph/rnnoise) y [DeepFilterNet](https://github.com/Rikorose/DeepFilterNet) mantienen sus propias licencias y artefactos. Fijar commit, hash, licencia y modelo elegido en un manifiesto al terminar el spike, no usar enlaces a ramas móviles.

## Distribución y arranque

El instalador completo llevará UI, servicio y los pesos seleccionados con redistribución aprobada. El gestor manejará actualizaciones y componentes opcionales con confirmación y tamaño verificado. Si un peso requiere descarga inicial, se declarará antes de distribuir y la función no se anunciará disponible offline desde el instalador. No exigir Python global, compiladores ni gestores de desarrollo al usuario final. Si se necesita Python, empaquetar un runtime privado con dependencias fijadas; medir el aumento de tamaño.

Los modelos se guardan por usuario y versión bajo Application Support, no en Git ni en la DB. El manifiesto registra SHA-256, origen permitido, formato, tamaño máximo, runtime compatible, licencia y dependencias. Las descargas van a staging y no ejecutan scripts arbitrarios. Activar una versión solo tras verificar integridad y carga. La eliminación de un modelo usado requiere detener la sesión de manera explícita.

Al abrir la app arranca el servicio, pero los pesos se cargan cuando se necesita el motor. Al salir, el proceso y su memoria se liberan. Inferencia y registro locales no transmiten voz. Solo la instalación inicial o actualización explícita de modelos usa red. Probar todo desconectado después de instalar.

## Dispositivo virtual

[BlackHole](https://github.com/ExistentialAudio/BlackHole) es un candidato compatible con Apple Silicon e Intel. Para el prototipo se instala de forma separada; no se redistribuye ni renombra automáticamente dentro del producto. Su proyecto exige resolver GPLv3 o licencia alternativa para integraciones no GPLv3. Decidir distribución antes de beta externa. El coste/licencia del driver es independiente del de las IA.

## Prueba que decide viabilidad

Comparar ruido de ventilador/teclado, español hablado, otras voces por turnos y solapadas, distancias y micrófonos distintos. Registrar hashes, equipo, configuración, retraso añadido p50/p95, CPU/RAM y ejemplos consentidos. Rechazo falso y aceptación falsa son errores distintos. No etiquetar el producto como «solo mi voz» basándose en una demo del autor.

## Catálogo de URLs oficiales

Estos enlaces permiten investigar e implementar. Son referencias, no URLs inmutables de descarga para el instalador. La release fijará archivos concretos y hashes en el catálogo de distribución.

| Motor/componente        | Código y documentación                                                                                                                                              | Modelo/licencia                                                                                                                    |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| RNNoise                 | [Repositorio y compilación](https://github.com/xiph/rnnoise), [página del proyecto](https://jmvalin.ca/demo/rnnoise/)                                               | [Licencia](https://github.com/xiph/rnnoise/blob/main/COPYING); fijar los pesos compatibles con el commit seleccionado.             |
| DeepFilterNet           | [Repositorio y uso](https://github.com/Rikorose/DeepFilterNet), [releases](https://github.com/Rikorose/DeepFilterNet/releases)                                      | [Modelos oficiales](https://github.com/Rikorose/DeepFilterNet/tree/main/models); revisar las licencias de la release seleccionada. |
| nomo-pvad               | [Inferencia, registro y API](https://github.com/tuya/nomo-pvad), [reporte técnico](https://tuya.com/model/doc/pvad)                                                 | [Pesos](https://github.com/tuya/nomo-pvad/tree/master/weights), [licencia](https://github.com/tuya/nomo-pvad/blob/master/LICENSE). |
| ERes2NetV2              | [3D-Speaker](https://github.com/modelscope/3D-Speaker), [documentación de ERes2NetV2](https://github.com/modelscope/3D-Speaker/tree/main/egs/cnceleb/sv-eres2netv2) | [Modelo upstream en ModelScope](https://modelscope.cn/models/iic/speech_eres2netv2_sv_zh-cn_16k-common).                           |
| PyTorch, si se necesita | [Documentación](https://docs.pytorch.org/docs/stable/index.html)                                                                                                    | Runtime privado candidato; no instalarlo globalmente al usuario.                                                                   |

La integración concreta por módulo y el flujo de build/instalación están en [installation.md](installation.md). La edición Local debe funcionar sin servicios de inferencia externos después de instalar los componentes elegidos. La edición Cloud tendrá un agente de audio local, pero los modelos se ejecutarán en servidores detrás del BFF.
