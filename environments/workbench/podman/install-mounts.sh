#!/usr/bin/env bash
# Managed by dotfiles: install the bounded host mount helper, never a privileged container.
set -euo pipefail
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ $EUID == 0 && $# == 1 && $1 =~ ^[a-z_][a-z0-9_-]*[$]?$ ]] || {
    echo 'Uso: sudo bash install-mounts.sh USUARIO' >&2; exit 1;
}
mount_user=$1
id "$mount_user" >/dev/null
mount_source=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
for directory in /etc/workbench-mounts /srv/workbench-mounts /usr/local/libexec; do
    [[ ! -L $directory ]] || { echo "Destino simbólico rechazado: $directory" >&2; exit 1; }
    if [[ -e $directory ]]; then
        if [[ $(stat -c %u "$directory") != 0 ]] || (( (8#$(stat -c %a "$directory") & 8#022) != 0 )); then
            echo "Directorio inseguro: $directory" >&2; exit 1;
        fi
    else
        install -d -o root -g root -m 0755 "$directory"
    fi
done
# Refuse to replace unrelated root files; keep the resource list on subsequent installs.
for file in /usr/local/libexec/workbench-mount-helper /usr/local/libexec/workbench-mount-client /usr/local/libexec/mount_policy.py /etc/sudoers.d/workbench-mounts /etc/systemd/system/workbench-mounts.service; do
    [[ ! -L $file ]] || { echo "Destino simbólico rechazado: $file" >&2; exit 1; }
    if [[ -e $file ]] && ! grep -qi 'workbench' "$file"; then
        echo "Archivo ajeno; no se sobrescribe: $file" >&2; exit 1
    fi
done
install -o root -g root -m 0755 "$mount_source/mount_helper.py" /usr/local/libexec/workbench-mount-helper
install -o root -g root -m 0755 "$mount_source/mounts.py" /usr/local/libexec/workbench-mount-client
install -o root -g root -m 0644 "$mount_source/mount_policy.py" /usr/local/libexec/mount_policy.py
if [[ ! -e /etc/workbench-mounts/fstab && ! -L /etc/workbench-mounts/fstab ]]; then
    install -o root -g root -m 0600 "$mount_source/mounts.fstab" /etc/workbench-mounts/fstab
fi
mount_sudoers=$(mktemp)
trap 'rm -f -- "$mount_sudoers"' EXIT
printf '# Managed workbench mounts: validated requests only\n%s ALL=(root) NOPASSWD: /usr/local/libexec/workbench-mount-helper list, /usr/local/libexec/workbench-mount-helper mount *, /usr/local/libexec/workbench-mount-helper unmount *, /usr/local/libexec/workbench-mount-helper request\n' "$mount_user" > "$mount_sudoers"
visudo -cf "$mount_sudoers"
install -o root -g root -m 0440 "$mount_sudoers" /etc/sudoers.d/workbench-mounts
cat > /etc/systemd/system/workbench-mounts.service <<'UNIT'
# Managed workbench mounts
[Unit]
Description=Shared subtree for bounded workbench mounts
After=local-fs.target
Before=umount.target
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/libexec/workbench-mount-helper prepare
ExecStop=/usr/local/libexec/workbench-mount-helper release
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now workbench-mounts.service
/usr/local/libexec/workbench-mount-helper prepare
