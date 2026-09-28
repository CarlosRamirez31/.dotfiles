# Workbench

Instala Podman rootless y Distrobox para separar dependencias de proyectos y
herramientas de laboratorio del sistema Arch principal. No crea ni descarga
contenedores durante la instalación.

El instalador selecciona `crun` explícitamente como runtime OCI para que Pacman
no pregunte entre `crun`, `krun` y `runc`. Es una opción ligera y adecuada para
Podman rootless; `krun` solo resulta necesario cuando se busca aislamiento KVM.

Hay dos perfiles intencionales:

- `dev`: Arch limpio para compiladores o dependencias de un proyecto.
- `pentest`: Kali Rolling para herramientas de laboratorios autorizados.

## Comandos

```bash
dotfiles-box create dev
dotfiles-box enter dev
dotfiles-box create pentest
dotfiles-box enter pentest
dotfiles-box list
dotfiles-box stop pentest
dotfiles-box remove pentest
```

`remove` siempre solicita confirmación. Tus directorios personales se integran
mediante Distrobox; los paquetes instalados dentro del contenedor no ensucian
Arch.
