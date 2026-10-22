local awful = require("awful")
local gears = require("gears")
local wibox = require("wibox")

local M = {}

local colors = {
    surface = "#242438",
    hover = "#45475a",
    text = "#cdd6f4",
    muted = "#a6adc8",
    lavender = "#b4befe",
    mauve = "#cba6f7",
    pink = "#f5c2e7",
    cyan = "#89dceb",
    red = "#f38ba8",
    yellow = "#f9e2af",
    green = "#a6e3a1",
}

function M.pill(widget, background)
    return wibox.widget({
        {
            widget,
            left = 9,
            right = 9,
            top = 5,
            bottom = 5,
            widget = wibox.container.margin,
        },
        bg = background or colors.surface,
        shape = gears.shape.rounded_rect,
        widget = wibox.container.background,
    })
end

function M.inline(widget)
    return wibox.widget({
        widget,
        left = 5,
        right = 5,
        widget = wibox.container.margin,
    })
end

function M.metric(icon, accent, command, interval, fallback)
    local text = wibox.widget.textbox()
    text.font = "JetBrainsMono Nerd Font 10"
    awful.widget.watch({ "sh", "-c", command }, interval, function(_, stdout)
        local value = stdout:gsub("%s+$", "")
        if value == "" then value = fallback or "--" end
        text.markup = string.format(
            '<span foreground="%s">%s</span><span foreground="%s"> %s</span>',
            accent,
            icon,
            colors.text,
            gears.string.xml_escape(value)
        )
    end)
    return M.inline(text)
end

function M.action(icon, accent, callback)
    local text = wibox.widget({
        markup = string.format('<span foreground="%s">%s</span>', accent, icon),
        font = "JetBrainsMono Nerd Font 11",
        align = "center",
        widget = wibox.widget.textbox,
    })
    local button = M.inline(text)
    button:buttons(gears.table.join(awful.button({}, 1, callback)))
    return button
end

function M.htb()
    local text = wibox.widget.textbox()
    text.font = "JetBrainsMono Nerd Font 10"
    local pill = M.inline(text)
    awful.widget.watch({ "sh", "-c", "$HOME/.local/bin/dotfiles-htb-vpn-status 2>/dev/null" }, 5, function(_, stdout)
        local value = stdout:gsub("%s+$", "")
        pill.visible = value ~= ""
        text.markup = string.format(
            '<span foreground="%s">󰖂</span><span foreground="%s"> %s</span>',
            colors.green,
            colors.text,
            gears.string.xml_escape(value)
        )
    end)
    return pill
end

function M.volume()
    return M.metric("󰕾", colors.red, "wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null | awk '{printf \"%d%%\", $2 * 100}'", 3)
end

function M.network()
    return M.metric("󰤨", colors.mauve, "nmcli -t -f DEVICE,STATE device 2>/dev/null | awk -F: '$2 == \"connected\" {print $1; exit}'", 5)
end

function M.memory()
    return M.metric("󰍛", colors.yellow, "free -m | awk '/Mem:/ {printf \"%dM\", $3}'", 5)
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
    return M.metric("󰻠", colors.red, command, 5)
end

function M.clock()
    local text = wibox.widget.textbox()
    text.font = "JetBrainsMono Nerd Font 10"
    local function update()
        text.markup = string.format(
            '<span foreground="%s">󰥔</span><span foreground="%s"> %s</span>',
            colors.pink,
            colors.text,
            os.date("%I:%M %p  ·  %a %d")
        )
    end
    update()
    gears.timer({ timeout = 30, autostart = true, callback = update })
    return M.inline(text)
end

M.colors = colors
return M
