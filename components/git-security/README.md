# Git security

Este componente define una política Git global portable y mantiene nombre, correo y llave fuera del repositorio. Existe para compartir comportamientos seguros sin publicar identidad personal ni rutas de llaves.

## Comportamiento configurado

| Opción | Motivo |
| --- | --- |
| Rama inicial `main` | Nombre coherente en repositorios nuevos. |
| `pull.ff=only` | Impide merges accidentales durante `git pull`. |
| Push de rama actual + upstream automático | Primer `git push` simple y explícito. |
| Prune de ramas y tags remotos | Elimina referencias obsoletas al hacer fetch. |
| Autostash en rebase | Aparta/restaura cambios locales temporalmente. |
| Diff `histogram` | Cambios de código más legibles. |
| Conflicto `zdiff3` | Muestra base común además de ambos lados. |
| Commit verbose | Enseña el diff en el editor del mensaje. |
| Formato de firma SSH | Reutiliza llaves SSH sin infraestructura GPG. |

`.config/git/config` incluye `~/.config/git/identity`. Ese archivo privado se crea con modo `0600` y está ignorado por Git.

## Identidad y firma

```bash
./install.sh git-security
dotfiles-git-identity setup "Tu Nombre" correo@example.com
dotfiles-git-identity setup "Tu Nombre" correo@example.com ~/.ssh/id_ed25519.pub
dotfiles-git-identity status
```

El tercer argumento debe ser la llave **pública**. Cuando se proporciona, configura `user.signingKey` y activa firma automática de commits y tags. La privada permanece en GNOME Keyring/GCR o en otro agente SSH y nunca se copia.

`setup` reemplaza únicamente el archivo de identidad administrado, no repositorios ni llaves. Para cambiar de identidad por repositorio usa `git config user.name/email` dentro de ese repositorio; la configuración local tiene prioridad.

## Verificación y problemas

```bash
git config --show-origin --list
git config --get user.email
git config --get commit.gpgSign
ssh-add -L
git log --show-signature -1
```

Si una firma falla, confirma que `SSH_AUTH_SOCK` apunta al socket GCR, que el agente cargó la llave privada correspondiente y que la ruta configurada apunta a `.pub`. El componente instala `git` y `openssh`; el agente se configura en `security` y se exporta en `uwsm`/`shell`.
