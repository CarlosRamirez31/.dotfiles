#!/usr/bin/env bash
set -euo pipefail
profile=$1 mode=$2
source_root=$HOME/.local/libexec/workbench-source
if [[ $profile == dev ]]; then
    # Old launchers key on CONTAINER_ID=dev; HOME now points to an internal home.
    if [[ $mode == fresh ]]; then
        for component in docker dbeaver rider flutter hermes; do
            bash "$source_root/setup/modules/$component/setup-container.sh" \
                "$source_root"
        done
    fi
    python3 "$source_root/environments/workbench/podman/share_documents.py"
    python3 "$source_root/environments/workbench/podman/adapt_presentation.py"
else
    python3 "$source_root/environments/workbench/podman/configure_security.py"
    # Security environments use the editor, not the mobile/.NET development stack.
    python3 - <<'PY'
import json
from pathlib import Path
path = Path.home() / '.config/nvim/lazyvim.json'
if path.exists():
    data = json.loads(path.read_text())
    data['extras'] = [item for item in data.get('extras', [])
                      if item not in ('lazyvim.plugins.extras.lang.dart', 'lazyvim.plugins.extras.lang.dotnet', 'lazyvim.plugins.extras.lang.rust')]
    path.write_text(json.dumps(data, indent=2) + '\n')
flutter = Path.home() / '.config/nvim/lua/plugins/flutter.lua'
if flutter.exists():
    flutter.write_text('return {}\n')
lazy = Path.home() / '.config/nvim/lua/config/lazy.lua'
if lazy.exists():
    lazy.write_text(''.join(line for line in lazy.read_text().splitlines(keepends=True)
                            if 'lazyvim.plugins.extras.lang.rust' not in line))
PY
fi
# Copies are internal; none of these updates can write to shared Neovim data.
if ! tree-sitter --version | grep -Eq '^tree-sitter (0\.(2[5-9]|[3-9][0-9])\.|[1-9])'; then
    npm install --global --prefix "$HOME/.local" tree-sitter-cli@0.27.1
    hash -r
fi
if ! command -v yazi >/dev/null; then
    case $(uname -m) in
        x86_64)
            yazi_target=x86_64-unknown-linux-gnu
            yazi_digest=a02fe91d3304294048c681f010f1100856872a4e98ecf6927328e888d40a6ad2
            ;;
        aarch64)
            yazi_target=aarch64-unknown-linux-gnu
            yazi_digest=02807f08d6b589b65b7516a4e259d83f5995d7a23bb12b3a155141385b370b3a
            ;;
        *)
            printf 'Arquitectura de Yazi no compatible.\n' >&2
            exit 1
            ;;
    esac
    yazi_stage=$(mktemp -d)
    curl --fail --location --retry 3 --connect-timeout 20 \
        "https://github.com/sxyazi/yazi/releases/download/v26.9.1/yazi-$yazi_target.zip" \
        -o "$yazi_stage/yazi.zip"
    printf '%s  %s\n' "$yazi_digest" "$yazi_stage/yazi.zip" | sha256sum -c -
    unzip -q "$yazi_stage/yazi.zip" -d "$yazi_stage"
    install -Dm755 "$yazi_stage/yazi-$yazi_target/yazi" "$HOME/.local/bin/yazi"
    install -Dm755 "$yazi_stage/yazi-$yazi_target/ya" "$HOME/.local/bin/ya"
    rm -rf -- "$yazi_stage"
fi
if ! nvim -u NONE -i NONE -n --headless '+lua if vim.fn.has("nvim-0.11") ~= 1 then vim.cmd("cquit 1") end' +qa; then
    # Parrot Echo currently ships 0.10.4. Use the official pinned release,
    # with the SHA-256 from GitHub's release asset metadata; never mix apt repos.
    version=0.12.6
    case $(uname -m) in
        x86_64)
            arch=x86_64
            digest=474430d53e6264f6d6dd18db42d6dc9df3a1b56ca9e88a325bbf860e1a811d87
            ;;
        aarch64)
            arch=arm64
            digest=8f1f64a0bdb97247034038c3823c6cbad5bdf9ecd5751b85494b71c3ee04c815
            ;;
        *)
            printf 'Arquitectura de Neovim no compatible.\n' >&2
            exit 1
            ;;
    esac
    stage=$(mktemp -d)
    trap 'rm -rf -- "$stage"' EXIT
    curl --fail --location --retry 3 --connect-timeout 20 \
        "https://github.com/neovim/neovim/releases/download/v$version/nvim-linux-$arch.tar.gz" \
        -o "$stage/nvim.tar.gz"
    printf '%s  %s\n' "$digest" "$stage/nvim.tar.gz" | sha256sum -c -
    sudo install -d "/opt/neovim/$version"
    sudo tar -xzf "$stage/nvim.tar.gz" --strip-components=1 -C "/opt/neovim/$version"
    sudo ln -sfn "/opt/neovim/$version/bin/nvim" /usr/local/bin/nvim
    hash -r
fi
nvim -u NONE -i NONE -n --headless '+lua if vim.fn.has("nvim-0.11") ~= 1 then vim.api.nvim_err_writeln("Neovim >= 0.11 requerido"); vim.cmd("cquit 1") end' +qa
setup_log=${XDG_STATE_HOME:-$HOME/.local/state}/podman-workbench/nvim-setup.log
mkdir -p -- "$(dirname -- "$setup_log")"
run_nvim() {
    if ! nvim "$@" >>"$setup_log" 2>&1; then
        tail -n 60 -- "$setup_log" >&2
        return 1
    fi
}
if [[ $profile == dev && $mode == copy ]]; then
    snapshot_lock=$HOME/.dotfiles/config/nvim/lazy-lock.json
    if [[ -r $snapshot_lock && ! $snapshot_lock -ef $HOME/.config/nvim/lazy-lock.json ]]; then
        cp -- "$snapshot_lock" "$HOME/.config/nvim/lazy-lock.json"
    fi
    run_nvim --headless '+Lazy! restore' +qa
else
    run_nvim --headless '+Lazy! sync' +qa
fi
run_nvim --headless '+lua local ok,err=pcall(function() require("config.treesitter").install() end); if not ok then vim.api.nvim_err_writeln(tostring(err)); vim.cmd("cquit 1") end' +qa
run_nvim --headless '+lua require("lazy").load({plugins={"mason.nvim"}}); local r=require("mason-registry"); local wanted=LazyVim.opts("mason.nvim").ensure_installed or {}; for _,name in ipairs(wanted) do local p=r.get_package(name); if not p:is_installed() and not p:is_installing() then p:install() end end; vim.wait(1000,function() return false end,100); local done=vim.wait(300000,function() for _,p in ipairs(r.get_all_packages()) do if p:is_installing() then return false end end return true end,100); for _,name in ipairs(wanted) do if not r.get_package(name):is_installed() then done=false end end; if not done then vim.api.nvim_err_writeln("Faltan herramientas de Mason; revisa :Mason"); vim.cmd("cquit 1") end' +qa
DOTFILES_FASTFETCH=0 zsh -lic 'exit'
printf 'Neovim preparado; registro interno: %s\n' "$setup_log"
