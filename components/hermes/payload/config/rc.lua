local awful = require('awful')
local gears = require('gears')
local beautiful = dofile('/opt/presentacion/config/theme.lua')
require('awful.autofocus')
local mod = 'Mod1'
beautiful.border_width = 0
beautiful.useless_gap = 5
awful.layout.layouts = { awful.layout.suit.tile, awful.layout.suit.tile.left, awful.layout.suit.floating, awful.layout.suit.max }
awful.screen.connect_for_each_screen(function(s)
    awful.tag({'1','2','3','4'}, s, awful.layout.layouts[1])
end)
local function spawn(cmd) return function() awful.spawn.with_shell('exec '..cmd) end end
local function focus(dir) return function() awful.client.focus.bydirection(dir) end end
local function swap(dir) return function() awful.client.swap.bydirection(dir) end end
local function float()
    local c=client.focus; if not c then return end
    c.fullscreen=false; c.maximized=false; c.floating=not c.floating
    if c.floating then awful.placement.centered(c,{honor_workarea=true}) end
    c:raise()
end
local keys=gears.table.join(
    awful.key({mod},'Return',spawn('alacritty')),
    awful.key({mod,'Control'},'t',spawn('alacritty')),
    awful.key({mod},'space',spawn('rofi -show drun')),
    awful.key({mod},'d',spawn('rofi -show drun')),
    awful.key({mod},'F2',spawn('rofi -show run')),
    awful.key({mod},'Tab',spawn('rofi -modi window,drun -show window')),
    awful.key({mod},'b',spawn('presentacion firefox')),
    awful.key({mod},'e',spawn('alacritty -e yazi @HOST_HOME@/Documents/Universidad')),
    awful.key({mod},'w',spawn('/opt/presentacion/bin/wallpaper-picker')),
    awful.key({mod},'q',function() if client.focus then client.focus:kill() end end),
    awful.key({mod},'v',float),
    awful.key({mod},'f',function() if client.focus then client.focus.fullscreen=not client.focus.fullscreen end end),
    awful.key({mod},'F9',function() if client.focus then client.focus.minimized=true end end),
    awful.key({mod,'Shift'},'e',function() awesome.quit() end),
    awful.key({'Mod4'},'space',spawn('@HOST_HOME@/.local/bin/dotfiles-keyboard-toggle')),
    awful.key({},'Print',spawn('/opt/presentacion/bin/screenshot full')),
    awful.key({mod},'Print',spawn('/opt/presentacion/bin/screenshot area')),
    awful.key({mod,'Shift'},'s',spawn('/opt/presentacion/bin/screenshot area')),
    awful.key({},'XF86AudioRaiseVolume',spawn('pactl set-sink-volume @DEFAULT_SINK@ +5%')),
    awful.key({},'XF86AudioLowerVolume',spawn('pactl set-sink-volume @DEFAULT_SINK@ -5%')),
    awful.key({},'XF86AudioMute',spawn('pactl set-sink-mute @DEFAULT_SINK@ toggle'))
)
for _,v in ipairs({{'h','left'},{'j','down'},{'k','up'},{'l','right'},{'Left','left'},{'Down','down'},{'Up','up'},{'Right','right'}}) do
    keys=gears.table.join(keys,awful.key({mod},v[1],focus(v[2])),awful.key({mod,'Shift'},v[1],swap(v[2])))
end
for index=1,4 do
    keys=gears.table.join(keys,
        awful.key({mod},'#'..index+9,function() local t=awful.screen.focused().tags[index];if t then t:view_only() end end),
        awful.key({mod,'Shift'},'#'..index+9,function() local c=client.focus; if c then local t=c.screen.tags[index];if t then c:move_to_tag(t);t:view_only() end end end))
end
root.keys(keys)
awful.rules.rules={
    {rule={},properties={border_width=beautiful.border_width,border_color=beautiful.border_normal,
        focus=awful.client.focus.filter,raise=true,screen=awful.screen.preferred,
        placement=awful.placement.no_overlap+awful.placement.no_offscreen,
        floating=false,maximized=false,fullscreen=false,
        buttons=gears.table.join(awful.button({mod,'Shift'},1,function(c) c.floating=true; c:raise();awful.mouse.client.move(c) end))}},
    {rule_any={type={'dock'},class={'Polybar'}},properties={floating=true,sticky=true,ontop=true,border_width=0,focusable=false,skip_taskbar=true}},
    {rule_any={type={'dialog','utility','splash'}},properties={floating=true,placement=awful.placement.centered}},
}
client.connect_signal('focus',function(c)c.border_color=beautiful.border_focus end)
client.connect_signal('unfocus',function(c)c.border_color=beautiful.border_normal end)
client.connect_signal('mouse::enter',function(c) if awful.client.focus.filter(c) then c:emit_signal('request::activate','mouse_enter',{raise=false}) end end)
local area=dofile('/opt/presentacion/config/polybar-workarea.lua'); area.start()
