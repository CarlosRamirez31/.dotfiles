#!/usr/bin/env bash
set -euo pipefail
module_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
exec bash "$module_root/../../../environments/workbench/podman/install-component.sh" "hermes"
