-- Publish tag changes once; Polybar waits on file events instead of polling D-Bus.
local gears = require("gears")
local M = {}
local pending = false
local directory = (os.getenv("XDG_RUNTIME_DIR") or os.getenv("XDG_CACHE_HOME") or
    (os.getenv("HOME") .. "/.cache")) .. "/dotfiles-polybar-tags"
local colors = { "#f9de8f", "#ff9b93", "#95e1d3", "#81a1c1" }

function M.render(s, monitor)
    local result = {}
    for i, t in ipairs(s.tags) do
        local underline = t.selected and "%{u#565c64}%{+u}" or ""
        local reset = t.selected and "%{-u}" or ""
        local name = tostring(t.name):gsub("%%", "%%%%")
        result[#result + 1] = "%{A1:dotfiles-polybar --tag " .. monitor .. " " .. i ..
            ":}%{F" .. (colors[i] or "#cdd6f4") .. "}" .. underline .. " " .. name ..
            " " .. reset .. "%{F-}%{A}"
    end
    return table.concat(result) .. "\n"
end

function M.publish()
    gears.filesystem.make_directories(directory)
    for s in screen do
        for monitor in pairs(s.outputs) do
            if monitor:match("^[a-zA-Z0-9_.:-]+$") then
                local path = directory .. "/" .. monitor
                local value = M.render(s, monitor)
                local previous = io.open(path, "r")
                local unchanged = previous and previous:read("*a") == value
                if previous then previous:close() end
                if not unchanged then
                    local file = assert(io.open(path .. ".tmp", "w"))
                    file:write(value)
                    file:close()
                    assert(os.rename(path .. ".tmp", path))
                end
            end
        end
    end
end

local function schedule()
    if pending then return end
    pending = true
    gears.timer.delayed_call(function()
        pending = false
        M.publish()
    end)
end

function M.start()
    if M.started then M.publish(); return end
    M.started = true
    for _, event in ipairs({ "property::selected", "property::name", "property::screen", "property::activated" }) do
        tag.connect_signal(event, schedule)
    end
    for _, event in ipairs({ "added", "removed", "property::outputs" }) do
        screen.connect_signal(event, schedule)
    end
    M.publish()
end

return M
