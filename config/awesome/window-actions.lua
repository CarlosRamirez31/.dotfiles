local awful = require("awful")
local beautiful = require("beautiful")
local gears = require("gears")
local wibox = require("wibox")
local naughty = require("naughty")
local style = require("menu-style")
local colors = style.colors

local M = {}
local focus, pinned, menu_client, anchor
local updating_border = false
local popup = awful.popup({ visible = false, ontop = true, type = "dialog",
    minimum_width = 254, maximum_width = 254, bg = colors.base, fg = colors.text,
    border_width = 1, border_color = colors.border, widget = wibox.widget.textbox(),
    shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 14) end,
})
local function eligible(c)
    return c and c.valid and c.focusable and not c.skip_taskbar
        and c.type ~= "dock" and c.type ~= "desktop"
end

local function end_focus()
    local saved = focus
    if not saved then return end
    focus = nil
    if saved.client.valid then saved.client.fullscreen = saved.fullscreen end
    if saved.screen.valid then require("polybar-visibility").suppress(saved.screen, false) end
    require("notification-center").set_quiet(saved.quiet)
end

local function update_pin_border(c, changed)
    if not pinned or pinned.client ~= c or updating_border then return end
    if changed then pinned[changed] = c[changed] end
    updating_border = true
    local show_border = c == client.focus or c == mouse.current_client
    c.border_width = show_border and (beautiful.border_width or pinned.border_width) or 0
    c.border_color = (show_border and beautiful.border_focus or beautiful.border_normal) or pinned.border_color
    updating_border = false
end

local function pin_width_changed(c) update_pin_border(c, "border_width") end
local function pin_color_changed(c) update_pin_border(c, "border_color") end
local function pin_interaction_changed(c)
    gears.timer.delayed_call(function() if c.valid then update_pin_border(c) end end)
end

local function place_pinned(saved)
    if pinned ~= saved or not saved.client.valid then return end
    local c = saved.client
    local g = c.screen.workarea
    local ratio = math.max(1, math.min(2.4, saved.geometry.width / math.max(1, saved.geometry.height)))
    local width = math.min(540, math.floor(g.width * .36), math.floor(g.height * .42 * ratio))
    local height = math.floor(width / ratio)
    local margin = 18 + 2 * c.border_width
    c:geometry({ x = g.x + g.width - width - margin, y = g.y + g.height - height - margin,
        width = width, height = height })
    c:raise()
end

