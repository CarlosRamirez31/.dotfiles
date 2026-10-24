local delayed, signals, active_filter = {}, { client = {}, tag = {}, screen = {} }, nil
local function connect(kind, event, callback)
    signals[kind][event] = signals[kind][event] or {}
    table.insert(signals[kind][event], callback)
end
local function emit(kind, event, value)
    for _, callback in ipairs(signals[kind][event] or {}) do callback(value) end
end
local function flush()
    while #delayed > 0 do local callbacks = delayed; delayed = {}; for _, f in ipairs(callbacks) do f() end end
end
local screens, clients = {}, {}
screen = setmetatable({ connect_signal = function(event, callback) connect('screen', event, callback) end }, {
    __call = function(_, _, previous)
        for i, s in ipairs(screens) do if previous == nil or screens[i - 1] == previous then return s end end
    end,
})
tag = { connect_signal = function(event, callback) connect('tag', event, callback) end }
client = { connect_signal = function(event, callback) connect('client', event, callback) end }
package.loaded.awful = { client = { focus = { history = { get = function(s)
    for _, c in ipairs(clients) do if c.screen == s and c:isvisible() then return c end end
end } } }, ewmh = { add_activate_filter = function(f) active_filter = f end } }
package.loaded.gears = { timer = { delayed_call = function(f) delayed[#delayed + 1] = f end } }
local function monitor(name, x)
    local s = { valid = true, outputs = { [name] = {} }, tags = {}, geometry = { x = x, y = 0, width = 1920, height = 1080 } }
    s.workarea = s.geometry
    for i = 1, 4 do
        local t = { index = i, name = tostring(i), screen = s, selected = i == 1 }
        function t:clients()
            local result = {}
            for _, c in ipairs(clients) do for _, own in ipairs(c:tags()) do if own == self then result[#result + 1] = c end end end
            return result
        end
        s.tags[i] = t
    end
    screens[#screens + 1] = s
    return s
end
local function window(s, indices, minimized)
    local c = { valid = true, screen = s, type = 'normal', minimized = not not minimized, floating = false }
    local tags, geometry = {}, { x = s.geometry.x + 100, y = 60, width = 800, height = 600 }
    for _, i in ipairs(indices) do tags[#tags + 1] = s.tags[i] end
    function c:tags(value) if value then tags = value; emit('client', 'tagged', self) end; return tags end
    function c:lower() self.lowered = true end
    function c:geometry(value) if value then geometry = value end; return geometry end
    function c:isvisible()
        if self.minimized then return false end
        for _, t in ipairs(tags) do if t.selected then return true end end
        return false
    end
    clients[#clients + 1] = c
    return c
end
local primary, external = monitor('eDP-2', 0), monitor('DP-1', 1920)
screen.primary = primary
local foreground = window(primary, { 1 })
local a, b, d = window(external, { 4 }), window(external, { 4 }), window(external, { 3 })
local overlap = window(external, { 1, 2 })
local minimized = window(external, { 2 }, true)
client.focus = foreground
local memory = dofile('config/awesome/window-memory.lua')
memory.start(); memory.start()
assert(#signals.tag['removal-pending'] == 1)
-- X11 may already have cleared the removed output names.
external.outputs = {}; external.valid = false; screens = { primary }
emit('tag', 'removal-pending', external.tags[1]); flush()
assert(a.screen == primary and a:tags()[1] == primary.tags[4])
assert(b:tags()[1] == primary.tags[4] and d:tags()[1] == primary.tags[3])
assert(#overlap:tags() == 2 and overlap.minimized and active_filter(overlap) == false)
assert(minimized.minimized and not a.minimized)
assert(client.focus == foreground and primary.tags[1].selected)
-- Opening workspace 4 adopts those windows; workspace 3 stays untouched.
primary.tags[1].selected = false; primary.tags[4].selected = true
emit('screen', 'tag::history::update', primary)
-- Explicitly opening a parked client also adopts it.
overlap.minimized = false; emit('client', 'property::minimized', overlap)
local reconnected = monitor('DP-1', 1920)
emit('screen', 'added', reconnected); flush()
assert(a.screen == primary and b.screen == primary and overlap.screen == primary)
assert(d.screen == reconnected and d:tags()[1] == reconnected.tags[3])
assert(minimized.screen == reconnected and minimized.minimized)
assert(client.focus == foreground and primary.tags[4].selected)
-- A subsequent disconnect parks selected-tag arrivals, and reselecting the
-- current tag restores them even when selection itself did not change.
local selected = window(reconnected, { 4 })
reconnected.valid = false; screens = { primary }
emit('tag', 'removal-pending', reconnected.tags[4]); flush()
assert(selected.screen == primary and selected.minimized)
emit('screen', 'tag::history::update', primary)
assert(not selected.minimized and active_filter(selected) == nil)
-- Floating windows retain relative geometry, and a manual move cancels return.
local third = monitor('HDMI-1', 1920)
emit('screen', 'added', third); flush()
local floating = window(third, { 2 }); floating.floating = true
local adopted = window(third, { 3 })
third.valid = false; screens = { primary }
emit('tag', 'removal-pending', third.tags[2]); flush()
adopted:tags({ primary.tags[2] })
local third_back = monitor('HDMI-1', 1920)
emit('screen', 'added', third_back); flush()
assert(floating.screen == third_back and floating:geometry().x == 2020)
assert(adopted.screen == primary)
print('Window memory: matching tags, background arrival and conditional return passed')
