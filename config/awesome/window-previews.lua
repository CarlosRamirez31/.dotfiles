local awful = require("awful")
local gears = require("gears")
local wibox = require("wibox")
local lgi = require("lgi")
local cairo = lgi.cairo
local colors = require("menu-style").colors
local app_label = require("polybar-tags").render_app

local M = {}
local snapshots = setmetatable({}, { __mode = "k" })
local function rounded(cr, width, height) gears.shape.rounded_rect(cr, width, height, 14) end
local function overlay()
    return wibox({ visible = false, ontop = true, input_passthrough = true, type = "dialog",
        bg = colors.base, fg = colors.text, shape = rounded, border_width = 1, border_color = colors.lavender })
end
local preview, switcher = overlay(), overlay()
local function text(value, color, size)
    return wibox.widget({ markup = '<span foreground="' .. color .. '">' .. gears.string.xml_escape(value) .. "</span>",
        font = "JetBrainsMono Nerd Font Bold " .. size, ellipsize = "end", valign = "center",
        widget = wibox.widget.textbox })
end
local function title(c)
    return app_label(c, c.screen):gsub("\n$", "")
end
local function eligible(c)
    return c.valid and c.focusable and not c.skip_taskbar
        and c.type ~= "desktop" and c.type ~= "dock" and c.type ~= "splash"
end

local function remember(c)
    if not eligible(c) or c.minimized or c.hidden then return end
    local source = gears.surface.load_uncached(c.content)
    local width, height = gears.surface.get_size(source)
    if width < 1 or height < 1 then return end
    local scale = math.min(1, 320 / width, 200 / height)
    local image = cairo.ImageSurface.create(cairo.Format.ARGB32,
        math.max(1, math.ceil(width * scale)), math.max(1, math.ceil(height * scale)))
    local cr = cairo.Context(image)
    cr:scale(scale, scale)
    cr:set_source_surface(source, 0, 0)
    cr:paint()
    if cr.status == "SUCCESS" then snapshots[c] = image end
end

local function remember_tag(t)
    if t.selected then return end
    -- Awesome emits this signal before X11 unmaps the departing windows.
    for _, c in ipairs(t:clients()) do remember(c) end
end

local function remember_visible(c)
    if c.valid and c:isvisible() then remember(c) end
end

local function paint(cr, c, width, height, stretch)
    cr:save()
    cr:rectangle(0, 0, width, height)
    cr:clip()
    cr:set_source(gears.color(colors.raised))
    cr:paint()
    local content = c:isvisible() and not c.minimized and gears.surface.load_uncached(c.content)
        or snapshots[c]
    local surface = content or (c.icon and gears.surface(c.icon))
    if surface then
        local sw, sh = gears.surface.get_size(surface)
        if sw > 0 and sh > 0 then
            local sx, sy = width / sw, height / sh
            if not (stretch and content) then
                local limit = content and math.huge or 1
                sx = math.min(sx, sy, limit, content and math.huge or .55 * height / sh)
                sy = sx
            end
            cr:translate((width - sw * sx) / 2, (height - sh * sy) / 2)
            cr:scale(sx, sy)
            cr:set_source_surface(surface, 0, 0)
            cr:paint()
        end
    end
    cr:restore()
end

local function canvas(width, height, draw)
    local widget = wibox.widget.base.make_widget(nil, nil, { enable_properties = true })
    widget.forced_width, widget.forced_height = width, height
    widget.fit = function() return width, height end
    widget.draw = function(_, _, cr, w, h)
        if w > 1 and h > 1 then draw(cr, w, h) end
    end
    return widget
end

