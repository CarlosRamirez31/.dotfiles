$ErrorActionPreference = "Stop"

function Ensure-WingetPackage {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(Mandatory = $true)][string]$Id
    )

    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        winget install --exact --id $Id --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            throw "No se pudo instalar $Id con winget."
        }
    }
}

function Update-SessionPath {
    $MachinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$MachinePath;$UserPath"
}

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "winget es necesario para instalar las dependencias de Neovim."
}

Ensure-WingetPackage -Command "git" -Id "Git.Git"
Ensure-WingetPackage -Command "nvim" -Id "Neovim.Neovim"
Ensure-WingetPackage -Command "rg" -Id "BurntSushi.ripgrep.MSVC"
Ensure-WingetPackage -Command "fd" -Id "sharkdp.fd"
Ensure-WingetPackage -Command "cmake" -Id "Kitware.CMake"
Ensure-WingetPackage -Command "node" -Id "OpenJS.NodeJS.LTS"
Ensure-WingetPackage -Command "dotnet" -Id "Microsoft.DotNet.SDK.10"
Ensure-WingetPackage -Command "rustup" -Id "Rustlang.Rustup"
Update-SessionPath

if (-not (Get-Command tree-sitter -ErrorAction SilentlyContinue)) {
    npm install --global tree-sitter-cli
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo instalar tree-sitter-cli con npm."
    }
    Update-SessionPath
}

if (-not (Get-Command tree-sitter -ErrorAction SilentlyContinue)) {
    throw "tree-sitter-cli se instaló, pero tree-sitter no está disponible en PATH."
}

if (Get-Command rustup -ErrorAction SilentlyContinue) {
    rustup component add rust-analyzer
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo instalar rust-analyzer con rustup."
    }
}

$Source = Join-Path $PSScriptRoot "dotfiles/.config/nvim"
$Target = Join-Path $env:LOCALAPPDATA "nvim"

if (Test-Path $Target) {
    $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $Backup = "$Target.backup.$Timestamp"
    Write-Host "Backing up $Target to $Backup"
    Move-Item -LiteralPath $Target -Destination $Backup
}

New-Item -ItemType Directory -Force -Path $Target | Out-Null
Copy-Item -Path (Join-Path $Source "*") -Destination $Target -Recurse -Force
Copy-Item -Path (Join-Path $Source ".neoconf.json") -Destination $Target -Force
Copy-Item -Path (Join-Path $Source ".gitignore") -Destination $Target -Force

& nvim --headless "+Lazy! sync" "+qa"
if ($LASTEXITCODE -ne 0) {
    throw "Falló la sincronización de plugins de Neovim."
}
& nvim --headless "+lua require('config.treesitter').install()" "+qa"
if ($LASTEXITCODE -ne 0) {
    throw "Falló la instalación de parsers de Tree-sitter."
}
Write-Host "Neovim instalado con la configuración unificada de dotfiles."
