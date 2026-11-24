-- Render widget trees to an owned image before transferring them to X11.
-- This avoids the broken transformed/clipped XRender path on hybrid graphics.
local cairo = require('lgi').cairo
local M = {}

function M.start()
    if M.started then return true end
    M.started = true
    -- Retire the old process-wide workaround; GTK children use their defaults.
    require('lgi').GLib.unsetenv('CAIRO_DEBUG')
    local hierarchy = require('wibox.hierarchy')
    local original = hierarchy.draw
    local buffers = setmetatable({}, {__mode='k'})
    hierarchy.draw = function(self, context, cr)
        local kind = cr:get_target():get_type()
        if kind ~= 'XCB' and kind ~= 'XLIB' then return original(self, context, cr) end
        local width, height = self:get_size()
        width, height = math.ceil(width), math.ceil(height)
        if width < 1 or height < 1 then return end
        local buffer = buffers[self]
        if not buffer or buffer.width ~= width or buffer.height ~= height then
            buffer = {width=width, height=height,
                image=cairo.ImageSurface.create(cairo.Format.ARGB32, width, height)}
            buffers[self] = buffer
        end
        local software = cairo.Context(buffer.image)
        software:set_operator(cairo.Operator.CLEAR)
        software:paint()
        software:set_operator(cairo.Operator.OVER)
        software:set_font_options(cr:get_font_options())
        -- Textboxes without explicit markup inherit the drawable foreground.
        software:set_source(cr:get_source())
        -- Recursive children target the image and follow the normal draw path.
        original(self, context, software)
        buffer.image:flush()
        cr:save()
        cr:set_source_surface(buffer.image, 0, 0)
        cr:paint()
        cr:restore()
    end
    return true
end
return M
