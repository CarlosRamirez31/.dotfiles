local awful=require('awful')
local gears=require('gears')
local wibox=require('wibox')
local style=require('menu-style')
local colors=style.colors
local M={}
local target,grabber
local saved=setmetatable({},{__mode='k'})
local popup=awful.popup({visible=false,ontop=true,type='dialog',width=470,minimum_width=470,maximum_width=470,
    bg=colors.base,border_width=1,border_color=colors.border,widget=wibox.widget.textbox(),
    shape=function(cr,w,h) gears.shape.rounded_rect(cr,w,h,16) end})
local presets={
    {name='Main left',layout=awful.layout.suit.tile,factor=.62,columns=1,rects={{0,0,.62,1},{.65,0,.35,.48},{.65,.52,.35,.48}}},
    {name='Main right',layout=awful.layout.suit.tile.left,factor=.62,columns=1,rects={{0,0,.35,.48},{0,.52,.35,.48},{.38,0,.62,1}}},
    {name='Three columns',layout=awful.layout.suit.tile,factor=1/3,columns=2,rects={{0,0,.31,1},{.35,0,.30,1},{.69,0,.31,1}}},
    {name='Grid',layout=awful.layout.suit.fair,rects={{0,0,.48,.48},{.52,0,.48,.48},{0,.52,.48,.48},{.52,.52,.48,.48}}},
    {name='Maximized',layout=awful.layout.suit.max,rects={{0,0,1,1}}},
    {name='Floating',layout=awful.layout.suit.floating,rects={{0,0,.7,.7},{.3,.3,.7,.7}}},
}
local function hide()
    popup.visible=false
    if grabber then awful.keygrabber.stop(grabber);grabber=nil end
end
local function valid() return target and target.activated and target.selected end
local function place()
    if not popup.visible then return end
    local area=popup.screen.workarea
    popup.x=area.x+math.floor((area.width-popup.width)/2)
    popup.y=area.y+math.max(0,math.floor((area.height-popup.height)/2))
end
popup:connect_signal('property::width',place)
popup:connect_signal('property::height',place)
local function apply(index)
    if not valid() then hide();return end
    local preset=presets[index]
    for _,c in ipairs(target:clients()) do
        if c.fullscreen then require('naughty').notify({title='Arrange windows',text='Exit fullscreen before arranging this workspace.'});return end
    end
    local state={layout=target.layout,factor=target.master_width_factor,columns=target.column_count,
        masters=target.master_count,clients=setmetatable({},{__mode='k'})}
    for _,c in ipairs(target:clients()) do
        if not c.floating then
            state.clients[c]={maximized=c.maximized,horizontal=c.maximized_horizontal,vertical=c.maximized_vertical}
            c.maximized,c.maximized_horizontal,c.maximized_vertical=false,false,false
        end
    end
    saved[target]=state
    target.master_width_factor=preset.factor or .5
    target.column_count=preset.columns or 1
    target.master_count=1
    target.layout=preset.layout
    hide()
end
local function undo()
    if not valid() or not saved[target] then return end
    local state=saved[target]
    saved[target]=nil
    target.layout=state.layout
    target.master_width_factor,target.column_count,target.master_count=state.factor,state.columns,state.masters
    for c,value in pairs(state.clients) do
        if c.valid then c.maximized=value.maximized;c.maximized_horizontal=value.horizontal;c.maximized_vertical=value.vertical end
    end
    hide()
end
local function tile(preset,index)
    local preview=wibox.widget.base.make_widget(nil,nil,{enable_properties=true})
    preview.fit=function() return 196,66 end
    preview.draw=function(_,_,cr,w,h)
        if w<=0 or h<=0 then return end
        for i,r in ipairs(preset.rects) do
            cr:set_source(gears.color(i==1 and colors.lavender or '#585477'))
            cr:rectangle(8+r[1]*(w-16),5+r[2]*(h-10),r[3]*(w-16),r[4]*(h-10))
            cr:fill()
        end
    end
    local widget=wibox.widget({{preview,style.text(index..'  '..preset.name,9,colors.text,27),
        layout=wibox.layout.fixed.vertical},bg=colors.surface,
        shape=function(cr,w,h) gears.shape.rounded_rect(cr,w,h,10) end,widget=wibox.container.background})
    widget:buttons(awful.button({},1,function() apply(index) end))
    widget:connect_signal('mouse::enter',function() widget.bg=colors.raised end)
    widget:connect_signal('mouse::leave',function() widget.bg=colors.surface end)
    return widget
end
function M.toggle()
    if popup.visible then hide();return end
    local s=awful.screen.focused()
    target=s.selected_tag
    if not target then return end
    popup.screen=s
    local rows=wibox.layout.fixed.vertical()
    rows.spacing=10
    rows:add(wibox.widget({style.text('Arrange windows',11,colors.lavender,29),nil,
        style.action('×',hide),layout=wibox.layout.align.horizontal}))
    for i=1,6,2 do rows:add(wibox.widget({tile(presets[i],i),tile(presets[i+1],i+1),spacing=10,
        layout=wibox.layout.flex.horizontal})) end
    if saved[target] then rows:add(style.action('↶  Undo last arrangement   ·   U',undo,colors.lavender)) end
    rows:add(style.text('1–6 to choose · Esc to close · Floating windows stay free',8,colors.muted,25))
    popup.widget=wibox.container.margin(rows,14,14,14,14)
    style.reveal(popup)
    place()
    grabber=awful.keygrabber.run(function(modifiers,key,event)
        if event~='press' then return end
        if key=='Escape' or (key=='F3' and gears.table.hasitem(modifiers,'Mod1')) then hide()
        elseif key:match('^[1-6]$') then apply(tonumber(key))
        elseif key=='u' then undo() end
    end)
end
tag.connect_signal('property::selected',function() if popup.visible then hide() end end)
return M
