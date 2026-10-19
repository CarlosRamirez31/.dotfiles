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

-- Polybar hides while the pointer is away from the top edge, so fullscreen
-- clients can use the entire monitor. Moving the pointer to that edge reveals
-- the menu again. It remains visible briefly after the pointer leaves, making
-- the menu usable instead of disappearing immediately.
-- Unknown at startup so the first normal-workspace check explicitly restores
-- the panel even if it was hidden by a previous fullscreen client.
local polybar_visible = false
local fullscreen_mode
local polybar_hide_timer
local polybar_show_timer

local function fullscreen_is_active()
    -- Only inspect the screen currently being used. A fullscreen client on an
    -- unselected tag (or a different monitor) must not affect normal work.
    local active_screen = awful.screen.focused()
    for _, c in ipairs(client.get(active_screen)) do
        if c.fullscreen and not c.hidden then
            for _, t in ipairs(c:tags()) do
                if t.selected then return true end
            end
        end
    end
    return false
end

local function hide_polybar()
    if not fullscreen_is_active() then return end
    polybar_visible = false
    awful.spawn({ "polybar-msg", "cmd", "hide" }, false)
end

polybar_hide_timer = gears.timer({ timeout = 2, single_shot = true, callback = hide_polybar })

local function show_polybar(force)
    if polybar_hide_timer.started then polybar_hide_timer:stop() end
    if polybar_visible and not force then return end

    polybar_visible = true
    awful.spawn({ "polybar-msg", "cmd", "show" }, false)
end

-- Avoid covering controls at the top of a fullscreen window on a brief pass
-- of the pointer; it has to remain on the reveal edge for a short moment.
polybar_show_timer = gears.timer({ timeout = 0.45, single_shot = true, callback = show_polybar })

local function update_polybar_visibility()
    -- Normal windows always keep the panel and its reserved workarea. The
    -- hover behaviour is exclusively for an active fullscreen client.
    local fullscreen = fullscreen_is_active()
    if not fullscreen then
        if polybar_hide_timer.started then polybar_hide_timer:stop() end
        if polybar_show_timer.started then polybar_show_timer:stop() end
        -- Send one explicit show command whenever leaving fullscreen (and on
        -- startup); this also recovers from a bar hidden before Awesome reload.
        if fullscreen_mode ~= false then show_polybar(true) end
        fullscreen_mode = false
        return
    end

    fullscreen_mode = true

    local position = mouse.coords()
    local screen = mouse.screen
    if not screen then return end

    local from_top = position.y - screen.geometry.y
    if not polybar_visible and from_top <= 3 then
        if not polybar_show_timer.started then polybar_show_timer:start() end
    elseif not polybar_visible then
        if polybar_show_timer.started then polybar_show_timer:stop() end
    elseif polybar_visible then
        -- The panel is about 40px tall including its margins and borders.
        -- Keep it open while the pointer is on it, then wait two seconds.
        if from_top <= 50 then
            if polybar_hide_timer.started then polybar_hide_timer:stop() end
        elseif not polybar_hide_timer.started then
            polybar_hide_timer:start()
        end
    end
end

client.connect_signal("property::fullscreen", update_polybar_visibility)
client.connect_signal("focus", update_polybar_visibility)
tag.connect_signal("property::selected", update_polybar_visibility)

local polybar_hover = gears.timer({ timeout = 0.15, autostart = false, call_now = false, callback = update_polybar_visibility })
gears.timer.start_new(1, function()
    polybar_hover:start()
    return false
end)
