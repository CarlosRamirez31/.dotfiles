local awful = require("awful")
local gears = require("gears")
local wibox = require("wibox")
local style = require("menu-style")
local colors = style.colors

local M = {}
local helper = os.getenv("HOME") .. "/.local/bin/dotfiles-polybar"
local pending, running = {}, false
local icons = {}
local title = wibox.widget({ font = "JetBrainsMono Nerd Font Bold 10", widget = wibox.widget.textbox })
local value = wibox.widget({ font = "JetBrainsMono Nerd Font Bold 10", widget = wibox.widget.textbox })
local bar = wibox.widget({ max_value = 100, forced_height = 5, background_color = colors.raised,
    shape = gears.shape.rounded_bar, bar_shape = gears.shape.rounded_bar, widget = wibox.widget.progressbar })
local glyph = wibox.layout.stack()
local popup = awful.popup({
    visible = false, ontop = true, input_passthrough = true, type = "notification",
    minimum_width = 244, maximum_width = 244, minimum_height = 58, maximum_height = 58,
    bg = colors.base, fg = colors.text, border_color = colors.border, border_width = 1,
    shape = function(cr, width, height) gears.shape.rounded_rect(cr, width, height, 14) end,
    widget = {
        { glyph, {
            { { title, nil, value, layout = wibox.layout.align.horizontal },
                bar, spacing = 6, layout = wibox.layout.fixed.vertical },
            left = 10, widget = wibox.container.margin,
        }, nil, layout = wibox.layout.align.horizontal },
        margins = 12, widget = wibox.container.margin,
    },
})
local hide = gears.timer({ timeout = 1.4, single_shot = true, callback = function() popup.visible = false end })

local function show(kind, level, muted, target)
    local brightness = kind == "brightness"
    local symbol = brightness and "󰃠" or muted and "󰖁" or "󰕾"
    local accent = brightness and colors.yellow or muted and colors.muted or colors.lavender
    icons[symbol] = icons[symbol] or style.icon(symbol, 15, accent, 26, 30)
    glyph:reset()
    glyph:add(icons[symbol])
    title.text = brightness and "Brightness" or "Volume"
    value.text = muted and "Muted" or string.format("%d%%", level)
    bar.color, bar.value = accent, muted and 0 or math.min(100, level)
    if not target.valid then target = awful.screen.focused() end
    popup.screen = target
    local area = target.workarea
    popup.x = area.x + math.floor((area.width - popup.width) / 2)
    popup.y = area.y + area.height - popup.height - 36
    popup.visible = true
    hide:again()
end

local function drain()
    local request = table.remove(pending, 1)
    if not request then running = false; return end
    local kind = request.kind
    local brightness = kind == "brightness"
    local status = brightness and { helper, "--brightness", "status" }
        or { "wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@" }
    awful.spawn.easy_async({ helper, "--" .. kind, request.action }, function(_, _, _, code)
        if code ~= 0 or #pending > 0 then drain(); return end
        awful.spawn.easy_async(status, function(output, _, _, status_code)
            if status_code == 0 and #pending == 0 then
                local level = tonumber(output:match(brightness and "^%s*(%d+)%%" or "^Volume:%s+([%d.]+)"))
                if level then
                    show(kind, brightness and level or math.floor(level * 100 + 0.5),
                        not brightness and output:find("[MUTED]", 1, true), request.screen)
                end
            end
            drain()
        end)
    end)
end

function M.adjust(kind, action)
    pending[#pending + 1] = { kind = kind, action = action, screen = awful.screen.focused() }
    if running then return end
    running = true
    drain()
end

return M
