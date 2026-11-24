package.preload['awful'] = function() return {} end
package.preload['gears'] = function() return {} end
local clients = {}
client = {get = function() return clients end}
local m = dofile(os.getenv('HOME') .. '/.dotfiles/config/awesome/wallpaper-pause.lua')
local s = {workarea={x=0,y=49,width=1920,height=1031}}
local geometry={x=10,y=59,width=900,height=1007}
local c = { geometry=function() return geometry end, border_width=2, valid=true, type='normal', isvisible=function(self) return self.visible end, visible=true }
clients={c}
assert(not m.covered(s))
c.maximized=true; assert(m.covered(s))
c.minimized=true; assert(not m.covered(s)); c.minimized=false
c.visible=false; assert(not m.covered(s)); c.visible=true
c.maximized=false; c.fullscreen=true; assert(m.covered(s))
c.hidden=true; assert(not m.covered(s)); c.hidden=false
c.fullscreen=false; c.maximized_horizontal=true; assert(not m.covered(s))
c.maximized_vertical=true; assert(m.covered(s))
c.type='desktop'; assert(not m.covered(s))
print('wallpaper pause: OK')

c.type='normal'; c.maximized_horizontal=false; c.maximized_vertical=false
geometry.width=1896; assert(m.covered(s))
geometry.width=900; assert(not m.covered(s))
print('workarea coverage: OK')
local function window(x, y, width, height)
    return { valid=true, type='normal', border_width=2,
        isvisible=function() return true end,
        geometry=function() return {x=x,y=y,width=width,height=height} end }
end
clients={window(10,59,940,1007), window(966,59,940,1007)}
assert(m.covered(s), 'two tiled windows cover desktop')
clients[2].minimized=true
assert(not m.covered(s), 'minimizing one exposes desktop')
clients={window(10,59,940,1007), window(966,59,940,490), window(966,565,940,501)}
assert(m.covered(s), 'three tiled windows cover desktop')
clients={window(10,59,940,1007), window(1100,59,806,1007)}
assert(not m.covered(s), 'wide central gap remains visible')
clients={window(10,59,940,1007), window(100,59,940,1007)}
assert(not m.covered(s), 'overlap must not count as extra coverage')
clients={}
assert(not m.covered(s), 'empty desktop animates')
print('combined window coverage: OK')
