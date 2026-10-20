local awful = require("awful")

local function once(process, command)
    local match = "-x " .. process
    awful.spawn.with_shell(
        "if ! pgrep -u \"$(id -u)\" " .. match .. " >/dev/null 2>&1; then " .. command .. " & fi"
    )
end

once("picom", "picom --config $HOME/.config/picom/picom.conf")
once("xss-lock", "xss-lock -- $HOME/.local/bin/dotfiles-lock")
-- Clipboard history capture is opt-in: clipmenud caused sustained CPU usage
-- and increased battery drain on this laptop. Start it manually when needed.

-- XSecureLock owns its display state.  A second DPMS timeout could keep the
-- monitor off after a successful unlock on some X11/VM graphics drivers.
awful.spawn.with_shell("xset s 600 60 -dpms")
-- Start in US. Switching is handled by Super+Space and the Polybar indicator.
awful.spawn.with_shell("setxkbmap -layout us,latam -option")
-- Detect hotplug as well as displays present at login. The display panel holds
-- a lock while editing, so automatic detection cannot interrupt a preview.
require("gears").timer({
    timeout = 5,
    autostart = true,
    call_now = true,
    callback = function()
        awful.spawn.easy_async({ os.getenv("HOME") .. "/.local/bin/dotfiles-display", "--auto" }, function() end)
    end,
})
awful.spawn.with_shell("$HOME/.local/bin/dotfiles-wallpaper restore")
awful.spawn.with_shell("$HOME/.local/bin/dotfiles-polybar")
awful.spawn.with_shell(
    "xrdb -merge \"$HOME/.Xresources\"; " ..
        "systemctl --user set-environment XCURSOR_THEME=Bibata-Modern-Classic " ..
        "XCURSOR_SIZE=24 XDG_SESSION_TYPE=x11 XDG_CURRENT_DESKTOP=awesome " ..
        "XDG_SESSION_DESKTOP=awesome; " ..
        "dbus-update-activation-environment --systemd DISPLAY XAUTHORITY " ..
        "XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE XCURSOR_THEME XCURSOR_SIZE; " ..
        "systemctl --user import-environment DISPLAY XAUTHORITY; " ..
        "systemctl --user start dotfiles-touchpad-typing.service"
)
