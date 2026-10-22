#!/usr/bin/env bash
set -uo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
failures=0

section() {
    printf '\n==> %s\n' "$1"
}

pass() {
    printf 'OK: %s\n' "$1"
}

fail() {
    printf 'ERROR: %s\n' "$1" >&2
    failures=$((failures + 1))
}

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        fail "falta el comando '$1'; ejecuta: ./install.sh quality"
        return 1
    fi
}

for command_name in shellcheck shfmt zsh jq luac lua git python3 nvim; do
    require_command "$command_name"
done
((failures == 0)) || exit 1

mapfile -d '' -t repository_files < <(
    git -C "$repo_root" ls-files -z --cached --others --exclude-standard
)

bash_files=()
zsh_files=()
json_files=()
lua_files=()

for file in "${repository_files[@]}"; do
    file="$repo_root/$file"
    [[ -f $file ]] || continue
    relative=${file#"$repo_root"/}
    first_line=''
    IFS= read -r first_line <"$file" || true

    case $first_line in
        '#!'*bash | '#!'*/sh) bash_files+=("$file") ;;
    esac

    case $relative in
        *.zsh | */.zshrc | */.zshenv | */.zprofile) zsh_files+=("$file") ;;
        *.json) json_files+=("$file") ;;
        *.lua) lua_files+=("$file") ;;
    esac
done

section 'Bash: análisis estático'
if shellcheck --external-sources --source-path="$repo_root" "${bash_files[@]}"; then
    pass "ShellCheck (${#bash_files[@]} archivos)"
else
    fail 'ShellCheck encontró problemas'
fi

section 'Bash: formato'
if shfmt --diff --indent 4 --case-indent "${bash_files[@]}"; then
    pass "shfmt (${#bash_files[@]} archivos)"
else
    fail 'shfmt encontró archivos sin el formato esperado'
fi

section 'Zsh: sintaxis'
zsh_failed=0
for file in "${zsh_files[@]}"; do
    if ! zsh -n "$file"; then
        printf 'Sintaxis Zsh inválida: %s\n' "${file#"$repo_root"/}" >&2
        zsh_failed=1
    fi
done
if ((zsh_failed == 0)); then
    pass "Zsh (${#zsh_files[@]} archivos)"
else
    fail 'Zsh encontró problemas de sintaxis'
fi

section 'JSON: sintaxis'
json_failed=0
for file in "${json_files[@]}"; do
    if ! jq empty "$file"; then
        printf 'JSON inválido: %s\n' "${file#"$repo_root"/}" >&2
        json_failed=1
    fi
done
if ((json_failed == 0)); then
    pass "JSON (${#json_files[@]} archivos)"
else
    fail 'jq encontró JSON inválido'
fi

section 'Lua: sintaxis'
lua_failed=0
for file in "${lua_files[@]}"; do
    if ! luac -p "$file"; then
        printf 'Sintaxis Lua inválida: %s\n' "${file#"$repo_root"/}" >&2
        lua_failed=1
    fi
done
if ((lua_failed == 0)); then
    pass "Lua (${#lua_files[@]} archivos)"
else
    fail 'Lua encontró problemas de sintaxis'
fi

section 'Python, TOML, JSONC, manifiesto y documentación'
if python3 -B "$repo_root/setup/validate.py"; then
    pass 'Fuentes, datos, rutas y enlaces locales válidos'
else
    fail 'Validación de fuentes o estructura fallida'
fi

section 'Pruebas funcionales sin instalación'
if python3 -B "$repo_root/tests/run.py"; then
    pass 'Pruebas Python y Lua'
else
    fail 'Hay pruebas funcionales fallidas'
fi

section 'Git: whitespace'
if git -C "$repo_root" diff --check && git -C "$repo_root" diff --cached --check; then
    pass 'Git no encontró errores de whitespace'
else
    fail 'Git encontró errores de whitespace'
fi

printf '\n'
if ((failures > 0)); then
    printf 'Validación fallida: %d grupo(s) con problemas.\n' "$failures" >&2
    exit 1
fi

printf 'Validación completa: todo está correcto.\n'
