local source = arg[0]:match("^(.*)/tests/")
local workarea = dofile(source .. "/dotfiles/.config/awesome/polybar-workarea.lua")

local function bar(screen_y, top, bar_y)
    local c = {
        valid = true,
        class = "Polybar",
        screen = { geometry = { y = screen_y } },
        reservation = { top = top, bottom = 0, top_start_x = 1920, top_end_x = 3839 },
        writes = 0,
    }
    function c:geometry() return { y = bar_y or screen_y + 5, height = 44 } end
    function c:struts(value)
        if value then self.reservation = value; self.writes = self.writes + 1 end
        return self.reservation
    end
    return c
end

local lowered = bar(200, 249)
workarea.update(lowered)
assert(lowered.reservation.top == 49, "Monitor offset must not shrink its usable height")
assert(lowered.reservation.top_start_x == 1920, "Keep horizontal strut bounds")
workarea.update(lowered)
assert(lowered.writes == 1, "Do not trigger a strut update loop")

local aligned = bar(0, 49)
workarea.update(aligned)
assert(aligned.writes == 0)

local hidden = bar(200, 0)
workarea.update(hidden)
assert(hidden.reservation.top == 0 and hidden.writes == 0, "Hidden bars reserve nothing")

local other = bar(200, 249)
other.class = "OtherDock"
workarea.update(other)
assert(other.writes == 0, "Leave other applications alone")

local negative = bar(-200, 49)
workarea.update(negative)
assert(negative.reservation.top == 49)

print("Polybar workarea tests OK")
