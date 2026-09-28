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
