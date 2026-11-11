local awful = require("awful")
local gears = require("gears")
local wibox = require("wibox")
local cairo = require("lgi").cairo
local style = require("menu-style")
local colors = style.colors

local M = {}
local helper = os.getenv("HOME") .. "/.local/bin/dotfiles-desktop-panel"
local runtime = os.getenv("XDG_RUNTIME_DIR")
local spectrum = runtime and (runtime .. "/dotfiles-music-spectrum")
local screens = setmetatable({}, { __mode = "k" })
local empty = {}
local enabled, pending, scheduled = false, false, false
local generation = 0
local playing, current, cover_path, cover
local accent = colors.lavender
local levels, previous = { 0, 0, 0, 0 }, ""
local metadata_timer, spectrum_timer

local function empty_screen(s)
    for _, c in ipairs(awful.client.visible(s)) do
        if c.type ~= "dock" and c.type ~= "desktop" and c.class ~= "Polybar" then return false end
    end
    return true
end

local function scene_for(s)
    if screens[s] then return screens[s] end
    local canvas = wibox.widget.base.make_widget(nil, nil, { enable_properties = true })
    canvas.fit = function(_, _, w, h) return w, h end
    canvas.draw = function(_, _, cr, w, h)
        for i, volume in ipairs(levels) do
            local y = h * (.70 + i * .046)
            local left = w * .47
            local right = w * (.55 + volume * .053)
            local line = cairo.Pattern.create_linear(left, 0, right, 0)
            local r, g, b = gears.color.parse_color(accent)
            line:add_color_stop_rgba(0, r, g, b, 0)
            line:add_color_stop_rgba(.56, r, g, b, .10 + volume * .067)
            line:add_color_stop_rgba(1, r, g, b, 0)
            cr:set_source(line)
            cr:set_line_width(1.2 + volume * .38)
            cr:move_to(left, y)
            cr:line_to(right, y)
            cr:stroke()
        end
    end
    local window = wibox({ screen = s, type = "desktop", bg = "#00000000",
        visible = false, input_passthrough = true, ontop = false })
    screens[s] = { window = window, canvas = canvas }
    return screens[s]
end

local function card(data)
    local artwork
    if cover then
        local source = cover
        artwork = wibox.widget.base.make_widget(nil, nil, { enable_properties = true })
        artwork.fit = function() return 66, 66 end
        artwork.draw = function(_, _, cr, width, height)
            if width <= 0 or height <= 0 then return end
            local iw, ih = gears.surface.get_size(source)
            if iw <= 0 or ih <= 0 then return end
            local scale = math.max(width / iw, height / ih)
            cr:save()
            cr:translate((width - iw * scale) / 2, (height - ih * scale) / 2)
            cr:scale(scale, scale)
            cr:set_source_surface(source, 0, 0)
            cr:paint()
            cr:restore()
        end
    else
        artwork = style.icon("󰎆", 23, colors.lavender, 66, 66)
    end
    local image = wibox.widget({ artwork, forced_width = 66, forced_height = 66, shape_clip = true,
        bg = colors.raised, shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 8) end,
        widget = wibox.container.background })
    local text = wibox.widget({ style.text(data.title or "", 13, colors.text, 28),
        style.text(data.artist or "", 10, accent, 22),
        layout = wibox.layout.fixed.vertical })
    local row = wibox.widget({ image, wibox.container.margin(wibox.container.place(text, "left", "center"),
        12, 0, 0, 0), nil, layout = wibox.layout.align.horizontal })
    return wibox.widget({ { row, margins = 11, widget = wibox.container.margin },
        forced_width = 382, bg = "#171722ef", shape_border_width = 1, shape_border_color = accent .. "77",
        shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 14) end,
        widget = wibox.container.background })
end

local function display()
    for s, scene in pairs(screens) do
        if not s.valid or not empty[s] or not playing then scene.window.visible = false end
    end
    if not playing then
        if spectrum_timer.started then spectrum_timer:stop() end
        return
    end
    for s in pairs(empty) do
        local scene = scene_for(s)
        local window = scene.window
        if scene.track ~= current then
            scene.track = current
            window.widget = wibox.widget({ scene.canvas,
                wibox.container.place(wibox.container.margin(card(current), 43, 0, 0, 43), "left", "bottom"),
                layout = wibox.layout.stack })
        end
        window:geometry(s.workarea)
        window.visible = true
    end
    if spectrum and not spectrum_timer.started then spectrum_timer:start() end
end

local function fetch()
    if pending or not enabled then return end
    local token = generation
    pending = true
    awful.spawn.easy_async({ helper, "music" }, function(stdout, _, _, code)
        if token ~= generation then return end
        pending = false
        local data = {}
        if code == 0 then
            for key, value in stdout:gmatch("([^\t\n]+)\t([^\n]*)\n") do data[key] = value end
        end
        playing = data.state == "Playing"
        if playing and (not current or current.title ~= data.title or current.artist ~= data.artist or current.cover ~= data.cover) then
            current = data
            if cover_path ~= data.cover then
                cover_path, cover, accent = data.cover, nil, colors.lavender
                if cover_path and cover_path ~= "" then
                    local image, err = gears.surface.load_uncached_silently(cover_path)
                    if not err then cover = image end
                    accent = cover and require("artwork-style").accent(cover) or colors.lavender
                end
            end
        end
        display()
    end)
end

local function update()
    empty = {}
    for s in screen do if empty_screen(s) then empty[s] = true end end
    local needed = next(empty) ~= nil
    if enabled ~= needed then
        enabled = needed
        generation = generation + 1
        pending, playing, current, cover, cover_path = false, false, nil, nil, nil
        levels, previous = { 0, 0, 0, 0 }, ""
        if enabled then
            if spectrum then
                local file = io.open(spectrum, "w")
                if file then file:write("0 0 0 0\n"); file:close() end
            end
            metadata_timer:start()
            fetch()
        else
            if metadata_timer.started then metadata_timer:stop() end
            if spectrum then os.remove(spectrum) end
        end
    end
    display()
end

local function schedule()
    if scheduled then return end
    scheduled = true
    gears.timer.delayed_call(function()
        scheduled = false
        update()
    end)
end

metadata_timer = gears.timer({ timeout = 1.5, callback = fetch })
spectrum_timer = gears.timer({ timeout = .09, callback = function()
    local file = io.open(spectrum, "r")
    if not file then return end
    local value = file:read("*l")
    file:close()
    if not value or value == previous then return end
    local a, b, c, d = value:match("^([0-7]) ([0-7]) ([0-7]) ([0-7])$")
    if not a then return end
    levels, previous = { tonumber(a), tonumber(b), tonumber(c), tonumber(d) }, value
    for s in pairs(empty) do
        if screens[s] then screens[s].canvas:emit_signal("widget::redraw_needed") end
    end
end })

function M.start()
    if M.started then return end
    M.started = true
    for _, event in ipairs({ "manage", "unmanage", "tagged", "untagged",
        "property::hidden", "property::minimized", "property::sticky", "property::screen" }) do
        client.connect_signal(event, schedule)
    end
    tag.connect_signal("property::selected", schedule)
    for _, event in ipairs({ "added", "removed", "property::workarea" }) do
        screen.connect_signal(event, schedule)
    end
    awesome.connect_signal("exit", function() if spectrum then os.remove(spectrum) end end)
    schedule()
end

return M
