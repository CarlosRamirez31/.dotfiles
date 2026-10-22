local queue = {}
package.loaded.gears = { timer = { delayed_call = function(fn) table.insert(queue, fn) end } }
local toolbar = dofile("config/awesome/emulator-toolbar.lua")
local function flush()
    while #queue > 0 do table.remove(queue, 1)() end
end
local screen = {
    workarea = { x = 0, y = 50, width = 1920, height = 1030 },
    geometry = { x = 0, y = 0, width = 1920, height = 1080 },
}
local function client(fields)
    fields.valid, fields.class, fields.border_width = true, "Emulator", 2
    fields.signals, fields.screen, fields._tags = {}, screen, { "tag1" }
    function fields:geometry(pos)
        if pos then for k, v in pairs(pos) do self[k] = v end end
        return { x = self.x, y = self.y, width = self.width, height = self.height }
    end
    function fields:tags(tags) if tags then self._tags = tags end; return self._tags end
    function fields:connect_signal(name, callback) self.signals[name] = callback end
    return fields
end
local parent = client({ x = 10, y = 59, width = 712, height = 1007,
    size_hints = { user_size = { width = 566, height = 1007 } } })
local c = client({ x = 990, y = -418, width = 54, height = 506, name = "Emulator", transient_for = parent })
toolbar.attach(c)
flush()
assert(c.x == 582 and c.y == 59, "anchor to visible screen rather than tiled padding")
assert(c.floating and parent.floating == nil, "only the toolbar should float")
parent.x, parent.width = 1600, 300
parent.signals["property::geometry"]()
flush()
assert(c.x == 1540, "move to the left when there is no room on the right")
parent.y = 900
parent.signals["property::geometry"]()
flush()
assert(c.y == 570, "keep controls within the monitor")
parent.size_hints.user_size.width = 100
parent.x, parent.y = 100, 100
parent.signals["property::size_hints"]()
flush()
assert(c.x == 206 and c.y == 100, "follow resizing/rotation")
c.x, c.y = 999, -999
c.signals["property::geometry"]()
flush()
assert(c.x == 206 and c.y == 100, "correct Qt's later move requests too")
parent._tags, parent.minimized = { "tag2" }, true
parent.signals.tagged()
flush()
assert(c._tags == parent._tags and c.minimized, "follow parent workspace and minimization")
print("Emulator toolbar checks passed")
