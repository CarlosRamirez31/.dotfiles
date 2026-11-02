---
name: repo-scaffold
description: Create a new programming repository using the user's project location and the chosen stack's conventions. Use for a new project or repository, not for ordinary edits in an existing checkout.
---

# Repositorios del usuario

- Sin una ubicación explícita, crea proyectos en `~/Documents/Programacion/<nombre>`. Los directorios `Documents/Codex` son áreas de trabajo, no el destino predeterminado de un nuevo proyecto permanente.
- Comprueba el destino y la existencia de `.git`. No sobrescribas un proyecto ni inicialices un repositorio dentro de otro accidentalmente. En una tarea de Agent Hub conserva el worktree asignado; no te salgas del scope para crear otra copia.
- Respeta el lenguaje/framework elegido y su estructura nativa. Para una aplicación normal suelen bastar código (`src/` si el stack lo usa), pruebas de comportamiento pertinentes, `.gitignore` y un README con cómo ejecutar. Para un script pequeño bastan el script y sus instrucciones; evita carpetas vacías.
- Separa presentación, lógica y acceso a datos según las responsabilidades reales. Registra herramientas de desarrollo reproducibles; excluye secretos, builds, cachés y dependencias instaladas de Git.
- Verifica el comando mínimo de ejecución o compilación. Crear el repo local no autoriza publicar, hacer push, elegir una licencia ni subir credenciales.

- Explora antes de definir el scaffold: consulta upstream, herramientas y dependencias, permite adquisición autorizada y baseline sin registro previo. Clonar escribe archivos; verifica autorización y destino. Propón la estructura mínima con software-architect y anti-overengineering dentro del trabajo autorizado; respeta las convenciones upstream, sin capas ni documentos por rutina.

- Si el almacén externo está autorizado y es escribible, registra la carpeta nueva con `dotfiles-project-context init --project <directorio>`, sin requerir Git. No ejecutes `git init` salvo que el usuario pida explícitamente un repositorio Git. La arquitectura y notas del agente van en el almacén externo de `software-architect`, no dentro del código. No confundas un README de uso del producto con memoria del agente.

- Si no puede persistirse memoria o recibos, conserva la actualización pendiente fuera del código en una ruta autorizada e informa su ubicación (o entrega su contenido si no existe ruta externa escribible). La arquitectura ausente, draft o con decisiones pendientes solo genera un aviso: puedes continuar con la tarea o definir la arquitectura primero. Si el usuario pidió implementar, continúa con supuestos razonables sin exigir confirmación por rutina. No amplíes permisos ni fabriques arquitectura.
