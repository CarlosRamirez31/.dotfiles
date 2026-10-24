-- Salvage clients before Awesome deletes a disconnected screen's tags.
local awful = require("awful")
local gears = require("gears")
local M = {}
local parked = setmetatable({}, { __mode = "k" })
local outputs_by_screen = setmetatable({}, { __mode = "k" })
local function remember_outputs(s)
    if next(s.outputs or {}) then
        local names = {}
        for name in pairs(s.outputs) do names[name] = true end
        outputs_by_screen[s] = names
    end
end
local migrating = false
local remembered = setmetatable({}, { __mode = "k" })

local function destination(removed)
    if screen.primary and screen.primary ~= removed and screen.primary.valid then
        return screen.primary
    end
    for s in screen do
        if s ~= removed and s.valid and #s.tags > 0 then return s end
    end
end

function M.reveal(s)
    if migrating then return end
    for c in pairs(remembered) do
        if c.valid and c.screen == s then
            for _, t in ipairs(c:tags()) do
                if t.selected and (parked[c] or not c.minimized) then remembered[c] = nil; break end
            end
        end
    end
    for c in pairs(parked) do
        if not c.valid then
            parked[c] = nil
        elseif c.screen == s then
            for _, t in ipairs(c:tags()) do
                if t.selected then
                    parked[c] = nil
                    c.minimized = false
                    break
                end
            end
        end
    end
end

function M.salvage(t)
    local source = t.screen
    if not source then return end
    local target = destination(source)
    if not target then return end
    local batch, seen = {}, {}
    -- Snapshot the entire screen first: clients can belong to several tags.
    for _, old_tag in ipairs(source.tags) do
        for _, c in ipairs(old_tag:clients()) do
            if not seen[c] and c.valid and c.type ~= "dock" and c.type ~= "desktop" then
                seen[c] = true
                local tags, indices = {}, {}
                for _, own in ipairs(c:tags()) do
                    if own.screen == source then
                        local match = target.tags[own.index]
                        if match then tags[#tags + 1] = match; indices[#indices + 1] = own.index end
                    end
                end
                if #tags > 0 then batch[#batch + 1] = { c = c, tags = tags, indices = indices } end
            end
        end
    end
    if #batch == 0 then return end
    local focused = client.focus
    if not focused or not focused.valid or focused.screen == source or seen[focused] then
        focused = awful.client.focus.history.get(target, 0)
        if seen[focused] then focused = nil end
    end
    migrating = true
    for _, entry in ipairs(batch) do
        local c = entry.c
        if not remembered[c] then
            local outputs = {}
            for name in pairs(outputs_by_screen[source] or source.outputs or {}) do outputs[name] = true end
            local geometry = c:geometry()
            geometry.x, geometry.y = geometry.x - source.geometry.x, geometry.y - source.geometry.y
            remembered[c] = { outputs = outputs, tags = entry.indices,
                minimized = c.minimized and not parked[c], geometry = geometry, floating = c.floating }
        end
        local visible = c.sticky
        for _, own in ipairs(entry.tags) do visible = visible or own.selected end
        if visible and not c.minimized then
            parked[c] = true
            c.minimized = true
        end
        -- Assign directly: move_to_screen also moves keyboard/pointer focus.
        c.screen = target
        c:tags(entry.tags)
        c:lower()
    end
    gears.timer.delayed_call(function()
        if focused and focused.valid and focused:isvisible() then client.focus = focused end
        migrating = false
    end)
end


function M.restore(s)
    if not s.valid or #s.tags == 0 then return end
    migrating = true
    for c, record in pairs(remembered) do
        local matches = false
        for name in pairs(s.outputs or {}) do matches = matches or record.outputs[name] end
        if not c.valid then
            remembered[c], parked[c] = nil, nil
        elseif matches then
            local tags, visible = {}, c.sticky
            for _, index in ipairs(record.tags) do
                if s.tags[index] then
                    tags[#tags + 1] = s.tags[index]
                    visible = visible or s.tags[index].selected
                end
            end
            if #tags > 0 then
                c.screen = s
                c:tags(tags)
                parked[c] = visible and not record.minimized or nil
                c.minimized = record.minimized or not not parked[c]
                if record.floating then
                    local g, area = record.geometry, s.workarea or s.geometry
                    local width, height = math.min(g.width, area.width), math.min(g.height, area.height)
                    c:geometry({ x = math.max(area.x, math.min(s.geometry.x + g.x, area.x + area.width - width)),
                        y = math.max(area.y, math.min(s.geometry.y + g.y, area.y + area.height - height)),
                        width = width, height = height })
                end
                c:lower()
                remembered[c] = nil
            end
        end
    end
    gears.timer.delayed_call(function() migrating = false end)
end

function M.start()
    if M.started then return end
    M.started = true
    for s in screen do remember_outputs(s) end
    tag.connect_signal("removal-pending", M.salvage)
    -- view_only emits this even when clicking the already selected tag.
    screen.connect_signal("tag::history::update", M.reveal)
    awful.ewmh.add_activate_filter(function(c)
        if parked[c] then return false end
    end)
    local function used(c)
        if not migrating then remembered[c], parked[c] = nil, nil end
    end
    client.connect_signal("focus", used)
    client.connect_signal("property::screen", used)
    client.connect_signal("tagged", used)
    client.connect_signal("property::minimized", function(c)
        if not c.minimized then used(c) end
    end)
    screen.connect_signal("added", function(s)
        remember_outputs(s)
        gears.timer.delayed_call(function() M.restore(s) end)
    end)
    screen.connect_signal("property::outputs", function(s)
        remember_outputs(s)
        gears.timer.delayed_call(function() M.restore(s) end)
    end)
    client.connect_signal("unmanage", function(c) remembered[c], parked[c] = nil, nil end)
end

return M
