local commands = {
    "command -v wl-clipboard-history >/dev/null && uwsm app -- wl-clipboard-history -t",
    "uwsm app -- wl-paste --type text --watch cliphist store",
    "uwsm app -- wl-paste --type image --watch cliphist store",
    "command -v xdm-app >/dev/null && uwsm app -- xdm-app",
    "uwsm app -- waybar",
    "uwsm app -- swww-daemon",
    "uwsm app -- swayosd-server",
    "uwsm app -- swaync",
    "uwsm app -- hypridle",
    "/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1",
    "hyprctl setcursor Bibata-Modern-Classic 24",
    "sleep 5; pkill xfce4-notifyd",
    "uwsm app -- nm-applet",
}

local arrpc = os.getenv("HOME") .. "/.local/scripts/arrpc"
local handle = io.open(arrpc, "r")
if handle then
    handle:close()
    table.insert(commands, arrpc)
end

hl.on("hyprland.start", function()
    for _, command in ipairs(commands) do
        hl.exec_cmd(command)
    end
end)
