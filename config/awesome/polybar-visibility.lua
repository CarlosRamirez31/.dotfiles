local awful = require("awful")
local gears = require("gears")
local M = { states = setmetatable({}, { __mode = "k" }) }

function M.fullscreen(s)
    for _, c in ipairs(client.get(s)) do
        if c.fullscreen and not c.hidden and not c.minimized then
            for _, t in ipairs(c:tags()) do
                if t.selected then return true end
            end
        end
    end
    return false
end

function M.pids(s)
    local result, seen = {}, {}
    local runtime = os.getenv("XDG_RUNTIME_DIR") or ("/tmp/dotfiles-display-" .. tostring(os.getenv("UID") or "1000"))
    for name in pairs(s.outputs) do
        local file = io.open(runtime .. "/dotfiles-polybar-pids/" .. name)
        if file then
            local pid = tonumber(file:read("*l"))
            file:close()
            if pid then result[#result + 1] = pid; seen[pid] = true end
        end
    end
    for _, c in ipairs(client.get(s)) do
        if c.class == "Polybar" and c.pid and not seen[c.pid] then
            result[#result + 1] = c.pid
        end
    end
    table.sort(result)
    return result
end

function M.set_visible(s, visible, pids)
    local state = M.states[s]
    local signature = table.concat(pids, ",")
    if state.visible == visible and state.signature == signature then return end
    state.visible, state.signature = visible, signature
    for _, pid in ipairs(pids) do
        awful.spawn({ "polybar-msg", "-p", tostring(pid), "cmd", visible and "show" or "hide" }, false)
    end
end

-- RandR can remove/reposition an output without moving its existing panel.
-- Keep the panel inside its current screen instead of leaving it off-screen.
function M.recover_geometry(s)
    local repaired = false
    local area = s.geometry
    for _, c in ipairs(client.get(s)) do
        if c.class == "Polybar" then
            local g = c:geometry()
            if g.x + g.width <= area.x or g.x >= area.x + area.width
                or g.y + g.height <= area.y or g.y >= area.y + area.height then
                g.x = area.x + math.max(0, math.floor((area.width - g.width) / 2))
                g.y = area.y + math.floor(area.height * 0.005)
                c:geometry(g)
                repaired = true
            end
        end
    end
    return repaired
end

function M.update_screen(s, position, pointer_screen)
    local state = M.states[s]
    if not state then
        state = {}
        M.states[s] = state
        state.show_timer = gears.timer({ timeout = 0.45, single_shot = true, callback = function()
            if M.fullscreen(s) then
                M.set_visible(s, true, M.pids(s))
                for _, c in ipairs(client.get(s)) do
                    if c.class == "Polybar" then c:raise() end
                end
            end
        end })
        state.hide_timer = gears.timer({ timeout = 2, single_shot = true, callback = function()
            if M.fullscreen(s) then M.set_visible(s, false, M.pids(s)) end
        end })
    end
    -- Polybar restores its own cached coordinates on every IPC show. Moving
    -- it back must not reset visibility: that would immediately hide a panel
    -- just revealed over fullscreen, causing an endless hide/show cycle.
    M.recover_geometry(s)
    local pids = M.pids(s)
    local full = M.fullscreen(s)
    if not full then
        state.show_timer:stop()
        state.hide_timer:stop()
        state.full = false
        M.set_visible(s, true, pids)
        return
    end
    if state.visible == nil then
        M.set_visible(s, false, pids)
    end
    state.full = true
    local top = position.y - s.geometry.y
    local on_edge = pointer_screen == s and top >= 0 and top <= 3
    local bar_bottom = 50
    for _, c in ipairs(client.get(s)) do
        if c.class == "Polybar" then
            local g = c:geometry()
            bar_bottom = math.max(bar_bottom, g.y - s.geometry.y + g.height + 5)
        end
    end
    if not state.visible then
        state.hide_timer:stop()
        if on_edge then
            if not state.show_timer.started then state.show_timer:start() end
        else
            state.show_timer:stop()
        end
    else
        state.show_timer:stop()
        local hovering = pointer_screen == s and top >= 0 and top <= bar_bottom
        if hovering then
            state.hide_timer:stop()
        elseif not state.hide_timer.started then
            state.hide_timer:start()
        end
    end
    M.set_visible(s, state.visible, pids)
end

function M.stop()
    if M.timer then M.timer:stop(); M.timer = nil end
    for _, state in pairs(M.states) do
        state.show_timer:stop()
        state.hide_timer:stop()
    end
end

function M.update()
    local position, pointer_screen = mouse.coords(), mouse.screen
    for s in screen do M.update_screen(s, position, pointer_screen) end
end

function M.start()
    if M.timer then return end
    M.timer = gears.timer({ timeout = 0.15, autostart = true, call_now = true, callback = M.update })
end

return M
