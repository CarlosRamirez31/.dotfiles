local beautiful = { border_normal = "#242438" }
local arranged = 0
local awful = { rules = { rules = { { properties = {} } } },
    layout = { arrange = function() arranged = arranged + 1 end } }
package.loaded.beautiful, package.loaded.awful = beautiful, awful
local timer_count, recovery_timer, commands = 0, nil, {}
package.loaded.gears = { timer = function(properties)
    timer_count = timer_count + 1
    recovery_timer = properties
    return properties
end }
awful.spawn = { easy_async = function(args, callback)
    table.insert(commands, args[2])
    if args[2] == "--export-saved" then callback("gap\t8\nborder\t1\naccent\t#abcdef\n", "", "exit", 0)
    else callback("", "", "exit", 0) end
end }
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
appearance.start()
assert(commands[1] == "--export-saved" and commands[2] == "--auto" and commands[3] == "restore" and commands[4] == "--start-compositor")
assert(beautiful.useless_gap == 8 and normal.border_width == 1)
assert(timer_count == 1 and recovery_timer.timeout == 5)
recovery_timer.callback()
assert(commands[5] == "--ensure-compositor")
appearance.start()
assert(timer_count == 1, "never create duplicate compositor monitors")
print("Appearance window checks passed")