local function show_workspace(bar, t, center)
    local s = bar.screen
    local area = s.workarea
    local clients = {}
    local tagged = {}
    for _, c in ipairs(t:clients()) do tagged[c] = true end
    for _, c in ipairs(client.get(s, true)) do
        if tagged[c] and eligible(c) and not c.minimized then clients[#clients + 1] = c end
    end
    local width = math.min(226, area.width - 30)
    local height = math.min(138, math.floor(width * area.height / area.width))
    local scene = canvas(width, height, function(cr, w, h)
        cr:set_source(gears.color(colors.surface))
        cr:paint()
        for i = #clients, 1, -1 do
            local c = clients[i]
            if c.valid then
                local g = c:geometry()
                local sx, sy = w / area.width, h / area.height
                cr:save()
                cr:translate((g.x - area.x) * sx, (g.y - area.y) * sy)
                paint(cr, c, g.width * sx, g.height * sy, true)
                cr:set_source(gears.color(colors.border))
                cr:rectangle(0, 0, g.width * sx, g.height * sy)
                cr:stroke()
                cr:restore()
            end
        end
    end)
    local label = #clients == 0 and "Empty" or (#clients == 1 and title(clients[1]) or (#clients .. " windows"))
    preview.widget = wibox.widget({ {
        { text("Workspace " .. t.name, colors.lavender, 10), nil, text(label, colors.muted, 9),
            forced_height = 18, layout = wibox.layout.align.horizontal },
        scene, spacing = 8, layout = wibox.layout.fixed.vertical },
        margins = 10, widget = wibox.container.margin })
    local screen_geo, bar_geo = s.geometry, bar:geometry()
    preview.screen = s
    preview:geometry({ x = math.max(screen_geo.x + 8, math.min(center - width / 2 - 10,
        screen_geo.x + screen_geo.width - width - 30)), y = bar_geo.y + bar_geo.height + 7,
        width = width + 20, height = height + 46 })
    preview.visible = true
end

local active_bar, metrics, hovered, ticks
local hover_timer
local function hide_preview()
    hovered, ticks = nil, 0
    preview.visible = false
end
local function check_pointer()
    local bar = active_bar
    if not bar or not bar.valid or mouse.current_client ~= bar then
        active_bar, metrics = nil, nil
        hover_timer:stop()
        hide_preview()
        return
    end
    if not metrics then return end
    local g, pointer = bar:geometry(), mouse.coords()
    local index = math.floor((pointer.x - g.x - metrics.left) / metrics.cell) + 1
    local t = bar.screen.tags[index]
    if not t or switcher.visible then hide_preview(); return end
    if t ~= hovered then hide_preview(); hovered = t end
    ticks = ticks + 1
    if ticks == 3 then show_workspace(bar, t, g.x + metrics.left + (index - .5) * metrics.cell) end
end
hover_timer = gears.timer({ timeout = .065, callback = check_pointer })

local function enter_bar(bar)
    if bar.class ~= "Polybar" then return end
    active_bar, metrics = bar, nil
    hide_preview()
    hover_timer:again()
    local output = (bar.name or ""):match("^polybar%-%a+_(.+)$")
    if not output then return end
    local helper = os.getenv("HOME") .. "/.local/bin/dotfiles-polybar-style"
    awful.spawn.easy_async({ helper, output }, function(values, _, _, code)
        if active_bar ~= bar or not bar.valid or code ~= 0 then return end
        local regular = tonumber(values:match("POLYBAR_FONT_0=[^\n]*:size=([%d.]+)"))
        local powerline = tonumber(values:match("POLYBAR_FONT_2=[^\n]*:size=([%d.]+)"))
        if not regular or not powerline then return end
        local cairo, pango = lgi.cairo, lgi.Pango
        local layout = lgi.PangoCairo.create_layout(cairo.Context(cairo.ImageSurface.create(cairo.Format.ARGB32, 1, 1)))
        local function advance(font, size, label)
            local desc = pango.FontDescription.from_string(font)
            desc:set_absolute_size(math.floor(size * 96 / 72 + .5) * pango.SCALE)
            layout:set_font_description(desc)
            layout:set_text(label, -1)
            return layout:get_pixel_size()
        end
        local font = "JetBrainsMono Nerd Font Bold"
        -- Matches the left padding, filesystem button and round-left cap
        -- preceding xworkspaces in the Polybar configuration.
        local left = advance(font, regular, "    ")
            + advance("Iosevka Nerd Font", powerline, " ")
        metrics = { left = left, cell = advance(font, regular, " 1 ") }
    end)
end

function M.start()
    if M.started then return end
    M.started = true
    client.connect_signal("mouse::enter", enter_bar)
    tag.connect_signal("property::selected", remember_tag)
    client.connect_signal("unfocus", remember_visible)
    for _, c in ipairs(client.get()) do remember_visible(c) end
    local hovered_client = mouse.current_client
    if hovered_client then enter_bar(hovered_client) end
end

local windows, selected, target
local function render_switcher()
    local area = target.workarea
    local max_cards = math.max(1, math.min(6, math.floor((area.width - 44) / 128)))
    local count = math.min(max_cards, #windows)
    local first = math.max(1, math.min(selected - math.floor(count / 2), #windows - count + 1))
    local width = math.max(78, math.min(168, math.floor((area.width - 40 - 8 * (count - 1)) / count)))
    local cards = wibox.layout.fixed.horizontal()
    cards.spacing = 8
    for index = first, first + count - 1 do
        local c = windows[index]
        local image = canvas(width - 14, 89, function(cr, w, h)
            if c.valid then paint(cr, c, w, h) end
        end)
        local label = text(c.valid and ((c.name and c.name ~= "") and c.name or title(c)) or "",
            index == selected and colors.lavender or colors.muted, 9)
        label.forced_height = 19
        local app_icon = c.valid and c.icon
        local glyph = app_icon and wibox.widget({ image = gears.surface(app_icon), resize = true,
            forced_width = 14, forced_height = 14, widget = wibox.widget.imagebox })
            or require("menu-style").icon("󰣆", 10, colors.muted, 14)
        local caption = wibox.widget({ { glyph, right = 5, widget = wibox.container.margin },
            label, nil, forced_height = 19, layout = wibox.layout.align.horizontal })
        cards:add(wibox.widget({ { { image, caption, spacing = 4, layout = wibox.layout.fixed.vertical },
                margins = 7, widget = wibox.container.margin },
            forced_width = width, bg = colors.surface, shape = rounded,
            shape_border_width = 1, shape_border_color = index == selected and colors.lavender or colors.border,
            widget = wibox.container.background }))
    end
    local footer = text(count < #windows and (selected .. " / " .. #windows) or "", colors.muted, 9)
    footer.align, footer.forced_height = "center", count < #windows and 18 or 0
    switcher.widget = wibox.widget({ { cards, footer, layout = wibox.layout.fixed.vertical },
        margins = 10, widget = wibox.container.margin })
    local total = count * width + (count - 1) * 8 + 20
    local height = 146 + footer.forced_height
    switcher.screen = target
    switcher:geometry({ x = area.x + math.floor((area.width - total) / 2),
        y = area.y + math.floor((area.height - height) / 2), width = total, height = height })
    switcher.visible = true
end

local function cycle(step)
    selected = (selected - 1 + step) % #windows + 1
    render_switcher()
end
local grabber = awful.keygrabber({
    stop_key = "Mod1", stop_event = "release", timeout = 10,
    keypressed_callback = function(self, mods, key)
        if key == "Escape" or key == "Return" then self:stop(key)
        elseif key == "Left" or key == "ISO_Left_Tab" then cycle(-1)
        elseif key == "Right" then cycle(1)
        elseif key == "Tab" then cycle(gears.table.hasitem(mods, "Shift") and -1 or 1) end
    end,
    stop_callback = function(_, key)
        local chosen = windows and windows[selected]
        windows, selected = nil, nil
        switcher.visible = false
        if chosen and chosen.valid and (key == "Alt_L" or key == "Alt_R" or key == "Return") then
            chosen:jump_to()
        end
    end,
})

function M.switch(reverse)
    if windows then cycle(reverse and -1 or 1); return end
    target = awful.screen.focused()
    local ordered, seen = {}, {}
    local function add(c)
        if c and eligible(c) and not seen[c] then
            ordered[#ordered + 1], seen[c] = c, true
        end
    end
    add(client.focus)
    for _, c in ipairs(awful.client.focus.history.list) do add(c) end
    for _, c in ipairs(client.get()) do add(c) end
    if #ordered == 0 then return end
    if #ordered == 1 then ordered[1]:jump_to(); return end
    if grabber:start() == false then return end
    windows = ordered
    selected = reverse and #windows or (client.focus == windows[1] and 2 or 1)
    hide_preview()
    render_switcher()
end

return M
