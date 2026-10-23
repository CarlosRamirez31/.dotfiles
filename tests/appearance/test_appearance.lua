local beautiful = { border_normal = "#242438" }
local arranged = 0
local awful = { rules = { rules = { { properties = {} } } },
    layout = { arrange = function() arranged = arranged + 1 end } }
package.loaded.beautiful, package.loaded.awful = beautiful, awful
local normal = { type = "normal", class = "Alacritty" }
local unfocused = { type = "normal", class = "Firefox" }
local emulator = { type = "normal", class = "Emulator", border_width = 0 }
local dock = { type = "dock", border_width = 0 }
client = { focus = normal, get = function() return { normal, unfocused, emulator, dock } end }
local monitor = { tags = { {}, {} } }
screen = function(_, previous) if not previous then return monitor end end
local appearance = dofile("config/awesome/appearance.lua")
appearance.apply(12, 2, "#abcdef")
assert(beautiful.useless_gap == 12 and beautiful.border_width == 2)
assert(normal.border_width == 2 and normal.border_color == "#abcdef")
assert(unfocused.border_color == "#242438")
assert(dock.border_width == 0 and emulator.border_width == 0)
assert(monitor.tags[1].gap == 12 and monitor.tags[2].gap == 12 and arranged == 1)
assert(awful.rules.rules[1].properties.border_width == 2)
appearance.apply(100, 20, "#ffffff")
assert(normal.border_width == 20 and monitor.tags[1].gap == 100)
appearance.apply(0, 0, "#000000")
assert(normal.border_width == 0 and monitor.tags[1].gap == 0)
assert(not pcall(appearance.apply, 101, 1, "#abcdef"))
print("Appearance window checks passed")
