local awful = require("awful")
local gears = require("gears")
local wibox = require("wibox")
local style = require("menu-style")

local M = {}
local colors = style.colors
local months = { "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre" }
local weekdays = { "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom" }
local popup, body, timer, year, month

local function text(value, size)
    return wibox.widget({
        text = value, font = "JetBrainsMono Nerd Font Bold " .. (size or 10),
        align = "center", valign = "center", widget = wibox.widget.textbox,
        forced_height = 30,
    })
end

local function cell(value, color, background, callback)
    local label = text(value, 10)
    local widget = wibox.widget({ label, fg = color or colors.text,
        bg = background, shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 8) end,
        widget = wibox.container.background })
    if callback then
        widget:buttons(gears.table.join(awful.button({}, 1, callback)))
        widget:connect_signal("mouse::enter", function() widget.bg = colors.raised end)
        widget:connect_signal("mouse::leave", function() widget.bg = background end)
    end
    return widget
end

local function hide()
    if popup then popup.visible = false end
    if timer then timer:stop(); timer = nil end
end

local render
local function move(delta)
    local date = os.date("*t", os.time({ year = year, month = month + delta, day = 1, hour = 12 }))
    year, month = date.year, date.month
    render()
end

local function today()
    local date = os.date("*t")
    year, month = date.year, date.month
    render()
end

render = function()
    body:reset()
    local now = os.date("*t")
    local title = text(months[month] .. " " .. year, 12)
    title.align = "left"
    body:add(wibox.widget({
        { title, fg = colors.lavender, widget = wibox.container.background },
        nil,
        { cell("‹", colors.text, colors.surface, function() move(-1) end),
          cell("›", colors.text, colors.surface, function() move(1) end),
          cell("×", colors.muted, colors.surface, hide),
          forced_width = 96, spacing = 4, layout = wibox.layout.flex.horizontal },
        layout = wibox.layout.align.horizontal,
    }))

    local grid = wibox.layout.grid()
    grid.forced_num_cols, grid.homogeneous, grid.spacing = 7, true, 4
    grid.expand = true
    for col, name in ipairs(weekdays) do
        grid:add_widget_at(cell(name, col >= 6 and colors.lavender or colors.muted), 1, col)
    end
    local first = os.date("*t", os.time({ year = year, month = month, day = 1, hour = 12 }))
    local offset = (first.wday + 5) % 7
    local last = os.date("*t", os.time({ year = year, month = month + 1, day = 0, hour = 12 })).day
    -- Always show six rows so changing months doesn't move the controls.
    for index = 0, 41 do
        local day = index - offset + 1
        local valid = day >= 1 and day <= last
        local is_today = valid and year == now.year and month == now.month and day == now.day
        local color = is_today and colors.base or (index % 7 >= 5 and colors.lavender or colors.text)
        grid:add_widget_at(cell(valid and tostring(day) or "", color,
            is_today and colors.lavender or nil), math.floor(index / 7) + 2, index % 7 + 1)
    end
    body:add(grid)
    body:add(cell(string.format("Hoy · %d %s %d", now.day, months[now.month]:lower(), now.year),
        colors.blue, colors.surface, today))
end

function M.show()
    hide()
    local anchor = mouse.coords()
    local screen = mouse.screen or awful.screen.focused()
    body = wibox.layout.fixed.vertical()
    body.spacing = 12
    today()
    if not popup then
        popup = awful.popup({
            visible = false, ontop = true, type = "dialog", bg = colors.base,
            border_width = 1, border_color = colors.border,
            minimum_width = 320, maximum_width = 320,
            shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 14) end,
            widget = wibox.widget.textbox(),
        })
    end
    popup.screen = screen
    popup.widget = wibox.widget({ body, margins = 16, widget = wibox.container.margin })
    local below_bar = screen.geometry.y + math.floor(screen.geometry.height * 0.005) + 52
    for _, bar in ipairs(client.get()) do
        if bar.class == "Polybar" and bar.screen == screen then
            local geometry = bar:geometry()
            if anchor.x >= geometry.x and anchor.x <= geometry.x + geometry.width then
                below_bar = geometry.y + geometry.height + 8
                break
            end
        end
    end
    local function place()
        local geometry = screen.geometry
        popup.x = math.max(geometry.x + 8, math.min(anchor.x - popup.width / 2,
            geometry.x + geometry.width - popup.width - 8))
        popup.y = math.max(geometry.y + 8, math.min(below_bar,
            geometry.y + geometry.height - popup.height - 8))
    end
    if popup._calendar_place then
        popup:disconnect_signal("property::width", popup._calendar_place)
        popup:disconnect_signal("property::height", popup._calendar_place)
    end
    popup._calendar_place = place
    popup:connect_signal("property::width", place)
    popup:connect_signal("property::height", place)
    popup.visible = true
    place()
    local date_key = os.date("%Y-%m-%d")
    timer = gears.timer({ timeout = 30, autostart = true, callback = function()
        local new_key = os.date("%Y-%m-%d")
        if new_key ~= date_key then date_key = new_key; render() end
    end })
end

function M.toggle()
    if popup and popup.visible then hide() else M.show() end
end

return M
