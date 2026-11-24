local source = (arg[0]:match('^(.*)/tests/') or '.')
local allocations,draws,clears=0,0,0
local image={get_type=function() return 'IMAGE' end,flush=function() end}
local software={get_target=function() return image end,
    set_operator=function(_,op) if op=='CLEAR' then clears=clears+1 end end,
    paint=function() end,set_font_options=function() end,
    set_source=function(_,source) assert(source=='foreground','Preserve inherited text color') end}
package.preload.lgi=function() return {GLib={unsetenv=function(key) assert(key=='CAIRO_DEBUG') end},cairo={
    Format={ARGB32=0},Operator={CLEAR='CLEAR',OVER='OVER'},
    ImageSurface={create=function(_,w,h) allocations=allocations+1;return image end},
    Context=function() return software end,
}} end
local hierarchy={draw=function(self,context,cr)
    assert(cr:get_target():get_type()=='IMAGE','Widget trees must draw into owned pixels')
    draws=draws+1
end}
package.preload['wibox.hierarchy']=function() return hierarchy end
local module=dofile(source..'/config/awesome/rendering.lua')
module.start();local wrapped=hierarchy.draw;module.start();assert(wrapped==hierarchy.draw)
local width,height=620,550
local tree={get_size=function() return width,height end}
local painted=0
local native={get_target=function() return {get_type=function() return 'XCB' end} end,
    get_font_options=function() return {} end,get_source=function() return 'foreground' end,
    save=function() end,restore=function() end,
    set_source_surface=function(_,surface,x,y) assert(surface==image and x==0 and y==0) end,
    paint=function() painted=painted+1 end}
hierarchy.draw(tree,{},native);hierarchy.draw(tree,{},native)
assert(draws==2 and painted==2 and allocations==1 and clears==2,'Reuse the backing image and clear it each repaint')
width=320;hierarchy.draw(tree,{},native)
assert(allocations==2,'Resize the backing image when geometry changes')
width=0;hierarchy.draw(tree,{},native);assert(draws==3 and allocations==2)
hierarchy.draw(tree,{},software);assert(draws==4 and allocations==2,'Image exports use the normal path')
print('Software rendering: complete trees, cached buffers, resize and normal image export passed')
