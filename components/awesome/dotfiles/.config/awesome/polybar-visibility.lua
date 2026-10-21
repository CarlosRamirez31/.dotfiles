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

function M.update_screen(s, position, pointer_screen)
    local state = M.states[s]
    if not state then
        state = { edge = 0, away = 0 }
        M.states[s] = state
    end
    local pids = M.pids(s)
    local full = M.fullscreen(s)
    if not full then
        state.full, state.edge, state.away = false, 0, 0
        M.set_visible(s, true, pids)
        return
    end
    if not state.full then
        state.full, state.edge, state.away = true, 0, 0
        M.set_visible(s, false, pids)
    end
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
        state.edge = on_edge and state.edge + 1 or 0
        if state.edge >= 3 then M.set_visible(s, true, pids); state.away = 0 end
    else
        local hovering = pointer_screen == s and top >= 0 and top <= bar_bottom
        state.away = hovering and 0 or state.away + 1
        if state.away >= 14 then M.set_visible(s, false, pids); state.edge = 0 end
    end
    M.set_visible(s, state.visible, pids)
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
