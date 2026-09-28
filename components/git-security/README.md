# Git security

Define comportamientos seguros y portables: rama inicial `main`, `pull` solo
fast-forward, upstream automático al primer push, limpieza de referencias
remotas, autostash al rebase y conflictos `zdiff3` más legibles.

La identidad y la llave de firma nunca se guardan en este repositorio. Se
escriben en `~/.config/git/identity`, ignorado por Git.

## Configuración

Sin firma:

```bash
dotfiles-git-identity setup "Tu Nombre" correo@example.com
```

Con firma SSH de commits y tags:

```bash
dotfiles-git-identity setup "Tu Nombre" correo@example.com ~/.ssh/id_ed25519.pub
```

Comprobación:

```bash
dotfiles-git-identity status
```

La llave indicada es la pública; la privada permanece en el agente SSH de
GNOME Keyring.
