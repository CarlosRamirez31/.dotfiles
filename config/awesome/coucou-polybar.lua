-- Coucou grows out of Polybar after a deliberate hover at its centre.
local awful = require("awful")
local gears = require("gears")
local function seconds() return require("lgi").GLib.get_monotonic_time() / 1000000 end
local M = { hover_delay = 0.3, leave_delay = 0.6, half_width = 140 }
M.pointer = function() return mouse.coords() end
M.seconds = seconds
local island, entered_at, left_at, opened_here, pending, dismissed, triggered
local input_shapes = setmetatable({}, { __mode = "k" })
local executable = os.getenv("HOME") .. "/.local/bin/coucou"

local function mode(c)
    return (c.name or ""):match("^Coucou Island | (%a+) |")
end

local function bar_for(s)
    for _, c in ipairs(client.get(s)) do
        if c.class == "Polybar" and not c.hidden and not c.minimized then return c end
    end
end

-- Awesome reparents GTK clients into its own X11 frame. Clearing only GTK's
-- ShapeInput leaves that frame swallowing clicks over the invisible island.
local function input_shape(c)
    local g = c:geometry()
    local expanded = mode(c) == "expanded"
    local w, h = (c.name or ""):match("| (%d+) | (%d+)$")
    w, h = tonumber(w) or g.width, tonumber(h) or g.height
    local signature = expanded and table.concat({g.width, g.height, w, h}, ":") or "empty"
    if input_shapes[c] == signature then return end
    local cairo = require("lgi").cairo
    local surface = cairo.ImageSurface(cairo.Format.A1, expanded and g.width or 0, expanded and g.height or 0)
    if expanded then
        local context = cairo.Context(surface)
        context:set_source_rgba(1, 1, 1, 1)
        context:rectangle(math.max(0, (g.width - w) / 2), 0, w, h)
        context:fill()
    end
    c.shape_input = surface._native
    surface:finish()
    input_shapes[c] = signature
end

local function place(c)
    if not c.valid then return end
    local bar = bar_for(c.screen)
    if not bar then return end
    local b, g = bar:geometry(), c:geometry()
    local x, y = b.x + math.floor((b.width - g.width) / 2), b.y + b.height - 1
    if g.x ~= x or g.y ~= y then c:geometry({ x = x, y = y }) end
    -- Keep WebKit mapped: unmapping pauses its animation frames and prevents opening.
    if c.hidden then c.hidden = false end
    if c.opacity ~= 1 then c.opacity = 1 end
    input_shape(c)
end

-- Flow has its own dock at the bottom, unrelated to the island. Shape its
-- Awesome frame too: GTK input alone leaves a full transparent frame clickable.
local flow_shapes = setmetatable({}, { __mode = "k" })
local function flow_shape(c)
    if not c.valid or c.class ~= "Coucou" then return end
    local w, h, rectangles = (c.name or ""):match("^Coucou Flow | (%d+) | (%d+) |%s*(.*)$")
    w, h = tonumber(w), tonumber(h)
    if not w or not h or w <= 0 or h <= 0 then return end
    local g = c:geometry()
    local signature = table.concat({g.width, g.height, c.name}, ":")
    if flow_shapes[c] == signature then return end
    flow_shapes[c] = signature
    c.border_width = 0
    local cairo = require("lgi").cairo
    local surface = cairo.ImageSurface(cairo.Format.A1, g.width, g.height)
    local context = cairo.Context(surface)
    context:set_source_rgba(1, 1, 1, 1)
    for rx, ry, rw, rh in rectangles:gmatch("(%d+),(%d+),(%d+),(%d+);") do
        local x, y, width, height = tonumber(rx), tonumber(ry), tonumber(rw), tonumber(rh)
        if width > 0 and height > 0 and x + width <= w and y + height <= h then
            context:rectangle(x * g.width / w, y * g.height / h, width * g.width / w, height * g.height / h)
        end
    end
    context:fill()
    c.shape_input, c.shape_bounding = surface._native, surface._native
    surface:finish()
end

local function attach(c)
    flow_shape(c)
    if not c.valid or c.class ~= "Coucou" or not mode(c) then return end
    if island == c then return end
    island = c
    entered_at, left_at, opened_here, pending, dismissed, triggered = nil, nil, false, nil, nil, false
    c.floating, c.sticky, c.ontop = true, true, true
    c.border_width, c.skip_taskbar, c.size_hints_honor = 0, true, true
    -- GTK requests focus when a text field is selected. The generic dock rule
    -- otherwise forces focusable=false even after GTK enables keyboard input.
    c.focusable = true
    c:connect_signal("property::geometry", function() place(c) end)
    c:connect_signal("property::name", function()
        if mode(c) == "expanded" then dismissed = false end
        place(c)
    end)
    place(c)
end

local function toggle()
    pending = { deadline = M.seconds() + 1.5, target = mode(island) == "expanded" and "compact" or "expanded" }
    awful.spawn({ executable, "--shortcut", "toggleIsland" }, false)
end

function M.start()
    -- GTK may set WM_CLASS/title after manage, and Coucou can restart independently.
    for _, c in ipairs(client.get()) do attach(c) end
    if M.timer then
        if not M.timer.started then M.timer:start() end
        return
    end
    client.connect_signal("manage", attach)
    client.connect_signal("property::name", attach)
    client.connect_signal("property::class", attach)
    for _, c in ipairs(client.get()) do attach(c) end
    M.timer = gears.timer({ timeout = 0.1, autostart = true, callback = function()
        if not island or not island.valid then
            for _, candidate in ipairs(client.get()) do attach(candidate) end
        end
        for _, candidate in ipairs(client.get()) do flow_shape(candidate) end
        local c = island
        if not c or not c.valid then return end
        local bar = bar_for(c.screen)
        if not bar then return end
        place(c)
        local b, p = bar:geometry(), M.pointer()
        local centre = b.x + b.width / 2
        local hotspot = p.x >= centre - M.half_width and p.x <= centre + M.half_width
            and p.y >= b.y and p.y <= b.y + b.height
        local now = M.seconds()
        M.debug = { mode = mode(c), opened_here = opened_here, hotspot = hotspot, left_at = left_at, now = now }
        if pending then
            -- The app acknowledged the transition: no fixed dead time after it.
            if mode(c) == pending.target then pending = nil
            elseif now < pending.deadline then return
            else pending = nil end
        end
        if hotspot then
            opened_here = true
            left_at = nil
            if mode(c) ~= "expanded" and not triggered then
                entered_at = entered_at or now
                if now - entered_at >= M.hover_delay then
                    opened_here, dismissed, triggered = true, false, true
                    toggle()
                    entered_at = nil
                end
            end
        else
            triggered = false
            entered_at = nil
            if opened_here and mode(c) == "expanded" then
                local g = c:geometry()
                local w, h = (c.name or ""):match("| (%d+) | (%d+)$")
                w, h = tonumber(w) or 400, tonumber(h) or 250
                local inside = p.x >= centre - w / 2 - 8 and p.x <= centre + w / 2 + 8
                    and p.y >= b.y and p.y <= g.y + h + 8
                if inside or client.focus == c then left_at = nil else
                    left_at = left_at or now
                    if now - left_at >= M.leave_delay then
                        opened_here, dismissed, left_at = false, true, nil
                        toggle()
                    end
                end
            else left_at = nil end
        end
    end })
end

return M
