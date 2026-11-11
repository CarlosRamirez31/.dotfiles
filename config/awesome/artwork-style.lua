local gears = require("gears")
local lgi = require("lgi")
local M = {}
function M.load(path)
    local source, err = gears.surface.load_uncached_silently(path)
    if err or not source then return nil, err end
    local w, h = gears.surface.get_size(source)
    if w < 1 or h < 1 then return nil, "Empty artwork" end
    local image = lgi.cairo.ImageSurface.create(lgi.cairo.Format.ARGB32, w, h)
    local cr = lgi.cairo.Context(image)
    cr:set_source_surface(source, 0, 0)
    cr:paint()
    cr:set_source_rgba(0, 0, 0, 0)
    image:flush()
    return image
end
function M.accent(surface)
    local cairo = lgi.cairo
    local width, height = gears.surface.get_size(surface)
    if width < 1 or height < 1 then return "#cba6f7" end
    local side = 16
    local buffer = require("lgi.core").bytes.new(side * side * 4)
    local sample = cairo.ImageSurface.create_for_data(buffer, cairo.Format.RGB24, side, side, side * 4)
    local cr = cairo.Context(sample)
    cr:scale(side / width, side / height)
    cr:set_source_surface(surface, 0, 0)
    cr:paint()
    sample:flush()
    local pixels, groups, best = tostring(buffer), {}, nil
    cr:set_source_rgba(0, 0, 0, 0)
    sample:finish()
    for offset = 1, #pixels, 4 do
        local rgb = string.unpack("=I4", pixels, offset)
        local r, g, b = (rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255
        local high, low = math.max(r, g, b), math.min(r, g, b)
        if high >= 64 and high - low >= 28 then
            local key = ((r // 64) * 4 + g // 64) * 4 + b // 64
            local group = groups[key] or { count = 0, weight = 0, r = 0, g = 0, b = 0 }
            groups[key] = group
            group.count, group.weight = group.count + 1, group.weight + high - low
            group.r, group.g, group.b = group.r + r, group.g + g, group.b + b
            if not best or group.weight > best.weight then best = group end
        end
    end
    if not best then return "#cba6f7" end
    local function soften(channel) return math.floor(.68 * channel / best.count + .32 * 255 + .5) end
    return string.format("#%02x%02x%02x", soften(best.r), soften(best.g), soften(best.b))
end

return M
