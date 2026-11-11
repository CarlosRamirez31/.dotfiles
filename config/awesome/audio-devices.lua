local awful = require('awful')
local gears = require('gears')
local wibox = require('wibox')
local style = require('menu-style')
local colors = style.colors
local M = {}
local helper = os.getenv('HOME') .. '/.local/bin/dotfiles-audio-devices'
local generation, pending, tab, page = 0, false, 'outputs', 1
local anchor, output = nil, ''
local mode = 'outputs'
local popup = awful.popup({ visible = false, ontop = true, type = 'dialog',
    width = 410, minimum_width = 410, maximum_width = 410, bg = colors.base, border_width = 1, border_color = colors.border,
    widget = wibox.widget.textbox(),
    shape = function(cr,w,h) gears.shape.rounded_rect(cr,w,h,14) end })
local timer, refresh, render
local function place()
    if popup.visible and anchor then style.place_below_bar(popup,anchor) end
end
popup:connect_signal('property::height',place)
popup:connect_signal('property::width',place)
local function hide()
    generation = generation + 1
    popup.visible, pending = false, false
    if timer.started then timer:stop() end
end
local function apply(entry)
    if pending then return end
    pending = true
    local token = generation
    awful.spawn.easy_async({helper,entry.kind,entry.id,entry.key},function(_,err,_,code)
        if token ~= generation then return end
        pending = false
        if code ~= 0 then require('naughty').notify({title='Audio selection',text=err}) end
        refresh()
    end)
end
render = function(failed)
    local rows = wibox.layout.fixed.vertical()
    rows.spacing = 8
    rows:add(wibox.widget({style.text(mode=='inputs' and 'Audio inputs' or 'Audio devices',11,colors.lavender,28),nil,
        style.action('×',hide),layout=wibox.layout.align.horizontal}))
    if mode~='inputs' then rows:add(wibox.widget({style.action('Outputs',function() tab='outputs';page=1;render() end,
        tab=='outputs' and colors.lavender or colors.muted),
        style.action('Profiles',function() tab='profiles';page=1;render() end,
        tab=='profiles' and colors.lavender or colors.muted),spacing=8,layout=wibox.layout.flex.horizontal})) end
    local entries={}
    for kind,id,key,active,label in output:gmatch('([^\t\n]+)\t(%d+)\t([^\t\n]+)\t([01])\t([^\n]+)\n') do
        if (mode=='inputs' and (kind=='source' or kind=='source-port')) or (mode~='inputs' and (tab=='profiles') == (kind=='profile')) then
            entries[#entries+1]={kind=kind,id=id,key=key,active=active=='1',label=label}
        end
    end
    local count=math.max(1,math.min(6,math.floor((popup.screen.workarea.height-180)/60)))
    local pages=math.max(1,math.ceil(#entries/count))
    page=math.min(page,pages)
    if #entries==0 then rows:add(style.text(failed and 'Audio unavailable' or 'No devices available',9,colors.muted,32)) end
    for i=(page-1)*count+1,math.min(page*count,#entries) do
        local entry=entries[i]
        local label=(entry.active and '●  ' or '○  ') .. entry.label
        local widget=style.action(label,function() apply(entry) end,entry.active and colors.lavender or colors.text)
        awful.tooltip({objects={widget},text=entry.label})
        rows:add(widget)
    end
    if pages>1 then rows:add(wibox.widget({
        style.action('‹',function() page=math.max(1,page-1);render() end),
        style.text(page..' / '..pages,9,colors.muted,28),
        style.action('›',function() page=math.min(pages,page+1);render() end),
        layout=wibox.layout.align.horizontal})) end
    rows:add(style.text(mode=='inputs' and 'Select an input to move current recording.' or tab=='outputs' and 'Select an output to move current playback.'
        or 'Profiles may also change microphone availability.',8,colors.muted,30))
    popup.widget=wibox.container.margin(rows,12,12,12,12)
    style.reveal(popup)
    style.place_below_bar(popup,anchor)
end
refresh=function()
    if pending then return end
    pending=true
    local token=generation
    local command = mode=='inputs' and {helper,'inputs'} or {helper}
    awful.spawn.easy_async(command,function(data,_,_,code)
        if token~=generation then return end
        pending=false
        output=code==0 and data or ''
        render(code~=0)
    end)
end
timer=gears.timer({timeout=3,callback=refresh})
function M.toggle(requested)
    if popup.visible or pending then hide();return end
    anchor=mouse.coords()
    popup.screen=mouse.screen or awful.screen.focused()
    mode=requested=='inputs' and 'inputs' or 'outputs'
    tab,page='outputs',1
    refresh()
    timer:start()
end
return M
