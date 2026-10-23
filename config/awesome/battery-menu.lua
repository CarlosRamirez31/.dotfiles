local awful = require("awful")
local gears = require("gears")
local wibox = require("wibox")
local menu_style = require("menu-style")

local M = {}
local popup, current, content, message
local busy = false
local generation = 0
local timer
local colors = menu_style.colors
local styles = {
    bright = { "󰓅", "#fab387" }, balanced = { "󰾅", "#f9e2af" },
    ["balanced-60"] = { "󰾆", "#89b4fa" },
    ["save-fluid"] = { "", "#a6e3a1" }, ["save-max"] = { "󰁹", "#94e2d5" },
}
local helper = os.getenv("HOME") .. "/.local/bin/dotfiles-power-profile"

local function text(value, font, color)
    return wibox.widget({
        markup = string.format('<span foreground="%s">%s</span>', color or colors.text,
            gears.string.xml_escape(tostring(value))),
        font = font or "JetBrainsMono Nerd Font Bold 10", widget = wibox.widget.textbox,
    })
end

local function margin(widget, horizontal, vertical)
    return wibox.widget({ widget, left = horizontal, right = horizontal,
        top = vertical, bottom = vertical, widget = wibox.container.margin })
end

local function read(path)
    local file = io.open(path)
    if not file then return nil end
    local value = file:read("*l")
    file:close()
    return value
end

