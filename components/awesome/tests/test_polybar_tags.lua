local source = arg[0]:match("^(.*)/tests/")
package.loaded.gears = {}
local tags = dofile(source .. "/dotfiles/.config/awesome/polybar-tags.lua")
local left = { tags = { { name = "1", selected = true }, { name = "2", selected = false } } }
local right = { tags = { { name = "1", selected = false }, { name = "2", selected = true } } }
local a = tags.render(left, "eDP-2")
local b = tags.render(right, "HDMI-1-1")
assert(a:find("--tag eDP-2 1", 1, true))
assert(not a:find("HDMI-1-1", 1, true), "Monitor tags must not leak between outputs")
assert(b:find("--tag HDMI-1-1 2", 1, true))
assert(a:find("%{+u} 1", 1, true))
assert(b:find("%{+u} 2", 1, true))
left.tags[1].selected, left.tags[2].selected = false, true
local changed = tags.render(left, "eDP-2")
assert(changed ~= a and changed:find("%{+u} 2", 1, true))
assert(a:sub(-1) == "\n", "The stream requires one complete line per update")
print("Polybar tag tests OK")
