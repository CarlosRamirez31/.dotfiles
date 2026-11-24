local source = (arg[0]:match('^(.*)/tests/') or '.')
package.preload.awful = function() return {} end
package.preload.gears = function() return {} end
local layout = dofile(source .. '/config/awesome/screen-layout.lua')
for _,area in ipairs({
    {x=0,y=49,width=1366,height=719},
    {x=1920,y=49,width=2560,height=1391},
    {x=-1920,y=-1080,width=1920,height=1031},
}) do
    for _,g in ipairs({{x=8000,y=8000,width=850,height=680},
        {x=-8000,y=-8000,width=4000,height=3000}}) do
        local fit=layout.fit(g,area)
        assert(fit.x>=area.x+8 and fit.y>=area.y+8)
        assert(fit.x+fit.width<=area.x+area.width-8)
        assert(fit.y+fit.height<=area.y+area.height-8)
    end
end
print('Popup layout: secondary outputs, negative coordinates and smaller screens passed')
