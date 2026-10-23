local awful = require("awful")
local beautiful = require("beautiful")
local gears = require("gears")
local M = {}
local monitor, recovering
local helper = os.getenv("HOME") .. "/.local/bin/dotfiles-appearance"

function M.apply(gap, border, accent)
    assert(type(gap) == "number" and gap >= 0 and gap <= 100)
    assert(type(border) == "number" and border >= 0 and border <= 20)
    assert(type(accent) == "string" and accent:match("^#%x%x%x%x%x%x$"))
    beautiful.useless_gap, beautiful.border_width, beautiful.border_focus = gap, border, accent
    if awful.rules.rules[1] and awful.rules.rules[1].properties then
        awful.rules.rules[1].properties.border_width = border
    end
    for _, c in ipairs(client.get()) do
        if c.type == "normal" and not c.skip_taskbar and c.class ~= "Emulator" then
            c.border_width = border
            c.border_color = c == client.focus and accent or beautiful.border_normal
        end
    end
    for s in screen do
        for _, t in ipairs(s.tags) do t.gap = gap end
        awful.layout.arrange(s)
    end
end

function M.start()
    awful.spawn.easy_async({ helper, "--export-saved" }, function(output, _, _, code)
        if code ~= 0 then return end
        local values = {}
        for key, value in output:gmatch("([^\t\n]+)\t([^\n]+)") do values[key] = value end
        if values.accent then M.apply(tonumber(values.gap), tonumber(values.border), values.accent) end
    end)
    if monitor then return end
    -- Finish monitor setup and publish a valid wallpaper pixmap before GLX
    -- binds it. These previously raced each other at login.
    recovering = true
    awful.spawn.easy_async({ os.getenv("HOME") .. "/.local/bin/dotfiles-display", "--auto" }, function()
        awful.spawn.easy_async({ os.getenv("HOME") .. "/.local/bin/dotfiles-wallpaper", "restore" }, function()
            awful.spawn.easy_async({ helper, "--start-compositor" }, function()
                recovering = false
            end)
        end)
    end)
    monitor = gears.timer({ timeout = 5, autostart = true, callback = function()
        if recovering then return end
        recovering = true
        awful.spawn.easy_async({ helper, "--ensure-compositor" }, function()
            recovering = false
        end)
    end })
end

return M
