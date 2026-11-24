local awful = require('awful')
local gears = require('gears')
local M = {}

-- Subtract window rectangles from the usable desktop. Expanding each window
-- by 12px ignores the normal tiling gutters, but keeps real exposed areas.
local function subtract(area, cover, remaining)
    local x1, y1 = math.max(area.x1, cover.x1), math.max(area.y1, cover.y1)
    local x2, y2 = math.min(area.x2, cover.x2), math.min(area.y2, cover.y2)
    if x1 >= x2 or y1 >= y2 then
        remaining[#remaining + 1] = area
        return
    end
    local function add(left, top, right, bottom)
        if left < right and top < bottom then
            remaining[#remaining + 1] = {x1=left, y1=top, x2=right, y2=bottom}
        end
    end
    add(area.x1, area.y1, area.x2, y1)
    add(area.x1, y2, area.x2, area.y2)
    add(area.x1, y1, x1, y2)
    add(x2, y1, area.x2, y2)
end

function M.covered(s)
    local w = s.workarea
    local exposed = {{x1=w.x, y1=w.y, x2=w.x+w.width, y2=w.y+w.height}}
    for _, c in ipairs(client.get(s)) do
        if c.valid and not c.minimized and not c.hidden and c:isvisible()
            and c.type ~= 'desktop' and c.type ~= 'dock' then
            if c.fullscreen or c.maximized or (c.maximized_horizontal and c.maximized_vertical) then
                return true
            end
            local g, border = c:geometry(), 2 * (c.border_width or 0)
            local cover = {x1=g.x-12, y1=g.y-12,
                           x2=g.x+g.width+border+12, y2=g.y+g.height+border+12}
            local remaining = {}
            for _, area in ipairs(exposed) do subtract(area, cover, remaining) end
            exposed = remaining
            if #exposed == 0 then return true end
        end
    end
    return false
end

function M.update()
    local command = {os.getenv('HOME') .. '/.local/bin/dotfiles-wallpaper-pause', 'screens'}
    local covered = {}
    for s in screen do
        if M.covered(s) then
            local g = s.geometry
            covered[#covered+1] = string.format('%d,%d,%d,%d', g.x, g.y, g.width, g.height)
        end
    end
    table.sort(covered)
    local signature = table.concat(covered, ';')
    if M.last == signature then return end
    M.last = signature
    for _, bounds in ipairs(covered) do command[#command+1] = bounds end
    awful.spawn(command, false)
end

function M.start()
    if M.started then return end
    M.started = true
    local timer = gears.timer { timeout = 0.15, single_shot = true, callback = M.update }
    local function schedule() timer:again() end
    for _, signal in ipairs({'manage', 'unmanage', 'tagged', 'untagged',
        'property::fullscreen', 'property::maximized', 'property::maximized_horizontal',
        'property::maximized_vertical', 'property::minimized', 'property::hidden',
        'property::sticky', 'property::screen', 'property::geometry'}) do
        client.connect_signal(signal, schedule)
    end
    tag.connect_signal('property::selected', schedule)
    screen.connect_signal('property::workarea', schedule)
    screen.connect_signal('added', schedule)
    screen.connect_signal('removed', schedule)
    schedule()
end
return M
