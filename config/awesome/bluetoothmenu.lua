local awful = require("awful")
local gears = require("gears")
local wibox = require("wibox")
local menu_style = require("menu-style")

local M = { version = 3 }
local popup, body, timer, session, grabber
local generation, page = 0, 1
local loading, dispatching, busy = false, false, false
local view, last_output, request_key = "saved", nil, nil
local backend = os.getenv("HOME") .. "/.local/bin/dotfiles-polybar-bluetooth"
local colors = menu_style.colors

local function text(value, font, color)
    return wibox.widget({
        markup = string.format('<span foreground="%s">%s</span>', color or colors.text,
            gears.string.xml_escape(value)),
        font = font or "JetBrainsMono Nerd Font Bold 10", ellipsize = "end", widget = wibox.widget.textbox,
    })
end

local function stop_input()
    if grabber then awful.keygrabber.stop(grabber); grabber = nil end
end

local function end_session(token)
    if token then awful.spawn({ backend, "--session", token, "--stop" }, false) end
end

function M.close()
    generation = generation + 1
    loading, dispatching, busy = false, false, false
    stop_input()
    if timer then timer:stop(); timer = nil end
    end_session(session)
    session = nil
    if popup then popup.visible = false end
end

local function row(icon, title, detail, color, callback)
    local glyph = menu_style.icon(icon, 18, color, 30, 32)
    glyph.forced_width = 30
    glyph.align = "center"
    local widget = wibox.widget({
        {
            {
                glyph,
                { text(title), text(detail, "JetBrainsMono Nerd Font Medium 8", colors.muted), spacing = 3,
                  layout = wibox.layout.fixed.vertical },
                spacing = 12, layout = wibox.layout.fixed.horizontal,
            },
            margins = 12, widget = wibox.container.margin,
        },
        bg = colors.surface,
        shape = function(cr, width, height) gears.shape.rounded_rect(cr, width, height, 12) end,
        widget = wibox.container.background,
    })
    widget:connect_signal("mouse::enter", function() widget.bg = colors.raised end)
    widget:connect_signal("mouse::leave", function() widget.bg = colors.surface end)
    widget:buttons(gears.table.join(awful.button({}, 1, callback)))
    return widget
end

