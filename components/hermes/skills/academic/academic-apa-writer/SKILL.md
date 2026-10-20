---
name: academic-apa-writer
description: Ejecuta de forma autónoma investigaciones y trabajos completos en APA 7, con fuentes verificadas y archivos finales.
version: 1.3.0
author: Hermes Academic Writer
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [academic, apa7, research, rag, docx]
    category: academic
    related_skills: [humanize-global, grounded-citations, docx, pdf]
    config:
      - key: academic_writer.language
        description: Idioma predeterminado de los trabajos
        default: es
      - key: academic_writer.writing_samples_dir
        description: Carpeta de muestras de escritura
        default: "academic/writing_samples"
      - key: academic_writer.output_dir
        description: Carpeta de salidas académicas
        default: "academic/output"
      - key: academic_writer.local_first
        description: Consultar documentos locales antes de la web
        default: true
      - key: academic_writer.web_fallback
        description: Permitir web solo para vacíos documentales
        default: true
      - key: academic_writer.validate_sources
        description: Exigir ledger y validación de fuentes
        default: true
      - key: academic_writer.humanize
        description: Aplicar humanize-global antes de validar hechos
        default: true
      - key: academic_writer.autonomous_mode
        description: Completar la tarea con valores predeterminados cuando la intención sea suficiente
        default: true
      - key: academic_writer.default_word_count
        description: Extensión aproximada cuando el usuario no indique otra
        default: 1500
      - key: academic_writer.default_export
        description: Formatos finales cuando el usuario no indique otros
        default: "docx+md"
      - key: academic_writer.auto_style_samples
        description: Usar automáticamente muestras de escritura disponibles
        default: true
      - key: academic_writer.format_profile
        description: Perfil institucional de formato predeterminado
        default: "unicaribe"
---

# Academic APA writer skill

Produce trabajos académicos completos y sustentados, con prioridad documental local y formato APA 7. Una orden breve pero accionable debe terminar en investigación, redacción, validación y archivos finales, no en una explicación del proceso. No inventa fuentes ni datos bibliográficos. La guía institucional o del profesor tiene prioridad sobre APA cuando contradice una regla general.

## When to use

Úsala para tarea, ensayo, investigación, informe académico, marco teórico, actividad universitaria, citas, bibliografía, APA o exportación académica a Word. También se invoca con `/academic-apa-writer` o mediante `/academico`.

## Prerequisites

- Coloca documentos en la carpeta configurada `academic/sources`.
- Usa `read_file` para inspecciones puntuales y `terminal` para los scripts de esta skill.
- Usa `web_search` y `web_extract` solo después de demostrar un vacío local.
- Para DOCX complejos, carga también las skills `docx` y `pdf` incluidas en el bundle `/academico`.

## How to run

Respeta este orden sin adelantar la web ni el formato:

```text
UNDERSTAND -> LOCAL_RESEARCH -> GAP_ANALYSIS -> WEB_RESEARCH -> SOURCE_LEDGER
-> OUTLINE -> DRAFT -> CITATIONS -> HUMANIZE -> FACT_VALIDATION
-> APA_FORMAT -> QUALITY_CONTROL -> EXPORT
```

## Quick reference

- Regla absoluta: NO SOURCE -> NO CITATION.
- Prioridad: usuario -> profesor -> institución -> APA 7 -> valores predeterminados.
- Una puntuación local alta es mejor; el buscador devuelve `score_direction: higher_is_better`.
- Si `MISSING` está vacío, no llames herramientas web.
- Si hay contradicción, conserva las fuentes de ambas afirmaciones y explica la diferencia relevante.
- En modo autónomo, entrega DOCX, Markdown y `.sources.json`; una instrucción explícita del usuario sustituye estos formatos.
- No detengas una tarea clara solo porque falten preferencias opcionales. Aplica los valores predeterminados y decláralos brevemente al entregar.
- No prometas ni optimices para evadir detectores de IA. Optimiza para claridad, naturalidad, trazabilidad y fidelidad a la voz disponible.
- El perfil predeterminado es UNICARIBE. Usa `references/UNICARIBE_FORMAT_PROFILE.md` para sus reglas institucionales confirmadas y la guía APA completa para todo lo demás.

## Autonomous completion contract

Si el usuario proporciona una acción y un tema comprensibles —por ejemplo, `investiga la deserción universitaria` o `hazme un ensayo sobre energía solar`— ejecuta el flujo completo sin exigir un prompt más elaborado.

Cuando el usuario no especifique otra cosa, usa:

- español;
- nivel universitario;
- informe académico con introducción, desarrollo, conclusión y referencias;
- aproximadamente 1,500 palabras, ajustables según la evidencia disponible;
- documentos locales primero y web únicamente para vacíos;
- citas y referencias según la guía APA integrada;
- `final.md`, `final.docx` y `final.sources.json` en la carpeta de salida configurada.

