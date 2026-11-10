-- Publish workspace and focus changes; Polybar waits on file events.
local gears = require("gears")
local M = {}
local pending = false
local directory = (os.getenv("XDG_RUNTIME_DIR") or os.getenv("XDG_CACHE_HOME") or
    (os.getenv("HOME") .. "/.cache")) .. "/dotfiles-polybar-tags"
local colors = { "#f9de8f", "#ff9b93", "#95e1d3", "#81a1c1" }
local apps = {
    ["brave-browser"] = "Brave", brave = "Brave",
    firefox = "Firefox", chromium = "Chromium", kitty = "Kitty", thunar = "Thunar",
    code = "VS Code", ["code-oss"] = "VS Code",
    wfica = "Citrix", ["citrix-wfica"] = "Citrix", ["org.pwmt.zathura"] = "Zathura",
}

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

function M.render_app(c, s)
    if not c or c.screen ~= s or c.type == "dock" or c.type == "desktop" then return "\n" end
    local class = c.class or c.instance or ""
    -- A window class comes from the application; never interpret its markup.
    local name = apps[class:lower()] or class:gsub("[%c%%{}]", ""):gsub("^%l", string.upper)
    local length = utf8.len(name)
    if not length or length == 0 then name = "App"
    elseif length > 14 then name = name:sub(1, utf8.offset(name, 14) - 1) .. "…" end
    return name .. "\n"
end

local function publish_file(path, value)
    local previous = io.open(path, "r")
    local unchanged = previous and previous:read("*a") == value
    if previous then previous:close() end
    if unchanged then return end
    local file = assert(io.open(path .. ".tmp", "w"))
    file:write(value)
    file:close()
    assert(os.rename(path .. ".tmp", path))
end

function M.publish()
    local app_directory = directory .. "/active-app"
    gears.filesystem.make_directories(app_directory)
    for s in screen do
        local app = M.render_app(client.focus, s)
        for monitor in pairs(s.outputs) do
            if monitor:match("^[a-zA-Z0-9_.:-]+$") then
                publish_file(directory .. "/" .. monitor, M.render(s, monitor))
                publish_file(app_directory .. "/" .. monitor, app)
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
    for _, event in ipairs({ "focus", "unfocus", "property::class", "property::screen" }) do
        client.connect_signal(event, schedule)
    end
    M.publish()
end

return M
