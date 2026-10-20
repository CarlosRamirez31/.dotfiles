local awful = require("awful")
local gears = require("gears")
local modkey = "Mod1"
local layout_resize_step = 0.01
local function spawn(command)
    return function()
        awful.spawn.with_shell(
            'unset WAYLAND_DISPLAY HYPRLAND_INSTANCE_SIGNATURE MOZ_ENABLE_WAYLAND; ' ..
                'export XDG_SESSION_TYPE=x11 XDG_CURRENT_DESKTOP=awesome ' ..
                'XDG_SESSION_DESKTOP=awesome XCURSOR_THEME=Bibata-Modern-Classic ' ..
                'XCURSOR_SIZE=24 GTK_CSD=0 PATH="$HOME/.local/bin:$PATH"; exec ' .. command
        )
    end
end

local function toggle_floating()
    local c = client.focus
    if not c then return end

    if c.floating then
        c.maximized = false
        c.fullscreen = false
        c.floating = false
    else
        c.fullscreen = false
        c.maximized = false
        c.floating = true
        awful.placement.centered(c, { honor_workarea = true, honor_padding = true })
    end
    c:raise()
end

local keys = gears.table.join(
    awful.key({ modkey, "Shift" }, "d", spawn("dotfiles-lazydocker")),
    awful.key({ "Mod4" }, "p", spawn("dotfiles-display")),
    awful.key({ modkey }, "Tab", spawn("rofi -modi window,drun -show window")),
    awful.key({ modkey }, "Return", spawn("dotfiles-terminal")), awful.key({ "Control", modkey }, "t", spawn("dotfiles-terminal")), awful.key({ modkey }, "space", spawn("dotfiles-app-launcher")), awful.key({ modkey }, "d", spawn("dotfiles-app-launcher")), awful.key({ modkey }, "F2", spawn("dotfiles-app-launcher")),
    awful.key({ modkey }, "b", spawn("dotfiles-firefox")), awful.key({ modkey }, "e", spawn("dotfiles-terminal --command yazi")), awful.key({ "Control", modkey }, "e", spawn("thunar")), awful.key({ modkey }, "w", spawn("dotfiles-wallpaper choose")), awful.key({ modkey }, "c", spawn("dotfiles-clipboard")), awful.key({ "Control", "Shift" }, "b", spawn("dotfiles-lock")), awful.key({ modkey, "Shift" }, "e", function() awesome.quit() end),
    awful.key({ modkey }, "q", function() if client.focus then client.focus:kill() end end), awful.key({ modkey }, "v", toggle_floating), awful.key({ modkey }, "F9", function() if client.focus then client.focus.minimized = true end end), awful.key({ "Mod4" }, "space", spawn("dotfiles-keyboard-toggle")),
    awful.key({ modkey, "Shift" }, "equal", function()
        local c = client.focus
        if c and c.floating then c:geometry({ width = c.width + 60, height = c.height + 60 }) end
    end),
    awful.key({ modkey, "Shift" }, "minus", function()
        local c = client.focus
        if c and c.floating then c:geometry({ width = math.max(100, c.width - 60), height = math.max(100, c.height - 60) }) end
    end),
    awful.key({}, "Print", spawn("dotfiles-screenshot full")), awful.key({ modkey }, "Print", spawn("dotfiles-screenshot area")), awful.key({ modkey, "Shift" }, "s", spawn("dotfiles-screenshot area")), awful.key({ modkey, "Shift" }, "r", spawn("dotfiles-record area")), awful.key({ modkey, "Shift" }, "c", spawn("gpick")),
    awful.key({}, "XF86AudioRaiseVolume", spawn("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+")), awful.key({}, "XF86AudioLowerVolume", spawn("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-")), awful.key({}, "XF86AudioMute", spawn("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle")), awful.key({}, "XF86AudioMicMute", spawn("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle")), awful.key({}, "XF86MonBrightnessUp", spawn("$HOME/.local/bin/dotfiles-polybar --brightness up")), awful.key({}, "XF86MonBrightnessDown", spawn("$HOME/.local/bin/dotfiles-polybar --brightness down")), awful.key({}, "XF86AudioPlay", spawn("playerctl play-pause")), awful.key({}, "XF86AudioNext", spawn("playerctl next")), awful.key({}, "XF86AudioPrev", spawn("playerctl previous")),
    awful.key({ modkey }, "h", function() awful.client.focus.bydirection("left") end), awful.key({ modkey }, "j", function() awful.client.focus.bydirection("down") end), awful.key({ modkey }, "k", function() awful.client.focus.bydirection("up") end), awful.key({ modkey }, "l", function() awful.client.focus.bydirection("right") end),
    awful.key({ modkey, "Shift" }, "h", function() awful.client.swap.bydirection("left") end), awful.key({ modkey, "Shift" }, "j", function() awful.client.swap.bydirection("down") end), awful.key({ modkey, "Shift" }, "k", function() awful.client.swap.bydirection("up") end), awful.key({ modkey, "Shift" }, "l", function() awful.client.swap.bydirection("right") end),
    awful.key({ modkey, "Control" }, "h", function() awful.tag.incmwfact(-layout_resize_step) end), awful.key({ modkey, "Control" }, "l", function() awful.tag.incmwfact(layout_resize_step) end), awful.key({ modkey, "Control" }, "j", function() awful.client.incwfact(-layout_resize_step) end), awful.key({ modkey, "Control" }, "k", function() awful.client.incwfact(layout_resize_step) end),
    awful.key({ modkey }, "Left", function() awful.client.focus.bydirection("left") end), awful.key({ modkey }, "Down", function() awful.client.focus.bydirection("down") end), awful.key({ modkey }, "Up", function() awful.client.focus.bydirection("up") end), awful.key({ modkey }, "Right", function() awful.client.focus.bydirection("right") end),
    awful.key({ modkey, "Shift" }, "Left", function() awful.client.swap.bydirection("left") end), awful.key({ modkey, "Shift" }, "Down", function() awful.client.swap.bydirection("down") end), awful.key({ modkey, "Shift" }, "Up", function() awful.client.swap.bydirection("up") end), awful.key({ modkey, "Shift" }, "Right", function() awful.client.swap.bydirection("right") end),
    awful.key({ modkey, "Control" }, "Left", function() awful.tag.incmwfact(-layout_resize_step) end), awful.key({ modkey, "Control" }, "Right", function() awful.tag.incmwfact(layout_resize_step) end), awful.key({ modkey, "Control" }, "Down", function() awful.client.incwfact(-layout_resize_step) end), awful.key({ modkey, "Control" }, "Up", function() awful.client.incwfact(layout_resize_step) end)
)
for index = 1, 4 do keys = gears.table.join(keys, awful.key({ modkey }, "#" .. index + 9, function() local tag = awful.screen.focused().tags[index]; if tag then tag:view_only() end end), awful.key({ modkey, "Shift" }, "#" .. index + 9, function() if client.focus then local tag = client.focus.screen.tags[index]; if tag then client.focus:move_to_tag(tag); tag:view_only() end end end)) end
return keys
