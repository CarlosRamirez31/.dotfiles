local commands = {}
package.loaded.awful = { spawn = function(args) commands[#commands + 1] = args end }
package.loaded.gears = { timer = function(options)
    return { started = false, timeout = options.timeout,
        start = function(self) self.started = true end,
        stop = function(self) self.started = false end,
        fire = function(self)
            assert(self.started, "Timer must be running")
            self.started = false
            options.callback()
        end }
end }
local source = (arg[0]:match("^(.*)/tests/") or ".")
local visibility = dofile(source .. "/config/awesome/polybar-visibility.lua")
local a = { geometry = { y = 0 }, outputs = { A = true }, clients = {} }
local b = { geometry = { y = 0 }, outputs = { B = true }, clients = {} }
client = { get = function(s) return s.clients end }
visibility.pids = function(s) return s == a and { 101 } or { 202 } end
local full = { fullscreen = true, tags = function() return { { selected = true } } end }
a.clients = { full }
visibility.update_screen(a, { y = 300 }, b)
visibility.update_screen(b, { y = 300 }, b)
assert(commands[1][3] == "101" and commands[1][5] == "hide")
assert(commands[2][3] == "202" and commands[2][5] == "show")
for _, command in ipairs(commands) do assert(command[2] == "-p", "Never broadcast hide to all bars") end
for _ = 1, 3 do visibility.update_screen(a, { y = 0 }, a) end
visibility.states[a].show_timer:fire()
assert(commands[#commands][3] == "101" and commands[#commands][5] == "show")
for _ = 1, 14 do visibility.update_screen(a, { y = 300 }, b) end
visibility.states[a].hide_timer:fire()
assert(commands[#commands][3] == "101" and commands[#commands][5] == "hide")
a.clients = {}
visibility.update_screen(a, { y = 300 }, b)
assert(commands[#commands][3] == "101" and commands[#commands][5] == "show")
full.tags = function() return { { selected = false } } end
a.clients = { full }
assert(not visibility.fullscreen(a), "Fullscreen on an unselected tag must not hide the bar")

-- A disconnected monitor used to leave the panel at its old root coordinates.
a.geometry = { x = 0, y = 0, width = 1920, height = 1080 }
local geometry = { x = 1939, y = 5, width = 1881, height = 44 }
local raised = 0
local panel = { class = "Polybar", raise = function() raised = raised + 1 end, geometry = function(_, value)
    if value then geometry = value end
    return geometry
end }
a.clients = { panel }
visibility.update_screen(a, { y = 300 }, a)
assert(geometry.x == 19 and geometry.y == 5, "Recover panel from removed monitor")
assert(commands[#commands][5] == "show", "Show the recovered panel")
local count = #commands
visibility.update_screen(a, { y = 300 }, a)
assert(#commands == count, "Do not repeatedly move or show a healthy panel")
full.tags = function() return { { selected = true } } end
a.clients = { panel, full }
visibility.update_screen(a, { y = 300 }, a)
visibility.states[a].hide_timer:fire()
assert(commands[#commands][5] == "hide", "Keep fullscreen hiding after recovery")
for _ = 1, 3 do visibility.update_screen(a, { y = 0 }, a) end
visibility.states[a].show_timer:fire()
assert(commands[#commands][5] == "show", "Keep edge reveal after recovery")
assert(raised == 1, "Raise the revealed panel above the fullscreen window")
geometry.x = 1939 -- Polybar remaps at its cached pre-hotplug position.
local before_remap = #commands
visibility.update_screen(a, { y = 0 }, a)
assert(geometry.x == 19, "Repair cached coordinates on reveal")
assert(visibility.states[a].visible and #commands == before_remap,
    "Geometry repair during fullscreen must not hide the revealed panel")
for _ = 1, 100 do visibility.update_screen(a, { y = 35 }, a) end
assert(not visibility.states[a].hide_timer.started, "Keep panel open while hovering")
visibility.update_screen(a, { y = 300 }, a)
assert(visibility.states[a].hide_timer.timeout == 2 and visibility.states[a].hide_timer.started)
visibility.update_screen(a, { y = 35 }, a)
assert(not visibility.states[a].hide_timer.started, "Returning to panel cancels hiding")
visibility.update_screen(a, { y = 300 }, b)
visibility.update_screen(b, { y = 300 }, b)
visibility.states[a].hide_timer:fire()
assert(visibility.states[b].visible, "Fullscreen must not hide the other monitor")
a.clients = { panel }
visibility.update_screen(a, { y = 300 }, a)
assert(visibility.states[a].visible and not visibility.states[a].show_timer.started
    and not visibility.states[a].hide_timer.started, "Leaving fullscreen restores panel")
print("Per-monitor Polybar visibility tests OK")
