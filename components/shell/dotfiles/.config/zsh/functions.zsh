mkcd() {
    if (( $# != 1 )); then
        print -u2 'uso: mkcd DIRECTORIO'
        return 2
    fi
    mkdir -p -- "$1" && cd -- "$1"
}

serve() {
    local port=${1:-8000}
    local bind=${2:-127.0.0.1}
    print "Sirviendo $PWD en http://$bind:$port"
    python -m http.server "$port" --bind "$bind"
}

portinfo() {
    if (( $# != 1 )); then
        print -u2 'uso: portinfo PUERTO'
        return 2
    fi
    ss -tulpen | rg ":${1}([^0-9]|$)"
}

cheat() {
    if (( $# == 0 )); then
        print -u2 'uso: cheat COMANDO'
        return 2
    fi
    tldr "$@"
}

vpn-on() {
    if (( $# != 1 )); then
        print -u2 'uso: vpn-on RUTA_AL_ARCHIVO_OVPN'
        return 2
    fi

    local config=${1:A}
    local runtime_dir=${XDG_RUNTIME_DIR:-/run/user/$UID}
    local pidfile=$runtime_dir/dotfiles-openvpn.pid
    local logfile=$runtime_dir/dotfiles-openvpn.log

    if [[ ! -r $config ]]; then
        print -u2 "vpn-on: no se puede leer: $config"
        return 1
    fi

    if [[ -r $pidfile ]]; then
        local current_pid=$(<$pidfile)
        if [[ $current_pid == <-> ]] && sudo kill -0 "$current_pid" 2>/dev/null; then
            print -u2 "vpn-on: la VPN ya esta activa (PID $current_pid)"
            return 1
        fi
        sudo rm -f -- "$pidfile"
    fi

    sudo openvpn \
        --cd "${config:h}" \
        --config "${config:t}" \
        --daemon dotfiles-vpn \
        --writepid "$pidfile" \
        --log "$logfile" || return

    mkdir -p "${XDG_STATE_HOME:-$HOME/.local/state}/dotfiles"
    touch "${XDG_STATE_HOME:-$HOME/.local/state}/dotfiles/openvpn-managed"
    print "VPN iniciada en segundo plano. Desconecta con: vpn-off"
    print "Registro: $logfile"
}

vpn-off() {
    local runtime_dir=${XDG_RUNTIME_DIR:-/run/user/$UID}
    local pidfile=$runtime_dir/dotfiles-openvpn.pid

    if [[ ! -r $pidfile ]]; then
        print -u2 'vpn-off: no hay una VPN iniciada con vpn-on'
        return 1
    fi

    local vpn_pid=$(<$pidfile)
    if [[ $vpn_pid != <-> ]]; then
        print -u2 'vpn-off: el archivo PID no es valido'
        return 1
    fi

    mkdir -p "${XDG_STATE_HOME:-$HOME/.local/state}/dotfiles"
    touch "${XDG_STATE_HOME:-$HOME/.local/state}/dotfiles/openvpn-managed"
    if sudo kill "$vpn_pid" 2>/dev/null; then
        # SIGTERM is asynchronous; do not announce disconnection until exit.
        local attempt
        for attempt in {1..25}; do
            sudo kill -0 "$vpn_pid" 2>/dev/null || break
            sleep 0.2
        done
        if sudo kill -0 "$vpn_pid" 2>/dev/null; then
            print -u2 'vpn-off: la VPN sigue cerrándose; revisa el registro y vuelve a intentarlo'
            return 1
        fi
        sudo rm -f -- "$pidfile"
        print 'VPN desconectada'
    else
        sudo rm -f -- "$pidfile"
        print -u2 'vpn-off: el proceso ya no estaba activo'
        return 1
    fi
}
