-- System dashboard and MPRIS player, opened from Polybar on the clicked screen.
local awful = require("awful")
local gears = require("gears")
local wibox = require("wibox")
local lgi = require("lgi")
local M = {}
local active, popup, timer, body, heading, refresh
local generation, busy = 0, false
local dragging = false
local previous_cpu, music_data, last_music_data
local weather = { city = "Santo Domingo", temperature = "—", description = "Cargando clima…" }
local home = os.getenv("HOME")
local helper = home .. "/.local/bin/dotfiles-desktop-panel"
local colors = { base = "#171722", surface = "#20202e", raised = "#373747",
    text = "#cdd6f4", muted = "#a6adc8", blue = "#89b4fa", green = "#a6e3a1",
    pink = "#f5c2e7", lavender = "#cba6f7", border = "#45475a" }

local function text(value, size, color)
    return wibox.widget({ markup = '<span foreground="' .. (color or colors.text) .. '">'
        .. gears.string.xml_escape(tostring(value or "")) .. '</span>',
        font = "Iosevka Nerd Font Bold " .. (size or 10), wrap = "word_char", widget = wibox.widget.textbox })
end

-- Center the visible ink, avoiding font bearings and baseline clipping.
local function icon(value, size, color, box)
    local widget = wibox.widget.base.make_widget(nil, nil, { enable_properties = true })
    box = box or math.ceil(size * 1.7)
    widget.forced_width, widget.forced_height = box, box
    widget.fit = function() return box, box end
    widget.draw = function(_, _, cr, width, height)
        local layout = lgi.PangoCairo.create_layout(cr)
        layout:set_font_description(lgi.Pango.FontDescription.from_string("JetBrainsMono Nerd Font " .. size))
        layout:set_text(value, -1)
        local ink = layout:get_pixel_extents()
        cr:set_source(gears.color(color or colors.blue))
        cr:move_to((width - ink.width) / 2 - ink.x, (height - ink.height) / 2 - ink.y)
        lgi.PangoCairo.show_layout(cr, layout)
    end
    return widget
end

local function margin(widget, x, y)
    return wibox.widget({ widget, left = x, right = x, top = y, bottom = y,
        widget = wibox.container.margin })
end

local function card(widget)
    return wibox.widget({ margin(widget, 10, 10), bg = colors.surface,
        shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 12) end,
        widget = wibox.container.background })
end

local function hide()
    generation = generation + 1
    if dragging then mousegrabber.stop(); dragging = false end
    if popup then popup.visible = false end
    if timer then timer:stop(); timer = nil end
    active, busy, music_data = nil, false, nil
end


local function launch(command)
    return function() hide(); awful.spawn(command) end
end

local function parse(output)
    local data = {}
    for key, value in output:gmatch("([^\t\n]+)\t([^\n]*)\n") do data[key] = value end
    return data
end

local function toggle_switch(kind)
    if busy then return end
    busy = true
    local token = generation
    awful.spawn.easy_async({ helper, "toggle", kind }, function(_, stderr, _, code)
        if token ~= generation then return end
        busy = false
        if code ~= 0 then require("naughty").notify({ title = "No se pudo cambiar el estado", text = stderr }) end
        refresh()
    end)
end