local function restore_window()
    local saved = pinned
    pinned = nil
    if not saved or not saved.client.valid then return end
    local c = saved.client
    c:disconnect_signal("property::border_width", pin_width_changed)
    c:disconnect_signal("property::border_color", pin_color_changed)
    c:disconnect_signal("focus", pin_interaction_changed)
    c:disconnect_signal("unfocus", pin_interaction_changed)
    c:disconnect_signal("mouse::enter", pin_interaction_changed)
    c:disconnect_signal("mouse::leave", pin_interaction_changed)
    c.border_width, c.border_color = saved.border_width, saved.border_color
    if saved.screen.valid and c.screen ~= saved.screen then c.screen = saved.screen end
    local tags = {}
    for _, t in ipairs(saved.tags) do
        if t.activated and t.screen == c.screen then tags[#tags + 1] = t end
    end
    if #tags > 0 then c:tags(tags) end
    if saved.floating and saved.screen.valid then c:geometry(saved.geometry) end
    c.floating, c.sticky, c.ontop = saved.floating, saved.sticky, saved.ontop
    c.size_hints_honor = saved.size_hints
    if saved.maximized then
        c.maximized = true
    else
        c.maximized_horizontal = saved.maximized_horizontal
        c.maximized_vertical = saved.maximized_vertical
    end
    c.fullscreen = saved.fullscreen
end

function M.toggle_focus()
    if focus then end_focus(); return end
    local c = client.focus
    if not eligible(c) then return end
    if pinned and pinned.client == c then
        restore_window()
        if not c:isvisible() then c:jump_to() end
    end
    focus = { client = c, screen = c.screen, fullscreen = c.fullscreen, quiet = naughty.is_suspended() }
    require("notification-center").set_quiet(true)
    c.fullscreen = true
    require("polybar-visibility").suppress(c.screen, true)
end

function M.toggle_floating(c)
    if pinned then restore_window(); return end
    c = c or client.focus
    if not eligible(c) then
        c = nil
        for _, candidate in ipairs(awful.client.visible(awful.screen.focused())) do
            if eligible(candidate) then
                if c then return end
                c = candidate
            end
        end
    end
    if not eligible(c) then return end
    if focus then end_focus() end
    local original = c:geometry()
    pinned = { client = c, screen = c.screen, tags = c:tags(), geometry = original, floating = c.floating,
        sticky = c.sticky, ontop = c.ontop, size_hints = c.size_hints_honor, fullscreen = c.fullscreen,
        maximized = c.maximized, maximized_horizontal = c.maximized_horizontal,
        maximized_vertical = c.maximized_vertical, border_width = c.border_width, border_color = c.border_color }
    c.fullscreen, c.maximized, c.maximized_horizontal, c.maximized_vertical = false, false, false, false
    c.floating, c.sticky, c.ontop, c.size_hints_honor = true, true, true, false
    c:connect_signal("property::border_width", pin_width_changed)
    c:connect_signal("property::border_color", pin_color_changed)
    c:connect_signal("focus", pin_interaction_changed)
    c:connect_signal("unfocus", pin_interaction_changed)
    c:connect_signal("mouse::enter", pin_interaction_changed)
    c:connect_signal("mouse::leave", pin_interaction_changed)
    update_pin_border(c)
    local saved = pinned
    place_pinned(saved)
    -- Let any pending layout from leaving fullscreen or tiling finish.
    gears.timer.delayed_call(function() place_pinned(saved) end)
end

local function hide()
    popup.visible = false
    menu_client = nil
end

local function new_terminal_here(c)
    if client.focus ~= c then return end
    root.fake_input("key_press", "Control_L")
    root.fake_input("key_press", "Shift_L")
    root.fake_input("key_press", "F12")
    root.fake_input("key_release", "F12")
    root.fake_input("key_release", "Shift_L")
    root.fake_input("key_release", "Control_L")
end

local function render(c, moving)
    local rows = wibox.layout.fixed.vertical()
    rows.spacing = 6
    local title = require("polybar-tags").render_app(c, c.screen):gsub("\n$", "")
    local title_row = wibox.widget({ style.text(moving and "Move to workspace" or title, 11, colors.lavender, 27),
        nil, style.action("×", hide, colors.muted), layout = wibox.layout.align.horizontal })
    rows:add(title_row)
    local function action(label, callback, color)
        rows:add(style.action(label, function()
            hide()
            if c.valid then callback() end
        end, color))
    end
    if moving then
        for _, t in ipairs(c.screen.tags) do
            if t.activated then
                action("Workspace " .. t.name, function()
                    if pinned and pinned.client == c then restore_window() end
                    if t.activated then c:move_to_tag(t) end
                end)
            end
        end
    else
        local class = (c.class or ""):lower()
        if class == "kitty" or class == "dotfiles-terminal-drawer" then
            action("New terminal here", function() new_terminal_here(c) end, colors.blue)
        elseif class == "brave" or class == "brave-browser" then
            action("New private window", function()
                awful.spawn({ os.getenv("HOME") .. "/.local/bin/dotfiles-app-launch", "brave", "--incognito" })
            end, colors.blue)
        end
        action(c.ontop and "Unpin from top" or "Keep above", function() c.ontop = not c.ontop end)
        action(pinned and "Restore floating window" or "Floating window", function() M.toggle_floating(c) end)
        rows:add(style.action("Move to workspace   ›", function()
            if c.valid then render(c, true) else hide() end
        end))
    end
    popup.widget = wibox.widget({ rows, margins = 10, widget = wibox.container.margin })
    style.reveal(popup)
    style.place_below_bar(popup, anchor)
end

popup:connect_signal("property::height", function()
    if anchor and popup.visible then style.place_below_bar(popup, anchor) end
end)

function M.toggle_menu()
    if popup.visible then hide(); return end
    local c = client.focus
    if not eligible(c) or c.screen ~= mouse.screen then return end
    menu_client, anchor = c, mouse.coords()
    popup.screen = c.screen
    render(c, false)
end

client.connect_signal("focus", function(c)
    if menu_client and c ~= menu_client then hide() end
end)
client.connect_signal("unmanage", function(c)
    if menu_client == c then hide() end
    if focus and focus.client == c then
        local saved = focus
        focus = nil
        if saved.screen.valid then require("polybar-visibility").suppress(saved.screen, false) end
        require("notification-center").set_quiet(saved.quiet)
    end
    if pinned and pinned.client == c then pinned = nil end
end)

local function check_focus()
    if focus and (not focus.client.valid or not focus.client.fullscreen or not focus.client:isvisible()
        or focus.client.screen ~= focus.screen) then end_focus() end
end
for _, event in ipairs({ "property::fullscreen", "property::minimized", "property::hidden", "property::screen" }) do
    client.connect_signal(event, function(c)
        if focus and c == focus.client then gears.timer.delayed_call(check_focus) end
    end)
end
tag.connect_signal("property::selected", function()
    if focus then gears.timer.delayed_call(check_focus) end
end)
awesome.connect_signal("exit", end_focus)

return M
