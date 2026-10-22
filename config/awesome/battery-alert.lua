local awful = require("awful")
local gears = require("gears")
local wibox = require("wibox")

local M = {}
local popup
local monitor
local warned = false
local preview = false

local function text(value, font, color)
    return wibox.widget({
        markup = string.format('<span foreground="%s">%s</span>', color, gears.string.xml_escape(value)),
        font = font,
        align = "center",
        valign = "center",
        forced_height = 28,
        widget = wibox.widget.textbox,
    })
end

function M.dismiss()
    if popup then popup.visible = false end
end

function M.show(capacity, is_preview)
    M.dismiss()
    preview = is_preview == true
    local icon = text("", "JetBrainsMono Nerd Font 42", "#f9e2af")
    icon.forced_height = 68
    local percentage = text(tostring(capacity) .. "%", "Lexend Bold 30", "#f9e2af")
    percentage.forced_height = 54
    local button = wibox.widget({
        text("Entendido", "Lexend Bold 11", "#181825"),
        margins = 10,
        widget = wibox.container.margin,
    })
    button = wibox.widget({ button, bg = "#cba6f7", shape = gears.shape.rounded_rect, widget = wibox.container.background })
    button:buttons(gears.table.join(awful.button({}, 1, M.dismiss)))
    button:connect_signal("mouse::enter", function(w) w.bg = "#d8bbff" end)
    button:connect_signal("mouse::leave", function(w) w.bg = "#cba6f7" end)
    local progress = wibox.widget({
        max_value = 100,
        value = capacity,
        forced_height = 5,
        color = "#f9e2af",
        background_color = "#313244",
        shape = gears.shape.rounded_rect,
        bar_shape = gears.shape.rounded_rect,
        widget = wibox.widget.progressbar,
    })
    popup = awful.popup({
        screen = awful.screen.focused(),
        ontop = true,
        visible = true,
        type = "notification",
        placement = function(window)
            awful.placement.centered(window, { parent = awful.screen.focused(), honor_workarea = false })
        end,
        bg = "#181825",
        fg = "#cdd6f4",
        border_width = 2,
        border_color = "#45475a",
        shape = function(cr, width, height) gears.shape.rounded_rect(cr, width, height, 20) end,
        minimum_width = 410,
        maximum_width = 410,
        widget = {
            {
                icon,
                text("Batería baja", "Lexend Bold 19", "#cdd6f4"),
                percentage,
                progress,
                text("Conecta el cargador para seguir trabajando.", "Lexend 10", "#a6adc8"),
                button,
                text(preview and "Vista previa · No es el nivel real de tu batería" or "Te avisamos para que no pierdas tu trabajo.", "Lexend 8", "#a6adc8"),
                spacing = 12,
                layout = wibox.layout.fixed.vertical,
            },
            margins = 28,
            widget = wibox.container.margin,
        },
    })
    awful.placement.centered(popup, { parent = awful.screen.focused(), honor_workarea = false })
    return popup
end

-- Latch until charging resumes or the battery rises above the threshold.
-- Dismissing the card must not produce another alert every thirty seconds.
function M.check_sample(capacity, status, plugged_in)
    if not capacity then return end
    if plugged_in or status == "Charging" or status == "Full" or capacity > 10 then
        warned = false
        if not preview then M.dismiss() end
    elseif status == "Discharging" and capacity <= 10 and not warned then
        warned = true
        M.show(capacity, false)
    end
end

function M.start()
    if monitor then return end
    monitor = gears.timer({
        timeout = 30,
        autostart = true,
        call_now = true,
        callback = function()
            awful.spawn.easy_async_with_shell([[
                plugged=0
                for supply in /sys/class/power_supply/*; do
                    [ -r "$supply/type" ] && [ -r "$supply/online" ] || continue
                    [ "$(cat "$supply/type")" != Battery ] || continue
                    [ "$(cat "$supply/online")" = 1 ] && plugged=1
                done
                for battery in /sys/class/power_supply/BAT*; do
                    [ -r "$battery/capacity" ] && [ -r "$battery/status" ] || continue
                    printf '%s\n%s\n%s\n' "$(cat "$battery/capacity")" "$(cat "$battery/status")" "$plugged"
                    break
                done
            ]], function(output)
                local capacity, status, plugged = output:match("^(%d+)\n([^\n]+)\n([01])")
                M.check_sample(tonumber(capacity), status, plugged == "1")
            end)
        end,
    })
end

return M