local function render_system(data)
    body:reset()
    local cpu
    local total, idle = tonumber(data.cpu_total), tonumber(data.cpu_idle)
    if previous_cpu and total > previous_cpu.total then
        cpu = math.floor(100 * (1 - (idle - previous_cpu.idle) / (total - previous_cpu.total)) + 0.5)
    end
    previous_cpu = { total = total, idle = idle }
    local avatar = icon("", 32, colors.blue, 58)
    avatar.forced_width, avatar.forced_height = 54, 58
    avatar.align, avatar.valign = "center", "center"
    if gears.filesystem.file_readable(home .. "/.face") then
        avatar = wibox.widget({ image = home .. "/.face", resize = true,
            forced_width = 54, forced_height = 58, widget = wibox.widget.imagebox })
    end
    local profile = wibox.widget({ text(data.user, "Bold 12", colors.blue),
        text("@" .. data.host, 9, colors.blue), text("up " .. data.uptime, 7, colors.blue),
        spacing = 1, layout = wibox.layout.fixed.vertical })
    local lock = icon("󰌾", 12, colors.blue, 20)
    lock:buttons(gears.table.join(awful.button({}, 1, launch({ home .. "/.local/bin/dotfiles-lock" }))))
    local logout = icon("󰍃", 12, colors.blue, 20)
    logout:buttons(gears.table.join(awful.button({}, 1, function() hide(); require("quickmenus").toggle("power") end)))
    body:add(card(wibox.widget({ { avatar, profile, spacing = 9, layout = wibox.layout.fixed.horizontal }, nil,
        { lock, logout, spacing = 12, layout = wibox.layout.fixed.vertical }, layout = wibox.layout.align.horizontal })))
    local updates = card(wibox.widget({ icon("󰮯", 16, "#f9e2af", 27), text(data.updates .. " Updates", 9, colors.blue),
        spacing = 5, layout = wibox.layout.fixed.vertical }))
    awful.tooltip({ objects = { updates }, text = "Actualizaciones según la base local de pacman" })
    local arch = icon("", 26, "#1793d1", 40)
    local distro = card(wibox.widget({ arch,
        { text(" Arch", 10, colors.blue), text("󰮯 " .. data.packages, 9, "#f9e2af"),
          text("▣ Awesome", 8, colors.pink), spacing = 2, layout = wibox.layout.fixed.vertical },
        spacing = 8, layout = wibox.layout.fixed.horizontal }))
    local system_row = wibox.layout.ratio.horizontal()
    system_row:add(wibox.container.margin(updates, 0, 7, 0, 0), distro)
    system_row:set_ratio(1, 0.38)
    body:add(system_row)
    local climate = text(weather.description, "Bold 15", colors.blue)
    climate.forced_height, climate.forced_width = 36, 100
    climate.ellipsize = "end"
    local cloud = icon("", 20, colors.lavender, 36)
    cloud.align, cloud.valign = "center", "center"
    cloud.forced_width = 43
    local degrees = text(weather.temperature, "Bold 15", colors.blue)
    degrees.align, degrees.forced_width = "right", 52
    local weather_row = wibox.layout.ratio.horizontal()
    weather_row:add(wibox.container.margin(card(wibox.widget({
            { climate, nil, degrees, layout = wibox.layout.align.horizontal },
            text(weather.city, 9, colors.blue), layout = wibox.layout.fixed.vertical })), 0, 7, 0, 0), card(cloud))
    weather_row:set_ratio(1, 0.77)
    body:add(weather_row)
    local function mini_gauge(symbol, value, detail, color)
        local ring = wibox.widget({ max_value = 100, value = value or 0, thickness = 5,
            start_angle = -math.pi / 2, colors = { color }, bg = colors.raised,
            forced_width = 48, forced_height = 48, widget = wibox.container.arcchart })
        local glyph = icon(symbol, 12, color, 48)
        local stack = wibox.widget({ ring, glyph, layout = wibox.layout.stack })
        stack.forced_width, stack.forced_height = 48, 48
        local widget = card(wibox.container.place(stack, "center", "center"))
        awful.tooltip({ objects = { widget }, text = detail .. (value and (" · " .. value .. "%") or "") })
        return widget
    end
    body:add(wibox.widget({ mini_gauge("", cpu, "CPU", colors.green),
        mini_gauge("", tonumber(data.ram), data.ram_detail, colors.blue),
        mini_gauge("", tonumber(data.disk), data.disk_detail, colors.pink),
        spacing = 7, layout = wibox.layout.flex.horizontal }))
    local function shortcut(symbol, title, callback, enabled, hint)
        local color = enabled == false and colors.raised or colors.blue
        local glyph = icon(symbol, 15, color or colors.blue, 43)
        local circle = wibox.widget({ wibox.container.place(glyph, "center", "center"), bg = colors.surface,
            shape = gears.shape.circle, forced_width = 43, forced_height = 43,
            widget = wibox.container.background })
        local name = text(title, 9, enabled == false and colors.muted or colors.blue)
        name.align = "center"
        local widget = wibox.widget({ wibox.container.place(circle), name,
            spacing = 5, layout = wibox.layout.fixed.vertical })
        widget:buttons(gears.table.join(awful.button({}, 1, callback)))
        circle:connect_signal("mouse::enter", function() circle.bg = colors.raised end)
        circle:connect_signal("mouse::leave", function() circle.bg = colors.surface end)
        awful.tooltip({ objects = { widget }, text = hint or title })
        return widget
    end
    body:add(wibox.widget({
        shortcut(data.network_kind == "wifi" and "󰤨" or "󰈀", data.network,
            function() toggle_switch("network") end, data.network_on == "1", "Encender / apagar " .. (data.network_kind == "wifi" and "Wi-Fi" or "Ethernet")),
        shortcut("", data.bluetooth_on == "1" and "ON" or "OFF",
            function() toggle_switch("bluetooth") end, data.bluetooth_on == "1", "Encender / apagar Bluetooth"),
        shortcut("", data.airplane_on == "1" and "ON" or "OFF",
            function() toggle_switch("airplane") end, data.airplane_on == "1", "Activar / desactivar modo avión"),
        spacing = 7, layout = wibox.layout.flex.horizontal }))
    local night = shortcut("󰌵", "NIGHT LIGHT", function() toggle_switch("nightlight") end, data.nightlight_on == "1")
    local terminal = shortcut("", "TERMINAL", launch({ home .. "/.local/bin/dotfiles-terminal" }))
    body:add(wibox.widget({ night, terminal, wibox.widget.textbox(),
        spacing = 7, layout = wibox.layout.flex.horizontal }))
    body:add(text(" " .. data.temperature, 9, colors.pink))
