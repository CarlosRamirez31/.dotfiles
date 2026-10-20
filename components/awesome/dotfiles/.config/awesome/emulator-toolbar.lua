local gears = require("gears")
local M = {}

-- Anchor controls to the visible Android display, not the larger tiled Qt
-- container. Never change the main window's layout or the toolbar's size.
function M.position(parent, toolbar)
    local g = parent:geometry()
    local size = (parent.size_hints or {}).user_size or {}
    local visible_width = math.min(g.width, size.width or g.width)
    local area = parent.fullscreen and parent.screen.geometry or parent.screen.workarea
    local border = toolbar.border_width or 0
    local width = toolbar.width + 2 * border
    local height = toolbar.height + 2 * border
    local x = g.x + visible_width + 2 * (parent.border_width or 0) + 2
    if x + width > area.x + area.width then x = g.x - width - 2 end
    x = math.max(area.x, math.min(x, area.x + area.width - width))
    local y = math.max(area.y, math.min(g.y, area.y + area.height - height))
    return { x = x, y = y }
end

function M.attach(c)
    if c._emulator_toolbar_attached then return end
    c._emulator_toolbar_attached = true
    local connected_parent
    local pending = false
    local schedule

    local function sync()
        if not c.valid or c.class ~= "Emulator" or c.name ~= "Emulator" then return end
        local parent = c.transient_for
        if not parent or not parent.valid or parent.class ~= "Emulator" then return end
        if not connected_parent then
            connected_parent = parent
            for _, signal in ipairs({
                "property::geometry", "property::size_hints", "property::screen",
                "property::fullscreen", "property::minimized", "tagged", "untagged",
            }) do parent:connect_signal(signal, schedule) end
        end
        c.floating = true
        if c.screen ~= parent.screen then c.screen = parent.screen end
        c:tags(parent:tags())
        c.minimized = parent.minimized
        local pos = M.position(parent, c)
        if c.x ~= pos.x or c.y ~= pos.y then c:geometry(pos) end
    end

    schedule = function()
        if pending then return end
        pending = true
        gears.timer.delayed_call(function()
            pending = false
            sync()
        end)
    end
    for _, signal in ipairs({ "property::geometry", "property::name", "property::transient_for" }) do
        c:connect_signal(signal, schedule)
    end
    schedule()
end

return M
