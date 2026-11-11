local wibox = require("wibox")
local gears = require("gears")
local lgi = require("lgi")
local M = {}

M.colors = {
    base = "#171722", surface = "#20202e", raised = "#303040", border = "#39394f",
    text = "#cdd6f4", muted = "#a6adc8", blue = "#89b4fa", green = "#a6e3a1",
    lavender = "#cba6f7", red = "#f38ba8", yellow = "#f9e2af",
}

-- Fit the finished widget at the popup's fixed width before mapping it.
function M.reveal(popup)
    if popup.visible then return end
    local widget = popup.widget
    local _, height = wibox.widget.base.fit_widget(widget, { dpi = popup.screen.dpi }, widget, popup.width, 9999)
    popup.height = math.max(1, math.ceil(height))
    popup.visible = true
end

function M.icon(symbol, size, color, width, height)
    width, height = width or 28, height or width or 28
    local widget = wibox.widget.base.make_widget(nil, nil, { enable_properties = true })
    widget.forced_width, widget.forced_height = width, height
    widget.fit = function() return width, height end
    widget.draw = function(_, _, cr, w, h)
        -- Transitions can briefly allocate zero space; Cairo cannot invert a zero scale.
        if w <= 2 or h <= 2 then return end
        local layout = lgi.PangoCairo.create_layout(cr)
        layout:set_font_description(lgi.Pango.FontDescription.from_string("JetBrainsMono Nerd Font " .. size))
        layout:set_text(symbol, -1)
        local ink = layout:get_pixel_extents()
        local scale = math.min(1, math.max(0, w - 2) / math.max(1, ink.width),
            math.max(0, h - 2) / math.max(1, ink.height))
        cr:save()
        cr:set_source(gears.color(color or M.colors.blue))
        cr:translate((w - ink.width * scale) / 2 - ink.x * scale,
            (h - ink.height * scale) / 2 - ink.y * scale)
        cr:scale(scale, scale)
        cr:move_to(0, 0)
        lgi.PangoCairo.show_layout(cr, layout)
        cr:restore()
    end
    return widget
end

function M.text(value, size, color, height)
    return wibox.widget({
        markup = '<span foreground="' .. (color or M.colors.text) .. '">'
            .. gears.string.xml_escape(tostring(value)) .. '</span>',
        font = "JetBrainsMono Nerd Font Bold " .. size, valign = "center",
        ellipsize = "end", forced_height = height, widget = wibox.widget.textbox,
    })
end

function M.action(value, callback, color)
    local label = M.text(value, 9, color, 28)
    local row = wibox.widget({
        { label, left = 8, right = 8, widget = wibox.container.margin },
        bg = M.colors.surface, widget = wibox.container.background,
        shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 7) end,
    })
    row:buttons(require("awful").button({}, 1, callback))
    row:connect_signal("mouse::enter", function() row.bg = M.colors.raised end)
    row:connect_signal("mouse::leave", function() row.bg = M.colors.surface end)
    return row
end

function M.place_below_bar(popup, anchor)
    local screen = popup.screen
    local g = screen.workarea
    local y = g.y + 8
    for _, c in ipairs(client.get(screen)) do
        if c.class == "Polybar" then
            local bar = c:geometry()
            if anchor.x >= bar.x and anchor.x < bar.x + bar.width
                and anchor.y >= bar.y and anchor.y < bar.y + bar.height then
                y = bar.y + bar.height + 8
                break
            end
        end
    end
    popup.x = math.max(g.x + 8, math.min(anchor.x - popup.width / 2, g.x + g.width - popup.width - 8))
    popup.y = math.max(g.y, math.min(y, g.y + g.height - popup.height - 8))
end

return M