end

local function timestamp(value)
    local seconds = math.floor((tonumber(value) or 0) / 1000000)
    return string.format("%d:%02d", math.floor(seconds / 60), seconds % 60)
end

local function control(method, seconds)
    if not music_data or not music_data.player or busy then return end
    local token = generation
    busy = true
    awful.spawn.easy_async({ helper, "action", music_data.player, method, tostring(seconds or 0) },
        function(_, stderr, _, code)
            if token ~= generation then return end
            busy = false
            if code ~= 0 then
                require("naughty").notify({ title = "Música", text = stderr })
            end
            refresh()
        end)
end

local cover_path, cover_surface
local function render_music(data)
    body:reset()
    music_data, last_music_data = data, data
    local empty = data.state == "empty"
    local available = not empty and data.control == "1"
    local function music_button(symbol, title, method, supported, accent, size)
        local widget = icon(symbol, size or 12, supported and (accent or colors.blue) or colors.raised, 24)
        widget:buttons(gears.table.join(awful.button({}, 1, function()
            if supported then control(method) end
        end)))
        awful.tooltip({ objects = { widget }, text = title })
        return widget
    end
    local shuffle = music_button("", "Aleatorio", "Shuffle", available and data.shuffle_supported == "1",
        data.shuffle == "1" and colors.green or colors.blue)
    local loop = music_button("󰑖", "Repetir", "Loop", available and data.loop_supported == "1",
        data.loop ~= "None" and colors.green or colors.blue)
    local source = icon("󰎆", 12, colors.pink, 22)
    local top = wibox.widget({ { shuffle, loop, spacing = 3, layout = wibox.layout.fixed.horizontal }, nil,
        source, layout = wibox.layout.align.horizontal })
    local title = text(empty and "Tu música, aquí" or data.title, "Bold 12", colors.text)
    title.wrap, title.ellipsize, title.forced_height = "word", "end", 25
    local artist = text(empty and "Reproduce algo en tu aplicación de música" or data.artist, 9, colors.text)
    artist.ellipsize, artist.forced_height = "end", 22
    local progress = wibox.widget({ max_value = math.max(tonumber(data.length) or 0, 1),
        value = tonumber(data.position) or 0, forced_height = 6,
        color = "#a970ff", background_color = "#9ba3ab88",
        shape = gears.shape.rounded_rect, bar_shape = gears.shape.rounded_rect,
        widget = wibox.widget.progressbar })
    local duration = text(timestamp(data.position) .. " / " .. timestamp(data.length), "Bold Italic 8", colors.blue)
    duration.forced_height = 16
    progress:connect_signal("button::press", function(_, x, _, mouse_button, _, geometry)
        local length = tonumber(data.length) or 0
        if mouse_button ~= 1 or data.seek ~= "1" or length <= 0 or busy or dragging then return end
        local width = geometry.widget_width
        local left = mouse.coords().x - x
        local token = generation
        local position
        local function preview(relative_x)
            position = math.max(0, math.min(1, relative_x / width)) * length
            progress.value = position
            duration.text = timestamp(position) .. " / " .. timestamp(length)
        end
        dragging = true
        preview(x)
        -- Keep the existing bar and preview locally. Seek once on release,
        -- rather than sending player commands for every mouse movement.
        mousegrabber.run(function(state)
            if token ~= generation then dragging = false; return false end
            preview(state.x - left)
            if not state.buttons[1] then
                dragging = false
                gears.timer.delayed_call(function()
                    if token == generation then control("SetPosition", position / 1000000) end
                end)
                return false
            end
            return true
        end, "sb_h_double_arrow")
    end)
    local info = wibox.widget({ top, nil, { title, artist, spacing = 1, layout = wibox.layout.fixed.vertical }, layout = wibox.layout.align.vertical })
    info.forced_height = 105
    local bottom = wibox.widget({ progress, duration, spacing = 4, layout = wibox.layout.fixed.vertical })
    local overlay = margin(wibox.widget({ info, nil, bottom, layout = wibox.layout.align.vertical }), 10, 8)
    if cover_path ~= data.cover then
        cover_path = data.cover
        cover_surface = nil
        if cover_path and cover_path ~= "" then
            local ok, surface = pcall(gears.surface.load_uncached, cover_path)
            if ok then cover_surface = surface end
        end
    end
    local artwork = wibox.widget.base.make_widget(nil, nil, { enable_properties = true })
    artwork.fit = function() return 320, 176 end
    artwork.draw = function(_, _, cr, width, height)
        cr:set_source(gears.color(colors.surface)); cr:paint()
        if cover_surface then
            local iw, ih = gears.surface.get_size(cover_surface)
            local scale = math.max(width / iw, height / ih)
            cr:save()
            cr:translate((width - iw * scale) / 2, (height - ih * scale) / 2)
            cr:scale(scale, scale)
            cr:set_source_surface(cover_surface, 0, 0); cr:paint()
            cr:restore()
        end
        cr:set_source_rgba(0.04, 0.05, 0.07, 0.48); cr:paint()
    end
    local cover = wibox.widget({
        { artwork, overlay, layout = wibox.layout.stack },
        shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 14) end,
        shape_clip = true, widget = wibox.container.background })
    cover.forced_width, cover.forced_height = 320, 176
    local close = icon("󰅙", 12, "#f38ba8", 24)
    close:buttons(gears.table.join(awful.button({}, 1, hide)))
    local pause = music_button(data.state == "Playing" and "󰏤" or "󰐊", data.state == "Playing" and "Pausar" or "Reproducir",
        "PlayPause", available and data.play == "1", colors.text, 17)
    local play_circle = wibox.widget({ wibox.container.place(pause), bg = available and "#7c3aed" or colors.surface,
        forced_width = 40, forced_height = 40, shape = gears.shape.circle, widget = wibox.container.background })
    local transport = wibox.widget({
        wibox.container.place(music_button("󰒮", "Anterior", "Previous", available and data.previous == "1", colors.text, 15)),
        wibox.container.place(play_circle),
        wibox.container.place(music_button("󰒭", "Siguiente", "Next", available and data.next == "1", colors.text, 15)),
        layout = wibox.layout.flex.horizontal })
    transport.forced_height = 44
    local track_title = text(empty and "Sin reproducción" or data.title, 10, colors.text)
    track_title.ellipsize, track_title.forced_height = "end", 22
    local track_artist = text(empty and "Tu música aparecerá aquí" or data.artist, 8, colors.muted)
    track_artist.ellipsize, track_artist.forced_height = "end", 20
    local current = wibox.widget({ margin(wibox.widget({ track_title, track_artist,
        spacing = 2, layout = wibox.layout.fixed.vertical }), 8, 7),
        bg = "#ffffff0c", shape = gears.shape.rounded_rect, widget = wibox.container.background })
    local status = text(empty and "MÚSICA" or (data.state == "Playing" and "REPRODUCIENDO" or "EN PAUSA"), 8, colors.muted)
    local heading_row = wibox.widget({ status, nil, close, layout = wibox.layout.align.horizontal })
    local detail = wibox.widget({ heading_row, current,
        text(empty and "" or data.album, 8, colors.muted), spacing = 8, layout = wibox.layout.fixed.vertical })
    local side = margin(wibox.widget({ detail, nil, transport, layout = wibox.layout.align.vertical }), 8, 5)
    side.forced_width, side.forced_height = 160, 176
    body:add(wibox.widget({ cover, side, spacing = 10, layout = wibox.layout.fixed.horizontal }))

