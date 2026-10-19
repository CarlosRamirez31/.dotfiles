-- Polybar's EWMH top strut includes the monitor's root-coordinate Y offset.
-- Awesome applies it to the client's screen, so convert it to local pixels.
local M = {}

function M.update(c)
    if not c.valid or c.class ~= "Polybar" then return end
    local struts = c:struts()
    -- Polybar clears its reservation when hidden; keep fullscreen behaviour.
    if not struts.top or struts.top == 0 then return end
    local geometry = c:geometry()
    local top = math.max(0, geometry.y - c.screen.geometry.y) + geometry.height
    if struts.top ~= top then
        struts.top = top
        c:struts(struts)
    end
end

function M.start()
    if M.started then return end
    M.started = true
    for _, signal in ipairs({ "manage", "property::class", "property::geometry",
                               "property::screen", "property::struts" }) do
        client.connect_signal(signal, M.update)
    end
    screen.connect_signal("property::geometry", function(s)
        for _, c in ipairs(client.get(s)) do M.update(c) end
    end)
    for _, c in ipairs(client.get()) do M.update(c) end
end

return M
