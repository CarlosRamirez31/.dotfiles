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

Las credenciales HTTPS se guardan en el llavero del sistema mediante
`credential.helper=libsecret`. El usuario de GitHub se introduce al autenticar o se define en la configuración
privada; es independiente del nombre del autor de los commits. La plantilla
versionada no fija nombre, correo ni usuario de GitHub. En el próximo push introduce tu token como contraseña una vez:
Git lo guardará en el llavero tras autenticar correctamente. El token no se
incluye en estos dotfiles. El llavero debe estar desbloqueado; SDDM puede
desbloquearlo al iniciar sesión si usa la misma contraseña.

```bash
./install.sh git-security
git identity setup "Tu Nombre" correo@example.com
git identity setup "Tu Nombre" correo@example.com ~/.ssh/id_ed25519.pub
git identity status
```

Git descubre `.local/bin/git-identity` como un subcomando, por eso se invoca de forma natural como `git identity`. El tercer argumento debe ser la llave **pública**. Cuando se proporciona, configura `user.signingKey` y activa firma automática de commits y tags. La privada permanece en GNOME Keyring/GCR o en otro agente SSH y nunca se copia.

`setup` reemplaza únicamente el archivo de identidad administrado, no repositorios ni llaves. Para cambiar de identidad por repositorio usa `git config user.name/email` dentro de ese repositorio; la configuración local tiene prioridad.

## Verificación y problemas

```bash
git config --show-origin --list
git config --get user.email
git config --get commit.gpgSign
ssh-add -L
git log --show-signature -1
```

Si una firma falla, confirma que `SSH_AUTH_SOCK` apunta al socket GCR, que el agente cargó la llave privada correspondiente y que la ruta configurada apunta a `.pub`. El componente instala `git` y `openssh`; el agente se configura en `security` y se exporta en `shell`.

## Fuentes del módulo

Instalador: [`setup/modules/git-security.sh`](../setup/modules/git-security.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