No inventes nombre, matrícula, profesor, institución, asignatura o fecha de entrega. Omite esos datos o deja campos editables claramente identificados cuando sean indispensables para una portada. Pregunta únicamente cuando la ambigüedad cambie materialmente el tema, exista una contradicción imposible de resolver o falte una autorización necesaria. La ausencia de longitud, apartados o formato no es por sí sola motivo para detenerse.

## Procedure

### 1. UNDERSTAND

Extrae pregunta, documento esperado, extensión, nivel, instrucciones, archivos, fecha, formato, fuentes mínimas y apartados. Aplica el contrato autónomo a preferencias omitidas y conserva cualquier instrucción explícita del usuario. No inventes datos personales ni requisitos institucionales.

En actividades de autoevaluación, distingue el instrumento de las respuestas personales: encontrar un cuestionario vacío no permite inferir resultados del estudiante. Si pide completar una tarea personal sin aportar respuestas, explica antes de generar archivos que necesitas sus respuestas reales; no interpretes «complétalo tú» como autorización para producir una entrega simulada. Crea un modelo ficticio solo cuando el usuario acepte expresamente un ejemplo, identifícalo como simulado tanto en el archivo como al entregar y redacta su interpretación en términos condicionales. No repitas una entrevista si pidió expresamente ese modelo. Conserva la extensión indicada por el profesor —por ejemplo, dos párrafos— en lugar de imponer el informe de 1,500 palabras.

Para completar cuestionarios con el estudiante, sigue esta secuencia:

1. Extrae los enunciados y la escala del instrumento local; presenta por defecto cinco preguntas por bloque, con numeración original y un recordatorio breve de la escala. Separa las aclaraciones en lenguaje sencillo del enunciado original para no alterar lo que se está respondiendo.
2. Registra cada bloque confirmado en un JSON de trabajo separado de los ejemplos, agrupado por instrumento, con identificador y respuesta literal. Antes de aplicar un bloque, conserva las respuestas anteriores y comprueba que los nuevos identificadores pertenecen al instrumento y bloque visibles; trata un cambio de respuesta ya registrada como corrección explícita, no como una entrada nueva. Verifica que el bloque guardado coincida con el mensaje y que no haya alterado respuestas anteriores, porque una sustitución textual en registros de varios instrumentos puede afectar el cuestionario equivocado. Valida la escala y no rellenes omisiones: si falta un ítem, pregunta solo por ese ítem antes de avanzar.
3. Resuelve identificadores ambiguos con una única confirmación concreta, por ejemplo «¿Confirmas que esa respuesta corresponde a la pregunta 6?». No ofrezcas dos alternativas seguidas de una pregunta respondible con «sí», porque ese sí no distingue las opciones. Conserva el valor anterior hasta aclarar cualquier corrección.
4. Antes de pasar al siguiente instrumento, comprueba cobertura completa, calcula los puntajes con código y presenta los totales como resultados de ese cuestionario, no como diagnóstico. Reinicia la numeración visible cuando el instrumento siguiente empiece en 1, manteniendo separados ambos registros.
5. Tras completar todos los instrumentos, muestra los resultados y el texto de la reflexión para revisión del estudiante antes de crear los documentos de entrega. No interrumpas la recogida de respuestas para fabricar archivos finales incompletos.

Si el usuario quiere Word para convertirlo por su cuenta a PDF, entrega DOCX y no generes PDF. Cuando la consigna exija una reflexión y anexos separados con nombres distintos, conserva esa separación en los archivos Word para facilitar su conversión y entrega.

### 2. LOCAL_RESEARCH

Ejecuta una consulta por cada subpregunta:

```text
"${HERMES_HOME}/academic/.venv/bin/python" ${HERMES_SKILL_DIR}/scripts/local_research.py search "consulta" --json
```

Los resultados tienen `text`, `source`, `page`, `score` y `source_id`. Lee los fragmentos completos necesarios. No interpretes la existencia de resultados como suficiencia.

### 3. GAP_ANALYSIS

Registra internamente `KNOWN`, `MISSING` y `UNCERTAIN`. Evalúa relevancia, cobertura, contexto, confiabilidad y relación directa. La salida del buscador incluye cobertura de términos como ayuda, no como decisión final.

### 4. WEB_RESEARCH

Solo para `MISSING`, usa consultas específicas con `web_search`. Prioriza fuentes oficiales, universidades, revistas, organismos, artículos y editoriales. Abre cada fuente con `web_extract` para verificar autor o institución, título, fecha y URL o DOI. Wikipedia sirve para orientación, no como referencia final.

### 5. SOURCE_LEDGER

Crea el ledger antes del borrador:

```text
"${HERMES_HOME}/academic/.venv/bin/python" ${HERMES_SKILL_DIR}/scripts/source_ledger.py init sources.json
"${HERMES_HOME}/academic/.venv/bin/python" ${HERMES_SKILL_DIR}/scripts/source_ledger.py add sources.json --type local --title "..." --locator "..." --supports "..."
```

Cada afirmación importante debe apuntar a una fuente real. No completes campos ausentes por intuición.

### 6. STYLE SAMPLE, OUTLINE, DRAFT, CITATIONS

Antes del esquema, inspecciona `academic/writing_samples`. Si contiene muestras legibles, selecciona hasta tres que se parezcan al entregable y extrae únicamente rasgos de estilo: registro, longitud y ritmo de oraciones, forma de los párrafos, uso de primera o tercera persona, conectores y organización. No reutilices sus hechos, argumentos, citas ni frases distintivas. Si no hay muestras, continúa sin detenerte.

Primero escribe `draft.md`. Inserta citas solo para fuentes presentes en el ledger. Mantén separadas paráfrasis y citas textuales; incluye página o párrafo cuando corresponda.

### 7. HUMANIZE

Aplica `humanize-global` a prosa no protegida. No alteres citas, referencias, autores, años, DOI, URLs, nombres, cifras o fechas.

### 8. FACT_VALIDATION

Para cuestionarios, extrae todos los enunciados del instrumento original y verifica programáticamente que los identificadores sean consecutivos, únicos y completos. Si la clave de corrección usa símbolos, colores o formas que no aparecen en la extracción textual, renderiza las páginas pertinentes e inspecciónalas antes de agrupar las respuestas; no reconstruyas la clave por el significado aparente de cada enunciado. Conserva las asignaciones impresas y documenta las discrepancias sin corregirlas silenciosamente. Calcula los puntajes con código, comprueba cobertura y ausencia de duplicados en las claves, y vuelve a leer las tablas DOCX para cotejar cada identificador, enunciado y respuesta. Si el instrumento pide una gráfica, inclúyela con texto alternativo y verifica que coincida con los totales. No conviertas puntuaciones brutas en niveles o percentiles sin un baremo aportado.

Compara `draft.md` y `humanized.md`, y ejecuta:

```text
"${HERMES_HOME}/academic/.venv/bin/python" ${HERMES_SKILL_DIR}/scripts/validate_sources.py --ledger sources.json --document humanized.md --original draft.md
"${HERMES_HOME}/academic/.venv/bin/python" ${HERMES_SKILL_DIR}/scripts/validate_citations.py humanized.md
```

### 9. APA_FORMAT, QUALITY_CONTROL, EXPORT

Cuando el perfil configurado sea `unicaribe`, consulta primero `references/UNICARIBE_FORMAT_PROFILE.md` y verifica la regla en `references/Normas-APA-7ma-Edicion-UNICARIBE.pdf` o su extracción completa `.txt`. Para reglas que la guía rápida no cubre, usa el PDF íntegro `references/Guia-Normas-APA-7ma-edicion.pdf`: consulta primero su extracción completa `references/Guia-Normas-APA-7ma-edicion.txt` y abre las páginas correspondientes. `references/apa7_reference.txt` es únicamente un índice con páginas; nunca sustituye la lectura de las fuentes completas ni autoriza completar reglas ausentes.

La propia guía declara que es un resumen no oficial, recomienda APA Style y advierte sobre adaptaciones universitarias. No ocultes esa procedencia. Si el profesor o la institución aporta una excepción explícita, compárala con la guía y aplícala según la prioridad ya indicada.

Ejecuta `final_academic_check.py`. Si creas un DOCX académico mediante python-docx en vez del generador, inicialízalo con `Document(ruta_a_apa7_template.docx)`, no con `Document()` vacío: el validador exige estilos institucionales adicionales, como `References` con sangría francesa. Conserva un solo campo ` PAGE ` en el encabezado de cada sección; reutiliza el existente o limpia el párrafo antes de insertar el reemplazo para evitar numeración duplicada. Valida cada documento separado, no solo la reflexión principal. El éxito de los validadores confirma estructura y formato, pero no convierte respuestas simuladas en resultados personales confirmados.

Para Word:

```text
"${HERMES_HOME}/academic/.venv/bin/python" ${HERMES_SKILL_DIR}/scripts/generate_docx.py final.md final.docx --template ${HERMES_SKILL_DIR}/templates/apa7_template.docx
"${HERMES_HOME}/academic/.venv/bin/python" ${HERMES_SKILL_DIR}/scripts/validate_apa.py final.docx
```

Guarda salidas en la carpeta configurada. Sanitiza el nombre y genera un `.sources.json` junto al documento cuando haya fuentes. En modo autónomo, no declares la tarea terminada hasta que existan los archivos solicitados o predeterminados y hayan pasado las comprobaciones aplicables. Si una comprobación falla, corrige y vuelve a ejecutarla; si no puede resolverse con la evidencia disponible, entrega el archivo como borrador identificado y explica el bloqueo concreto.