local refresh, render
local function action(arguments)
    if not session or dispatching then return end
    if busy and arguments[1] ~= "--answer" and arguments[1] ~= "--cancel" then return end
    dispatching = true
    local current = generation
    local command = { backend, "--session", session }
    for _, argument in ipairs(arguments) do command[#command + 1] = argument end
    awful.spawn.easy_async(command, function()
        if generation ~= current or not popup.visible then return end
        dispatching = false
        refresh()
    end)
end

local function switch(target, scan)
    if busy then return end
    stop_input()
    view, page = target, 1
    if last_output then render(last_output, true) end
    if scan then action({ "--scan" }) end
end

local function tabs()
    local tabs_widget = wibox.widget({ spacing = 8, layout = wibox.layout.flex.horizontal })
    for _, tab in ipairs({ { "saved", "󰂱  Mis dispositivos" }, { "nearby", "󰂴  Vincular" } }) do
        local title = text(tab[2], "JetBrainsMono Nerd Font Medium 9", view == tab[1] and colors.lavender or colors.muted)
        title.align = "center"
        local pill = wibox.widget({
            { title, margins = 10, widget = wibox.container.margin },
            bg = view == tab[1] and colors.raised or colors.surface,
            shape = gears.shape.rounded_rect, widget = wibox.container.background,
        })
        pill:buttons(gears.table.join(awful.button({}, 1, function() switch(tab[1], tab[1] == "nearby") end)))
        tabs_widget:add(pill)
    end
    return tabs_widget
end

local function pairing_request(rows, kind, code, name, id)
    rows:add(text(name, "JetBrainsMono Nerd Font Bold 12", colors.lavender))
    if kind == "confirm" or kind == "display" then
        rows:add(text(kind == "confirm" and "¿Coincide este código en ambos dispositivos?"
            or "Escribe este código en el otro dispositivo y pulsa Enter.", "JetBrainsMono Nerd Font Medium 9", colors.muted))
        local passkey = text(#code == 6 and (code:sub(1, 3) .. " " .. code:sub(4)) or code, "JetBrainsMono Nerd Font Bold 26", colors.blue)
        passkey.align = "center"
        rows:add(wibox.widget({ { passkey, margins = 14, widget = wibox.container.margin }, bg = colors.surface,
            shape = gears.shape.rounded_rect, widget = wibox.container.background }))
    end
    if kind == "pin" or kind == "passkey" then
        rows:add(text("Introduce el código mostrado por el dispositivo.", "JetBrainsMono Nerd Font Medium 9", colors.muted))
        local input, value = text("Pulsa aquí para escribir el código", "JetBrainsMono Nerd Font Bold 12", colors.blue), ""
        local function submit()
            if #value == 0 then return end
            stop_input()
            action({ "--answer", id .. ":" .. value })
        end
        local field = row("󰌌", "Código de vinculación", "Pulsa para escribir", colors.blue, function()
            if grabber then return end
            grabber = awful.keygrabber.run(function(modifiers, key, event)
                if event == "release" then return end
                if key == "Escape" then stop_input(); action({ "--cancel" }); return end
                if key == "Return" then submit(); return end
                if key == "BackSpace" then
                    local offset = utf8.offset(value, -1)
                    if offset then value = value:sub(1, offset - 1) end
                elseif not gears.table.hasitem(modifiers, "Control") and not gears.table.hasitem(modifiers, "Mod1")
                    and not gears.table.hasitem(modifiers, "Mod4") and #key == 1 and #value < (kind == "passkey" and 6 or 16)
                    and (kind ~= "passkey" or key:match("%d")) then
                    value = value .. key
                end
                input.text = value == "" and "Escribe el código…" or value
            end)
        end)
        rows:add(field)
        rows:add(input)
        rows:add(row("󰄬", "Confirmar código", "Enviar al dispositivo", colors.green, submit))
    elseif kind == "confirm" or kind == "authorize" then
        rows:add(row("󰄬", kind == "confirm" and "Sí, coincide · Vincular" or "Permitir vinculación",
            "Confirmar este dispositivo", colors.green, function() action({ "--answer", id .. ":yes" }) end))
    end
end

render = function(output, force)
    local kind, code, name, id = output:match("request\t([^\t\r\n]+)\t([^\t\r\n]*)\t([^\t\r\n]+)\t([^\r\n]+)")
    if grabber and request_key == id then return end
    if not force and output == last_output then return end
    stop_input()
    request_key, last_output = id, output
    busy = output:match("busy\t1") ~= nil
    local level, message = output:match("message\t([^\t\r\n]+)\t([^\r\n]+)")
    if not busy and view == "nearby" and message and message:lower():find("vinculado", 1, true) then
        view, page = "saved", 1
    end
    local state = output:match("state\t([^\r\n]+)") or "error"
    local scanning = output:match("scan\t1") ~= nil
    local devices = {}
    for address, connected, group, alias in output:gmatch("device\t([^\t\r\n]+)\t([01])\t([^\t\r\n]+)\t([^\r\n]+)") do
        if group == view then devices[#devices + 1] = { address = address, connected = connected == "1", name = alias } end
    end
    local rows = wibox.widget({ spacing = 10, layout = wibox.layout.fixed.vertical })
    if state == "on" or state == "off" then
        rows:add(row(state == "on" and "" or "󰂲", "Bluetooth " .. (state == "on" and "encendido" or "apagado"),
            state == "on" and "Pulsa para apagar" or "Pulsa para encender", state == "on" and colors.blue or colors.muted,
            function() action({ "--toggle" }) end))
    elseif state == "starting" then
        rows:add(text("Preparando Bluetooth…", "JetBrainsMono Nerd Font Bold 10", colors.blue))
    else
        rows:add(text(state == "unavailable" and "No hay un adaptador Bluetooth disponible."
            or "No se pudo acceder al servicio Bluetooth.", "JetBrainsMono Nerd Font Medium 9", colors.red))
    end
    rows:add(tabs())
    if message then rows:add(text(message, "JetBrainsMono Nerd Font Medium 9", level == "error" and colors.red or (level == "success" and colors.green or colors.blue))) end
    if kind then pairing_request(rows, kind, code, name, id) end
    if busy then
        rows:add(row("󰜺", "Cancelar", "Detener la operación actual", colors.red, function() stop_input(); action({ "--cancel" }) end))
    elseif state == "on" then
        rows:add(text(view == "nearby" and (scanning and "󰔟  BUSCANDO DISPOSITIVOS…" or "DISPOSITIVOS CERCANOS")
            or "TUS DISPOSITIVOS", "JetBrainsMono Nerd Font Bold 8", colors.muted))
        page = math.max(1, math.min(page, math.ceil(#devices / 4)))
        for index = (page - 1) * 4 + 1, math.min(page * 4, #devices) do
            local device = devices[index]
            rows:add(row(device.connected and "󰂱" or "", device.name,
                view == "nearby" and "Disponible · Pulsa para vincular" or (device.connected and "Conectado · Pulsa para desconectar" or "Guardado · Pulsa para conectar"),
                device.connected and colors.green or colors.lavender, function()
                    action({ view == "nearby" and "--pair" or (device.connected and "--disconnect" or "--connect"), device.address })
                end))
        end
        if #devices == 0 then
            rows:add(text(view == "nearby" and "Activa el modo de vinculación de tu dispositivo."
                or "Tus dispositivos aparecerán aquí al vincularlos.", "JetBrainsMono Nerd Font Medium 9", colors.muted))
        end
        if page > 1 then rows:add(row("󰜱", "Anteriores", "", colors.blue, function() page = page - 1; render(output, true) end)) end
        if #devices > page * 4 then rows:add(row("󰜴", "Más dispositivos", "", colors.blue, function() page = page + 1; render(output, true) end)) end
    end
    if not busy then
        rows:add(row("󰂴", view == "nearby" and (scanning and "Buscando…" or "Buscar de nuevo") or "Vincular dispositivo",
            "Auriculares, teclados y otros dispositivos", colors.blue, function() switch("nearby", true) end))
    end
    body:set_widget(rows)
end

refresh = function()
    if loading or not session or not popup or not popup.visible then return end
    loading = true
    local current = generation
    awful.spawn.easy_async({ backend, "--session", session, "--snapshot" }, function(output)
        if generation ~= current or not popup.visible then return end
        loading = false
        render(output)
    end)
end

function M.toggle()
    if popup and popup.visible then M.close(); return end
    M.close()
    page, view, last_output, request_key = 1, "saved", nil, nil
    body = wibox.container.background(text("Cargando dispositivos…", "JetBrainsMono Nerd Font Bold 10", colors.muted))
    local controls = wibox.widget({ spacing = 12, layout = wibox.layout.fixed.horizontal })
    for _, button in ipairs({ { "󰜉", function() if view == "nearby" then action({ "--scan" }) else refresh() end end, "Actualizar" }, { "󰅙", M.close, "Cerrar" } }) do
        local glyph = menu_style.icon(button[1], 16, button[3] == "Cerrar" and colors.red or colors.blue, 25, 28)
        glyph.forced_width = 25
        glyph.align = "center"
        glyph:buttons(gears.table.join(awful.button({}, 1, button[2])))
        awful.tooltip({ objects = { glyph }, text = button[3] })
        controls:add(glyph)
    end
    local heading = wibox.widget({
        { text("Bluetooth", "JetBrainsMono Nerd Font Bold 13", colors.blue), text("Tus conexiones, en un solo lugar", "JetBrainsMono Nerd Font Medium 9", colors.muted),
          spacing = 4, layout = wibox.layout.fixed.vertical },
        nil, controls, layout = wibox.layout.align.horizontal,
    })
    popup = awful.popup({
        screen = awful.screen.focused(), ontop = true, visible = true, type = "dialog",
        bg = colors.base, border_width = 1, border_color = colors.border,
        shape = gears.shape.rounded_rect, minimum_width = 410, maximum_width = 410,
        widget = {
            { heading, body, spacing = 16, layout = wibox.layout.fixed.vertical },
            margins = 18, widget = wibox.container.margin,
        },
    })
    local screen = awful.screen.focused()
    popup.x = screen.geometry.x + screen.geometry.width - 428
    popup.y = screen.geometry.y + 46
    local current = generation
    awful.spawn.easy_async({ backend, "--open" }, function(output, _, _, status)
        local token = output:match("^([0-9a-f]+)")
        if generation ~= current or not popup.visible then end_session(token); return end
        if status ~= 0 or not token or #token ~= 32 then
            body:set_widget(text("No se pudo abrir Bluetooth. Vuelve a intentarlo.", "JetBrainsMono Nerd Font Medium 9", colors.red))
            return
        end
        session = token
        refresh()
        timer = gears.timer({ timeout = 1, autostart = true, callback = refresh })
    end)
end

return M
