pcall(require, "luarocks.loader")
local awful = require("awful")
require("awful.autofocus")
local gears = require("gears")
local beautiful = require("theme")
local naughty = require("naughty")
if awesome.startup_errors then naughty.notify({ preset = naughty.config.presets.critical, title = "Awesome startup error", text = awesome.startup_errors }) end
awful.layout.layouts = { awful.layout.suit.tile, awful.layout.suit.tile.left, awful.layout.suit.floating, awful.layout.suit.max }
awful.screen.connect_for_each_screen(function(s)
    awful.tag({ "1", "2", "3", "4" }, s, awful.layout.layouts[1])
end)
require("bar")
require("quickmenus")
require("battery-alert").start()
root.keys(require("bindings"))
awful.rules.rules = require("rules")
require("polybar-workarea").start()
require("polybar-tags").start()
client.connect_signal("manage", function(c) if awesome.startup and not c.size_hints.user_position and not c.size_hints.program_position then awful.placement.no_offscreen(c) end end)

-- Some EWMH clients mark themselves sticky together with fullscreen. Prevent
-- that from letting a fullscreen window remain visible when another tag is
-- selected.
local hidden_fullscreen_clients = setmetatable({}, { __mode = "k" })
local function sync_fullscreen_tag_visibility(c)
    if not c.valid then return end
    if not c.fullscreen then
        if hidden_fullscreen_clients[c] then c.hidden = false end
        hidden_fullscreen_clients[c] = nil
        return
    end

    if c.sticky then c.sticky = false end
    local visible_on_selected_tag = false
    for _, t in ipairs(c:tags()) do
        if t.selected then
            visible_on_selected_tag = true
            break
        end
    end

    if visible_on_selected_tag then
        if hidden_fullscreen_clients[c] then c.hidden = false end
        hidden_fullscreen_clients[c] = nil
    else
        hidden_fullscreen_clients[c] = true
        c.hidden = true
    end
end

client.connect_signal("property::fullscreen", sync_fullscreen_tag_visibility)
client.connect_signal("property::sticky", sync_fullscreen_tag_visibility)
tag.connect_signal("property::selected", function(t)
    for _, c in ipairs(t:clients()) do sync_fullscreen_tag_visibility(c) end
end)

client.connect_signal("focus", function(c) c.border_color = beautiful.border_focus end)
client.connect_signal("unfocus", function(c) c.border_color = beautiful.border_normal end)
client.connect_signal("mouse::enter", function(c)
    if awful.layout.get(c.screen) ~= awful.layout.suit.magnifier
        and awful.client.focus.filter(c) then
        c:emit_signal("request::activate", "mouse_enter", { raise = false })
    end
end)
require("autostart")

-- Fullscreen and hover visibility are independent for each output.
require("polybar-visibility").start()
