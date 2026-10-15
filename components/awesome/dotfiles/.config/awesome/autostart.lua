local awful = require("awful")

local function once(process, command, match_command_line)
    local match = match_command_line and "-f '[c]lipmenud'" or "-x " .. process
    awful.spawn.with_shell(
        "if ! pgrep -u \"$(id -u)\" " .. match .. " >/dev/null 2>&1; then " .. command .. " & fi"
    )
end

once("picom", "picom --config $HOME/.config/picom/picom.conf")
once("xss-lock", "xss-lock -- $HOME/.local/bin/dotfiles-lock")
once("clipmenud", "clipmenud", true)

awful.spawn.with_shell("xset s 600 60 +dpms dpms 660 660 660")
awful.spawn.with_shell("$HOME/.local/bin/dotfiles-wallpaper restore")
awful.spawn.with_shell(
    "xrdb -merge \"$HOME/.Xresources\"; " ..
        "systemctl --user unset-environment WAYLAND_DISPLAY HYPRLAND_INSTANCE_SIGNATURE " ..
        "UWSM_FINALIZE_VARNAMES MOZ_ENABLE_WAYLAND; " ..
        "systemctl --user set-environment XCURSOR_THEME=Bibata-Modern-Classic " ..
        "XCURSOR_SIZE=24 XDG_SESSION_TYPE=x11 XDG_CURRENT_DESKTOP=awesome " ..
        "XDG_SESSION_DESKTOP=awesome; " ..
        "dbus-update-activation-environment --systemd DISPLAY XAUTHORITY " ..
        "XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE XCURSOR_THEME XCURSOR_SIZE"
)
