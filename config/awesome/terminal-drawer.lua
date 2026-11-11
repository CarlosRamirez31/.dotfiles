local awful = require("awful")
local gears = require("gears")

local M = {}
local window, previous_focus, target
local wanted, starting = false, false
local animation
local class = "dotfiles-terminal-drawer"

local function animate(c, from, to, fade_in, done)
    if animation then animation:stop() end
    local frame, frames = 0, 8
    local opacity = c.opacity or 1
    local end_opacity = fade_in and 1 or .35
    animation = gears.timer({ timeout = 1 / 60, autostart = true, callback = function()
        if not c.valid then animation:stop(); animation = nil; return end
        frame = frame + 1
        local fraction = frame / frames
        local ease = 1 - (1 - fraction) ^ 3
        c.y = math.floor(from + (to - from) * ease + .5)
        c.opacity = opacity + (end_opacity - opacity) * ease
        if frame == frames then
            animation:stop()
            animation = nil
            if done then done() end
        end
    end })
end

local function show()
    local c = window
    if not target or not target.valid then target = awful.screen.focused() end
    if client.focus ~= c then previous_focus = client.focus end
    local g = target.workarea
    local width = math.min(1080, math.floor(g.width * .76))
    local height = math.min(520, math.floor(g.height * .49))
    local top = g.y + 3
    c.screen = target
    if target.selected_tag then c:move_to_tag(target.selected_tag) end
    c:geometry({ x = g.x + math.floor((g.width - width) / 2), y = top,
        width = width, height = height })
    c.opacity = .35
    c.minimized = false
    c.hidden = false
    client.focus = c
    c:raise()
    animate(c, top, top + 14, true)
end

local function hide()
    local c = window
    if c.hidden then return end
    local restore = previous_focus
    animate(c, c.y, c.screen.workarea.y + 3, false, function()
        local focused = client.focus == c
        c.hidden = true
        c.opacity = 1
        if focused and restore and restore.valid and restore:isvisible() then client.focus = restore end
    end)
end

function M.start()
    if M.started then return end
    M.started = true
    local function register(c)
        if (c.class or ""):lower() ~= class then return false end
        window, starting = c, false
        c.floating, c.sticky, c.ontop, c.skip_taskbar = true, true, true, true
        return true
    end
    client.connect_signal("manage", function(c)
        if register(c) then
            if wanted then show() else c.hidden = true end
        end
    end)
    client.connect_signal("unmanage", function(c)
        if c ~= window then return end
        if animation then animation:stop(); animation = nil end
        window, previous_focus, wanted = nil, nil, false
    end)
    for _, c in ipairs(client.get()) do
        if register(c) then wanted = c:isvisible(); break end
    end
end

function M.toggle()
    M.start()
    if window and window.valid and wanted and (window.hidden or window.minimized) then wanted = false end
    wanted = not wanted
    if wanted then target = awful.screen.focused() end
    if window and window.valid then
        if wanted then show() else hide() end
    elseif wanted and not starting then
        local pid = awful.spawn({ os.getenv("HOME") .. "/.local/bin/dotfiles-terminal",
            "--class", class, "--title", "Kitty Drawer" }, false)
        starting = type(pid) == "number"
        if starting then
            gears.timer.start_new(4, function()
                if not window then starting, wanted = false, false end
                return false
            end)
        else
            wanted = false
        end
    end
end

return M
