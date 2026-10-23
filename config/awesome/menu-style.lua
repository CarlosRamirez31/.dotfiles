local wibox = require("wibox")
local gears = require("gears")
local lgi = require("lgi")
local M = {}

M.colors = {
    base = "#171722", surface = "#20202e", raised = "#303040", border = "#39394f",
    text = "#cdd6f4", muted = "#a6adc8", blue = "#89b4fa", green = "#a6e3a1",
    lavender = "#cba6f7", red = "#f38ba8", yellow = "#f9e2af",
}

function M.icon(symbol, size, color, width, height)
    width, height = width or 28, height or width or 28
    local widget = wibox.widget.base.make_widget(nil, nil, { enable_properties = true })
    widget.forced_width, widget.forced_height = width, height
    widget.fit = function() return width, height end
    widget.draw = function(_, _, cr, w, h)
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

return M
