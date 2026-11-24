-- Keep Awesome's menus and floating dialogs inside their monitor workarea.
local awful = require('awful')
local gears = require('gears')
local M = {}
local busy = false
local targets = setmetatable({}, {__mode='k'})

function M.fit(g, area)
    local margin = 8
    local width = math.max(1, math.min(g.width, area.width - margin * 2))
    local height = math.max(1, math.min(g.height, area.height - margin * 2))
    return {width=width, height=height,
        x=math.max(area.x + margin, math.min(g.x, area.x + area.width - width - margin)),
        y=math.max(area.y + margin, math.min(g.y, area.y + area.height - height - margin))}
end

local function fit_drawin(d, showing)
    if busy or not d.visible or (d.type ~= 'dialog' and d.type ~= 'popup_menu' and d.type ~= 'dropdown_menu') then return end
    local s = targets[d]
    if showing or not s or not s.valid then s = mouse.screen or awful.screen.focused() end
    targets[d] = s
    local geometry = d:geometry()
    local area = s.workarea
    if geometry.x + geometry.width < area.x or geometry.x > area.x + area.width
        or geometry.y + geometry.height < area.y or geometry.y > area.y + area.height then
        geometry.x = area.x + (area.width - geometry.width) / 2
        geometry.y = area.y + (area.height - geometry.height) / 2
    end
    busy = true
    local box = d.get_wibox and d.get_wibox()
    if box and box.screen ~= s then
        box.screen = s
    end
    d:geometry(M.fit(geometry, area))
    busy = false
end

local function reflow()
    for _, d in ipairs(drawin.get()) do fit_drawin(d, false) end
    for _, c in ipairs(client.get()) do
        if c.valid and c.floating and c.type ~= 'dock' and c.type ~= 'desktop'
            and c.role ~= 'dotfiles-file-tray-edge' and c.role ~= 'dotfiles-file-tray' then
            c:geometry(M.fit(c:geometry(), c.screen.workarea))
        end
    end
end

function M.start()
    if M.started then return end
    M.started = true
    M.on_visible = function(d) fit_drawin(d, true) end
    M.on_geometry = function(d) fit_drawin(d, false) end
    drawin.connect_signal('property::visible', M.on_visible)
    drawin.connect_signal('property::geometry', M.on_geometry)
    for _, signal in ipairs({'property::geometry', 'property::workarea', 'removed', 'added'}) do
        screen.connect_signal(signal, function() gears.timer.delayed_call(reflow) end)
    end
    gears.timer.delayed_call(reflow)
end
return M