end

refresh = function()
    if busy or dragging or not active then return end
    local token, kind = generation, active
    busy = true
    awful.spawn.easy_async({ helper, kind }, function(stdout, _, _, code)
        if token ~= generation then return end
        busy = false
        if code ~= 0 then
            heading.text = "No se pudo actualizar · Reintentando…"
            return
        end
        heading.text = ""
        local data = parse(stdout)
        if kind == "system" then render_system(data) else render_music(data) end
    end)
end

function M.toggle(kind)
    if kind ~= "system" and kind ~= "music" then return end
    if active == kind then hide(); return end
    hide()
    active = kind
    local s = mouse.screen or awful.screen.focused()
    local anchor = mouse.coords()
    heading = text(kind == "system" and "" or "Música", "Bold 12")
    local close = icon("󰅙", 12, colors.pink, 20)
    close:buttons(gears.table.join(awful.button({}, 1, hide)))
    body = wibox.widget({ text("Cargando…", 10, colors.muted), spacing = 10,
        layout = wibox.layout.fixed.vertical })
    popup = awful.popup({ screen = s, ontop = true, visible = true, type = "dialog",
        bg = colors.base, border_width = 1, border_color = colors.border,
        minimum_width = kind == "system" and 286 or 510,
        maximum_width = kind == "system" and 286 or 510,
        shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 14) end,
        widget = kind == "music" and margin(body, 10, 8) or margin(wibox.widget({
            { heading, nil, close, layout = wibox.layout.align.horizontal }, body,
            spacing = 8, layout = wibox.layout.fixed.vertical }), 10, 10) })

    local below = s.geometry.y + 58
    local music_x = s.geometry.x + 244
    for _, bar in ipairs(client.get()) do
        if bar.class == "Polybar" and bar.screen == s then
            local g = bar:geometry()
            if anchor.x >= g.x and anchor.x <= g.x + g.width then
                below = g.y + g.height + 8
                -- A real bar click supplies the exact module position. During
                -- live reloads, keep the panel beside the music module instead
                -- of following the pointer into an application window.
                music_x = g.x + 225 * g.height / 44
                if anchor.y >= g.y and anchor.y <= g.y + g.height then
                    music_x = anchor.x - 8
                end
                break
            end
        end
    end
    local function place()
        popup.x = math.max(s.geometry.x + 8, math.min(kind == "system" and s.geometry.x + 18
            or music_x, s.geometry.x + s.geometry.width - popup.width - 18))
        popup.y = math.max(s.geometry.y + 8, math.min(below, s.geometry.y + s.geometry.height - popup.height - 8))
    end
    popup:connect_signal("property::width", place)
    popup:connect_signal("property::height", place)
    place()
    if kind == "music" then render_music(last_music_data or { state = "empty" }) end
    refresh()
    if kind == "system" then
        local token = generation
        awful.spawn.easy_async({ helper, "weather" }, function(output)
            if token ~= generation then return end
            weather = parse(output)
            refresh()
        end)
    end
    timer = gears.timer({ timeout = kind == "system" and 3 or 1, autostart = true, callback = refresh })
end

M.hide = hide

function M.geometry()
    if popup then return popup.x, popup.y, popup.width, popup.height end
end

return M
