local awful = require("awful")
local wibox = require("wibox")
local M = {}
function M.text_watcher(command, interval, prefix)
    local widget = wibox.widget.textbox()
    awful.widget.watch(command, interval, function(target, stdout)
        local value = stdout:gsub("%s+$", "")
        target.text = value == "" and "" or prefix .. value
    end, widget)
    return widget
end
function M.htb()
    return M.text_watcher("$HOME/.local/bin/dotfiles-htb-vpn-status 2>/dev/null", 5, "󰖂 ")
end

function M.volume()
    return M.text_watcher("wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null | awk '{printf \"%d%%\", $2 * 100}'", 3, "󰕾 ")
end

function M.network()
    return M.text_watcher("nmcli -t -f DEVICE,STATE device 2>/dev/null | awk -F: '$2 == \"connected\" {print $1; exit}'", 5, "󰤨 ")
end

function M.memory()
    return M.text_watcher("free -m | awk '/Mem:/ {printf \"%dM\", $3}'", 5, "󰍛 ")
end

function M.cpu()
    local command = [[
        read -r _ u1 n1 s1 i1 w1 q1 r1 t1 rest < /proc/stat
        total1=$((u1+n1+s1+i1+w1+q1+r1+t1)); idle1=$((i1+w1))
        sleep 0.2
        read -r _ u2 n2 s2 i2 w2 q2 r2 t2 rest < /proc/stat
        total2=$((u2+n2+s2+i2+w2+q2+r2+t2)); idle2=$((i2+w2))
        awk -v dt="$((total2-total1))" -v di="$((idle2-idle1))" \
            'BEGIN { if (dt > 0) printf "%.0f%%", 100 * (dt-di) / dt }'
    ]]
    return M.text_watcher(command, 5, "󰻠 ")
end

return M