## Pitfalls

- Mantén los ejemplos simulados en una carpeta y con nombres distintos de los documentos de entrega, porque compartir ubicación y nombres facilita envíos accidentales. No retires la identificación de una simulación para presentarla como autoevaluación real. Al generar la versión basada en respuestas confirmadas, usa exclusivamente el registro real y comprueba texto, tablas y encabezados para eliminar restos del ejemplo: advertencias de simulación, puntajes anteriores, expresiones condicionales ya innecesarias y notas operativas del asistente. Mantén las aclaraciones de proceso en la conversación o en un archivo de control, no dentro de una entrega personal ya validada, salvo que la consigna exija declarar la asistencia utilizada.
- No uses web para repetir información local suficiente.
- No cites un resultado de búsqueda sin abrir y verificar la fuente.
- No ocultes que una sección necesitó fuentes externas.
- Si una tabla didáctica tiene filas duplicadas, incompletas o funciones asignadas a otra categoría, revisa la imagen del PDF y contrasta el artículo citado por el propio recurso. Conserva todas las categorías del material asignado, distingue los complementos y documenta las discrepancias sin inventar contenido faltante.
- No utilices los campos Author o CreationDate del PDF como autoría o fecha de publicación confirmadas cuando no consten en el documento.
- Si el usuario pide Word y excluye PDF, conserva los requisitos institucionales de contenido y pie de página, pero no generes un PDF de salida ni para revisión visual. Verifica el DOCX y no afirmes una paginación que no hayas renderizado.
- No atribuyas una afirmación web a un documento local.
- Para cuestionarios de autoevaluación, recoge las respuestas reales por bloques y persístelas en JSON; valida numeración, faltantes y símbolos antes de calcular. No uses respuestas inventadas para producir una entrega personal ni interpretes «termina» como autorización para rellenar ítems omitidos.
- Si se pasa de ejemplos a respuestas personales confirmadas, genera la entrega en una carpeta claramente separada. Compara cada celda del Word con el registro, recalcula todas las sumas y elimina únicamente las advertencias de simulación que ya no correspondan; conserva los enunciados aunque incluyan palabras como «borradores».
- Inspecciona visualmente las claves de corrección expresadas mediante símbolos: la extracción de texto puede omitirlas. Conserva las asignaciones del recurso entregado y documenta cualquier discrepancia sin corregirla por intuición.
- No declares "FINAL" si falla una comprobación crítica.
- Para mapas conceptuales, entrega un diagrama real con nodos, flechas y palabras de enlace; no lo sustituyas por un ensayo o una tabla comparativa. Puedes usar una sección Carta horizontal y otra vertical para referencias, verificando sus dimensiones, márgenes y pies. Separa organización del aprendizaje (autónomo/colaborativo), espacio (presencial/distancia) y tiempo (sincrónico/asincrónico) para no convertir categorías combinables en sinónimos.
- Distingue las citas que aparecen dentro de un fragmento textual de la atribución del fragmento: conserva las citas internas, pero no exijas referencias de obras originales no consultadas solo por aparecer dentro de una cita en bloque. Valida la atribución externa del bloque.
- Al comparar citas con referencias, normaliza el punto final del autor institucional y las marcas de cursiva Markdown de los títulos sin autor; no confundas esa puntuación editorial con una identidad bibliográfica diferente. Acepta fechas completas de referencias de videos y páginas (año, día y mes), conservando el año para emparejar la cita.
- En Linux usa `${HERMES_HOME}/academic/.venv/bin/python`; este entorno contiene python-docx, pypdf y ruamel.yaml. En Windows, la ruta equivalente es academic/.venv/Scripts/python.exe. Para tareas de foro, ajusta la extensión al género y no inventes intervenciones de compañeros ausentes.

## Verification

Antes de entregar, confirma: tarea respondida, búsqueda local ejecutada, web justificada, ledger completo, citas y referencias alineadas, piezas protegidas intactas, regla de formato localizada en la guía entregada, APA validado y archivo legible. Si falta evidencia o la guía no cubre el caso, indícalo en lugar de rellenar el vacío.

La respuesta final al usuario debe ser breve: indica qué se creó, dónde se guardó, qué fuentes se usaron y cualquier limitación real. No devuelvas solamente instrucciones que el propio agente podía ejecutar.

## Carpetas compartidas en este equipo

- Archivos aportados: `@HOST_HOME@/Documents/Universidad/entradas`.
- Entregables finales: `@HOST_HOME@/Documents/Universidad/salidas`.
- Muestras de escritura: `@HOST_HOME@/Documents/Universidad/muestras`.
- Las tres carpetas son compartidas entre el host y dev. Usa estas rutas al recibir y entregar documentos.