local function parse(output)
    local result = { profiles = {} }
    for line in output:gmatch("[^\n]+") do
        local fields = {}
        for value in line:gmatch("[^\t]+") do fields[#fields + 1] = value end
        if fields[1] == "STATUS" then
            result.capacity, result.watts, result.state = tonumber(fields[2]), tonumber(fields[3]), fields[4]
            result.brightness, result.hz = tonumber(fields[5]), tonumber(fields[6])
            result.active, result.energy, result.minutes = fields[7], fields[8], tonumber(fields[9])
        elseif fields[1] == "PROFILE" then
            result.profiles[#result.profiles + 1] = {
                id = fields[2], title = fields[3], detail = fields[4],
                measured = fields[5], available = fields[6] == "1",
            }
        end
    end
    if not result.active or #result.profiles == 0 then return nil end
    return result
end

local function hide()
    generation = generation + 1
    if popup then popup.visible = false end
    if timer then timer:stop(); timer = nil end
end

local render
local function apply(profile)
    if busy or not profile.available then return end
    busy = true
    local token = generation
    render(current, "Aplicando «" .. profile.title .. "»…")
    awful.spawn.easy_async(profile.command or { helper, "apply", profile.id, "--tsv" }, function(stdout, stderr, _, code)
        busy = false
        if token ~= generation or not popup or not popup.visible then return end
        local data = code == 0 and parse(stdout) or nil
        if data then
            current = data
            render(data, "Perfil aplicado")
        else
            render(current, (stderr:gsub("[\r\n]+$", "")), true)
        end
    end)
end

local function profile_card(profile, data)
    local selected = profile.id == data.active
    local style = styles[profile.id]
    local accent = style[2]
    local titles = wibox.widget({
        text(profile.title, "JetBrainsMono Nerd Font Bold 10", selected and accent or colors.text),
        text(profile.detail, "JetBrainsMono Nerd Font Medium 8", colors.muted),
        spacing = 4, layout = wibox.layout.fixed.vertical,
    })
    local badge = text(profile.measured, "JetBrainsMono Nerd Font Medium 8", accent)
    badge.align = "right"
    local check = menu_style.icon(selected and "󰄬" or "○", 12, selected and accent or colors.border, 24, 24)
    check.align = "right"
    local trailing = wibox.widget({ check, badge, spacing = 3, layout = wibox.layout.fixed.vertical })
    local icon = menu_style.icon(style[1], 19, accent, 33, 34)
    icon.forced_width = 33
    icon.valign = "center"
    local card = wibox.widget({
        margin(wibox.widget({
            { icon, titles, spacing = 10, layout = wibox.layout.fixed.horizontal },
            nil, trailing, layout = wibox.layout.align.horizontal,
        }), 13, 11),
        bg = selected and "#2d2840" or colors.surface,
        border_width = selected and 1 or 0,
        border_color = accent,
        shape = function(cr, width, height) gears.shape.rounded_rect(cr, width, height, 12) end,
        widget = wibox.container.background,
    })
    card.opacity = (busy or not profile.available) and 0.5 or 1
    card:connect_signal("mouse::enter", function(widget)
        if not busy and profile.available then widget.bg = colors.raised end
    end)
    card:connect_signal("mouse::leave", function(widget)
        widget.bg = selected and "#2d2840" or colors.surface
    end)
    card:buttons(gears.table.join(awful.button({}, 1, function() apply(profile) end)))
    return card
end

render = function(data, notice, failed)
    if not content then return end
    content:reset()
    if not data then
        content:add(text(notice or "Leyendo el estado de energía…", "JetBrainsMono Nerd Font Medium 10", colors.muted))
        return
    end
    local saving = data.energy == "power-saver"
    local battery = text((data.capacity or "—") .. "%", "JetBrainsMono Nerd Font Bold 24")
    local power = data.watts and string.format("%.1f W ahora", data.watts) or
        (data.state == "Charging" and "Cargando" or "Conectado a corriente")
    local active_title = "Personalizado"
    for _, profile in ipairs(data.profiles) do
        if profile.id == data.active then active_title = profile.title end
    end
    local summary = wibox.widget({
        { battery, nil, text(saving and "  AHORRO ACTIVO" or "󰚥  EQUILIBRADO",
            "JetBrainsMono Nerd Font 9", saving and colors.green or colors.blue),
            layout = wibox.layout.align.horizontal },
        { text(power, "JetBrainsMono Nerd Font Medium 10", colors.blue), nil, text(active_title, "JetBrainsMono Nerd Font Medium 9", colors.muted),
            layout = wibox.layout.align.horizontal },
        spacing = 5, layout = wibox.layout.fixed.vertical,
    })
    local progress = wibox.widget({ max_value = 100, value = data.capacity or 0,
        forced_height = 5, color = saving and colors.green or colors.lavender,
        background_color = colors.raised, shape = gears.shape.rounded_rect,
        bar_shape = gears.shape.rounded_rect, widget = wibox.widget.progressbar })
    local overview = wibox.widget({ summary, progress, spacing = 12, layout = wibox.layout.fixed.vertical })
    content:add(wibox.widget({ margin(overview, 14, 12), bg = colors.surface,
        shape = gears.shape.rounded_rect, widget = wibox.container.background }))
    local toggle_title = saving and "Desactivar modo ahorro de batería" or "Activar modo ahorro de batería"
    local toggle = wibox.widget({
        margin(text(toggle_title, "JetBrainsMono Nerd Font Bold 10", saving and colors.blue or colors.green), 14, 11),
        bg = colors.raised, shape = gears.shape.rounded_rect,
        widget = wibox.container.background,
    })
    toggle.opacity = busy and 0.5 or 1
    toggle:buttons(gears.table.join(awful.button({}, 1, function()
        apply({ available = true, title = toggle_title,
            command = { helper, saving and "saving-off" or "saving-on", "--tsv" } })
    end)))
    content:add(toggle)
    content:add(margin(text("MAYOR CONSUMO  ↓  MAYOR AUTONOMÍA", "JetBrainsMono Nerd Font Bold 8", colors.muted), 2, 5))
    for _, profile in ipairs(data.profiles) do content:add(profile_card(profile, data)) end
    content:add(margin(text("Los Hz de estos perfiles son los de la laptop.\nReferencias medidas sin monitores externos.",
        "JetBrainsMono Nerd Font Medium 8", colors.muted), 2, 4))
    if notice and notice ~= "" then
        message = text(notice, "JetBrainsMono Nerd Font Medium 8", failed and colors.red or colors.green)
        message.wrap = "word_char"
        message.forced_width = 380
        content:add(message)
    end
end

local function refresh()
    if busy then return end
    local token = generation
    awful.spawn.easy_async({ helper, "status", "--tsv" }, function(stdout, stderr, _, code)
        if token ~= generation or not popup or not popup.visible then return end
        current = code == 0 and parse(stdout) or nil
        render(current, current and nil or stderr:gsub("[\r\n]+$", ""), not current)
    end)
end

function M.show()
    generation = generation + 1
    if timer then timer:stop() end
    if popup then popup.visible = false end
    content = wibox.layout.fixed.vertical()
    content.spacing = 7
    local close = menu_style.icon("󰅙", 14, colors.red, 24, 24)
    close.forced_width, close.align, close.valign = 24, "center", "center"
    close:buttons(gears.table.join(awful.button({}, 1, hide)))
    local reload = menu_style.icon("󰜉", 15, colors.blue, 24, 24)
    reload.forced_width, reload.align, reload.valign = 24, "center", "center"
    reload:buttons(gears.table.join(awful.button({}, 1, refresh)))
    local controls = wibox.widget({ reload, close, spacing = 16, layout = wibox.layout.fixed.horizontal })
    local heading = wibox.widget({
        { text("Batería y energía", "JetBrainsMono Nerd Font Bold 13", colors.blue),
          text("Elige cómo quieres trabajar", "JetBrainsMono Nerd Font Medium 9", colors.muted),
          spacing = 4, layout = wibox.layout.fixed.vertical },
        nil, controls, layout = wibox.layout.align.horizontal,
    })
    local anchor = mouse.coords()
    local screen = mouse.screen or awful.screen.focused()
    popup = awful.popup({
        screen = screen, ontop = true, visible = true, type = "dialog",
        bg = colors.base, border_width = 1, border_color = colors.border,
        shape = function(cr, width, height) gears.shape.rounded_rect(cr, width, height, 14) end,
        minimum_width = 440, maximum_width = 440,
        widget = margin(wibox.widget({ heading, content, spacing = 16,
            layout = wibox.layout.fixed.vertical }), 18, 16),
    })
    local below_bar = screen.geometry.y + math.floor(screen.geometry.height * 0.005) + 52
    for _, bar in ipairs(client.get()) do
        if bar.class == "Polybar" and bar.screen == screen then
            local geometry = bar:geometry()
            if anchor.x >= geometry.x and anchor.x <= geometry.x + geometry.width then
                below_bar = geometry.y + geometry.height + 8
                break
            end
        end
    end
    local function place()
        popup.x = math.max(screen.geometry.x + 8, math.min(anchor.x - popup.width / 2,
            screen.geometry.x + screen.geometry.width - popup.width - 8))
        popup.y = math.max(screen.geometry.y + 8, math.min(below_bar,
            screen.geometry.y + screen.geometry.height - popup.height - 8))
    end
    popup:connect_signal("property::width", place)
    popup:connect_signal("property::height", place)
    place()
    render(nil)
    refresh()
    -- Only refresh battery telemetry while open. Never poll XRandR on a timer.
    timer = gears.timer({ timeout = 5, autostart = true, callback = function()
        if not current or busy then return end
        local base = "/sys/class/power_supply/BAT1/"
        current.capacity = tonumber(read(base .. "capacity"))
        current.state = read(base .. "status")
        current.watts = current.state == "Discharging" and (tonumber(read(base .. "power_now")) or 0) / 1000000 or nil
        render(current)
    end })
end

function M.toggle()
    if popup and popup.visible then hide() else M.show() end
end

function M.geometry()
    if popup then return popup.x, popup.y, popup.width, popup.height end
end

return M
