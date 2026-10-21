local commands = {}
package.loaded.awful = { spawn = function(args) commands[#commands + 1] = args end }
package.loaded.gears = {}
local source = arg[0]:match("^(.*)/tests/")
local visibility = dofile(source .. "/dotfiles/.config/awesome/polybar-visibility.lua")
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
assert(commands[#commands][3] == "101" and commands[#commands][5] == "show")
for _ = 1, 14 do visibility.update_screen(a, { y = 300 }, b) end
assert(commands[#commands][3] == "101" and commands[#commands][5] == "hide")
a.clients = {}
visibility.update_screen(a, { y = 300 }, b)
assert(commands[#commands][3] == "101" and commands[#commands][5] == "show")
full.tags = function() return { { selected = false } } end
a.clients = { full }
assert(not visibility.fullscreen(a), "Fullscreen on an unselected tag must not hide the bar")
print("Per-monitor Polybar visibility tests OK")
