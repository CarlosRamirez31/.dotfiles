-- The emulator publishes the rendered device size in WM_NORMAL_HINTS even
-- when tiling assigns its Qt container a larger rectangle. Shape that spare
-- area out instead of making Android itself translucent or forcing floating.
local M = {}

function M.attach(c)
    if c._emulator_shape_attached then return end
    c._emulator_shape_attached = true

    local function device_shape(cr, width, height)
        local size = (c.size_hints or {}).user_size
        if size and size.width > 0 and size.height > 0 then
            local border = 2 * c.border_width
            width = math.min(width, size.width + border)
            height = math.min(height, size.height + border)
        end
        cr:rectangle(0, 0, width, height)
    end

    local function update()
        if not c.valid then return end
        -- The separate toolbar and extended controls must keep their shape.
        if c.class == "Emulator" and (c.name or ""):match("^Android Emulator") then
            c.shape = device_shape
        end
    end

    c:connect_signal("property::name", update)
    c:connect_signal("property::size_hints", update)
    update()
end

return M
