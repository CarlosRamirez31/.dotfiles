local awful = require("awful")
local gears = require("gears")
local wibox = require("wibox")
local menu_style = require("menu-style")

local M = {}
local popups = {}
local network_view
local network_host
local network_spinner
local network_busy = false
local network_generation = 0
local network_timer
local network_page = 1
local password_grabber
local palette = menu_style.colors

local function escape(value)
    return gears.string.xml_escape(tostring(value or ""))
end

local function label(value, font, color)
    return wibox.widget({
        markup = string.format('<span foreground="%s">%s</span>', color or palette.text, escape(value)),
        font = font or "JetBrainsMono Nerd Font Bold 10",
        widget = wibox.widget.textbox,
    })
end


local function hide(kind)
    if kind == "network" then
        network_generation = network_generation + 1
        network_busy = false
        network_view = nil
        if network_spinner then network_spinner:stop(); network_spinner = nil end
    end
    if kind == "network" and network_timer then network_timer:stop(); network_timer = nil end
    if kind == "network" and password_grabber then
        awful.keygrabber.stop(password_grabber)
        password_grabber = nil
    end
    if popups[kind] then popups[kind].visible = false end
end

local function make_popup(kind, title, subtitle, content, width)
    if kind == "network" and popups.network and popups.network.visible then
        network_host:set_widget(content)
        return popups.network
    end
    if kind == "network" then
        network_host = wibox.container.background(content)
        content = network_host
    end
    local close = menu_style.icon("󰅙", 14, palette.red, 24, 24)
    close:buttons(gears.table.join(awful.button({}, 1, function() hide(kind) end)))

    local controls = wibox.widget({ spacing = 12, layout = wibox.layout.fixed.horizontal })
    if kind == "network" then
        local power = menu_style.icon("⏻", 16, palette.lavender, 26, 28)
        power.forced_width = 26
        power.align = "center"
        power:buttons(gears.table.join(awful.button({}, 1, function()
            if not network_view then return end
            awful.spawn.easy_async({ "nmcli", "radio", "wifi", network_view.wifi_enabled and "off" or "on" }, function() M.show_network() end)
        end)))
        awful.tooltip({ objects = { power }, text = "Encender / apagar Wi-Fi" })
        controls:add(power)
    end
    controls:add(close)
    local heading = wibox.widget({
        {
            {
                label(title, "JetBrainsMono Nerd Font Bold 12", palette.blue),
                label(subtitle, "JetBrainsMono Nerd Font Medium 9", palette.muted),
                spacing = 3,
                layout = wibox.layout.fixed.vertical,
            },
            nil,
            controls,
            layout = wibox.layout.align.horizontal,
        },
        bottom = 12,
        widget = wibox.container.margin,
    })

    local body = wibox.widget({
        heading,
        content,
        spacing = 0,
        layout = wibox.layout.fixed.vertical,
    })
    local popup = awful.popup({
        screen = awful.screen.focused(),
        ontop = true,
        visible = true,
        type = "dialog",
        bg = palette.base,
        border_width = 1,
        border_color = palette.border,
        shape = gears.shape.rounded_rect,
        minimum_width = width,
        maximum_width = width,
        widget = {
            body,
            left = 16,
            right = 16,
            top = 14,
            bottom = 14,
            widget = wibox.container.margin,
        },
    })
    local screen = awful.screen.focused()
    popup.x = screen.geometry.x + screen.geometry.width - width - 18
    popup.y = screen.geometry.y + 42
    popups[kind] = popup
    return popup
end

local function action_row(icon, title, detail, accent, callback)
    local icon_widget = menu_style.icon(icon, 16, accent, 28, 30)
    icon_widget.align = "center"
    icon_widget.valign = "center"
    icon_widget.forced_width = 28
    icon_widget.forced_height = 30

    local text = wibox.widget({
        label(title, "JetBrainsMono Nerd Font Bold 10", palette.text),
        label(detail, "JetBrainsMono Nerd Font Medium 8", palette.muted),
        spacing = 2,
        layout = wibox.layout.fixed.vertical,
    })
    local row = wibox.widget({
        {
            icon_widget,
            text,
            spacing = 12,
            layout = wibox.layout.fixed.horizontal,
        },
        left = 12,
        right = 12,
        top = 9,
        bottom = 9,
        widget = wibox.container.margin,
    })
    local background = wibox.widget({
        row,
        bg = palette.surface,
        shape = gears.shape.rounded_rect,
        widget = wibox.container.background,
    })
    background:connect_signal("mouse::enter", function(widget) widget.bg = palette.raised end)
    background:connect_signal("mouse::leave", function(widget) widget.bg = palette.surface end)
    background:buttons(gears.table.join(awful.button({}, 1, callback)))
    return background
end

local function power_content(confirm_kind)
    local rows = wibox.widget({ spacing = 7, layout = wibox.layout.fixed.vertical })
    if confirm_kind then
        local verb = confirm_kind == "shutdown" and "apagar" or "reiniciar"
        rows:add(label("¿Seguro que quieres " .. verb .. " el equipo?", "JetBrainsMono Nerd Font Bold 10", palette.text))
        rows:add(wibox.widget({ forced_height = 8, widget = wibox.widget.textbox }))
        rows:add(action_row("󰄬", "Sí, " .. verb, "Confirmar acción", palette.red, function()
            hide("power")
            awful.spawn.with_shell(confirm_kind == "shutdown" and "systemctl poweroff" or "systemctl reboot")
        end))
        rows:add(action_row("󰜺", "Cancelar", "Volver al menú", palette.muted, function() M.show_power() end))
        return rows
    end

    rows:add(action_row("󰌾", "Bloquear", "Cerrar la sesión visual", palette.blue, function()
        hide("power")
        awful.spawn.with_shell("$HOME/.local/bin/dotfiles-lock")
    end))
    rows:add(action_row("󰒲", "Suspender", "Pausar el equipo y conservar las aplicaciones", palette.lavender, function()
        hide("power")
        awful.spawn.with_shell("$HOME/.local/bin/dotfiles-sleep")
    end))
    rows:add(action_row("󰋊", "Hibernar", "Guardar la sesión en disco y apagar el equipo", palette.blue, function()
        hide("power")
        awful.spawn.easy_async({ "systemctl", "hibernate" }, function(_, stderr, _, code)
            if code ~= 0 then
                require("naughty").notify({
                    preset = require("naughty").config.presets.critical,
                    title = "No se pudo hibernar",
                    text = stderr,
                })
            end
        end)
    end))
    rows:add(action_row("󰍃", "Cerrar sesión", "Salir de AwesomeWM", palette.yellow, function()
        hide("power")
        awesome.quit()
    end))
    rows:add(action_row("󰜉", "Reiniciar", "Volver a iniciar el equipo", palette.lavender, function()
        M.show_power("reboot")
    end))
    rows:add(action_row("󰐥", "Apagar", "Apagar el equipo", palette.red, function()
        M.show_power("shutdown")
    end))
    return rows
end

function M.show_power(confirm_kind)
    hide("power")
    make_popup("power", confirm_kind and "Confirmar acción" or "Energía", "Sesión y apagado", power_content(confirm_kind), 290)
end

local function show_network_detail(network)
    network_generation = network_generation + 1
    network_busy = false
    if network_timer then network_timer:stop(); network_timer = nil end
    if network_spinner then network_spinner:stop(); network_spinner = nil end
    network_view = nil
    local rows = wibox.widget({ spacing = 9, layout = wibox.layout.fixed.vertical })
    local password = ""
    local busy = false
    local message = label(network.uuid and "Red guardada · Conecta o escribe una nueva contraseña" or "Introduce la contraseña de la red", "JetBrainsMono Nerd Font Medium 9", palette.muted)
    rows:add(label(network.ssid, "JetBrainsMono Nerd Font Bold 12", palette.lavender))
    rows:add(message)
    local input = label("Pulsa aquí para escribir la contraseña", "JetBrainsMono Nerd Font Bold 10", palette.text)
    local function update_input()
        input.text = password == "" and "Escribe la contraseña…" or string.rep("●", utf8.len(password) or #password)
    end
    local field = wibox.widget({ input, margins = 12, widget = wibox.container.margin })
    field = wibox.widget({ field, bg = palette.surface, shape = gears.shape.rounded_rect, widget = wibox.container.background })
    local function edit()
        if busy or password_grabber then return end
        update_input()
        password_grabber = awful.keygrabber.run(function(modifiers, key, event)
            if event == "release" then return end
            if key == "Escape" or key == "Return" then
                awful.keygrabber.stop(password_grabber)
                password_grabber = nil
            elseif key == "space" then
                password = password .. " "
                update_input()
            elseif key == "BackSpace" then
                local offset = utf8.offset(password, -1)
                if offset then password = password:sub(1, offset - 1) end
                update_input()
            elseif not gears.table.hasitem(modifiers, "Control") and not gears.table.hasitem(modifiers, "Mod1") and utf8.len(key) == 1 then
                password = password .. key
                update_input()
            end
        end)
    end
    field:buttons(gears.table.join(awful.button({}, 1, edit)))
    if network.security ~= "" and network.security ~= "--" then rows:add(field) end
    rows:add(action_row("󰄬", "Conectar", network.uuid and "Usar la conexión guardada" or "Guardar y conectar a esta red", palette.green, function()
        if busy then return end
        local args
        if network.uuid and password == "" then
            args = { "nmcli", "--wait", "25", "connection", "up", "uuid", network.uuid }
        else
            args = { "nmcli", "--wait", "25", "device", "wifi", "connect", network.ssid }
            if network.security ~= "" and network.security ~= "--" then
                if password == "" then message.text = "Escribe la contraseña antes de conectar"; edit(); return end
                args[#args + 1] = "password"
                args[#args + 1] = password
            end
        end
        if password_grabber then awful.keygrabber.stop(password_grabber); password_grabber = nil end
        busy = true
        message.text = "Conectando…"
        awful.spawn.easy_async(args, function(_, _, _, code)
            busy = false
            password = ""
            update_input()
            message.text = code == 0 and "Conectado correctamente" or "No se pudo conectar. Revisa la contraseña o la disponibilidad."
        end)
    end))
    rows:add(action_row("󰜱", "Volver a las redes", "", palette.blue, function() M.show_network() end))
    make_popup("network", "Conexiones", "Conectar a Wi-Fi", rows, 370)
end

local function network_content()
    local view = { wifi_enabled = true, networks = {}, devices = {}, signature = "", connection_signature = "" }
    local rows = wibox.widget({ spacing = 9, layout = wibox.layout.fixed.vertical })
    local refresh = label("󰜉", "JetBrainsMono Nerd Font 18", palette.blue)
    refresh.align = "center"
    refresh.forced_width = 38
    refresh:buttons(gears.table.join(awful.button({}, 1, function() M.show_network(true) end)))
    awful.tooltip({ objects = { refresh }, text = "Actualizar redes" })
    view.status = label("Wi-Fi", "JetBrainsMono Nerd Font Bold 10")
    rows:add(view.status)
    view.connection = wibox.container.background()
    rows:add(view.connection)
    rows:add(wibox.widget({ label("REDES DISPONIBLES", "JetBrainsMono Nerd Font Bold 8", palette.muted), nil, refresh, layout = wibox.layout.align.horizontal }))
    view.spinner = wibox.widget.base.make_widget(nil, nil, { enable_properties = true })
    view.spinner.fit = function() return 24, 24 end
    view.spinner.forced_width = 24
    view.spinner.forced_height = 24
    view.phase = 0
    view.spinner.draw = function(_, _, cr, width, height)
        local radius = math.min(width, height) / 2 - 3
        for index = 0, 11 do
            local angle = (index / 12) * 2 * math.pi - math.pi / 2
            local alpha = 0.15 + ((index - view.phase) % 12) / 11 * 0.85
            cr:set_source_rgba(0.796, 0.651, 0.969, alpha)
            cr:arc(width / 2 + math.cos(angle) * radius, height / 2 + math.sin(angle) * radius, 1.8, 0, 2 * math.pi)
            cr:fill()
        end
    end
    view.loading = wibox.container.place(view.spinner, "center", "center")
    view.loading.forced_height = 32
    view.loading.visible = false
    rows:add(view.loading)
    view.list = wibox.container.background()
    rows:add(view.list)
    view.widget = rows
    return view
end

local function render_connection(view)
    local ethernet, wifi
    for _, device in ipairs(view.devices) do
        if device.state == "connected" then
            if device.kind == "ethernet" then ethernet = device else wifi = device end
        end
    end
    view.ethernet = ethernet
    view.status.text = view.wifi_enabled and "Wi-Fi encendido" or "Wi-Fi apagado"
    local connected = ethernet or wifi
    local signature = connected and (connected.name .. connected.connection) or "none"
    if view.connection_signature == signature then return end
    view.connection_signature = signature
    view.connection:set_widget(connected and action_row(ethernet and "󰈀" or "󰤨", connected.connection,
        ethernet and "Ethernet · Conectado · Pulsa para desconectar" or "Wi-Fi · Conectada · Pulsa para desconectar", palette.green, function()
            awful.spawn.easy_async({ "nmcli", "device", "disconnect", connected.name }, function() M.show_network(true) end)
        end) or nil)
end

local function render_networks(view, scan_error)
    local available, signature = {}, {}
    for _, network in ipairs(view.networks) do
        if network.available and (view.ethernet or not network.active) then
            available[#available + 1] = network
            signature[#signature + 1] = table.concat({network.ssid, network.signal, network.security, network.uuid or ""}, "\t")
        end
    end
    network_page = math.min(network_page, math.max(1, math.ceil(#available / 5)))
    local key = table.concat(signature, "\n") .. network_page .. tostring(scan_error)
    view.empty = #available == 0
    view.list.visible = true
    if view.signature == key then return end
    view.signature = key
    local rows = wibox.widget({ spacing = 7, layout = wibox.layout.fixed.vertical })
    for index = (network_page - 1) * 5 + 1, math.min(network_page * 5, #available) do
        local network = available[index]
        rows:add(action_row("󰤨", network.ssid, network.signal .. "% · " .. network.security .. (network.uuid and " · Guardada" or ""), palette.lavender, function() show_network_detail(network) end))
    end
    if #available == 0 then
        local message = not view.wifi_enabled and "Wi-Fi apagado o adaptador no disponible. Pulsa ⏻ para activarlo."
            or (scan_error and "No se pudo buscar redes. Pulsa Actualizar para volver a intentarlo."
                or "No hay redes disponibles. Pulsa Actualizar para buscar de nuevo.")
        rows:add(label(message, "JetBrainsMono Nerd Font Medium 9", palette.muted))
    end
    if network_page > 1 then rows:add(action_row("󰜱", "Redes anteriores", "", palette.blue, function() network_page = network_page - 1; render_networks(view, scan_error) end)) end
    if #available > network_page * 5 then rows:add(action_row("󰜴", "Más redes", "", palette.blue, function() network_page = network_page + 1; render_networks(view, scan_error) end)) end
    view.list:set_widget(rows)
end

function M.show_network(refresh)
    if not network_view or not popups.network or not popups.network.visible then
        network_page = 1
        network_view = network_content()
        make_popup("network", "Conexiones", "Estado de Wi-Fi", network_view.widget, 370)
    end
    if network_busy then return end
    network_busy = true
    local view = network_view
    local generation = network_generation
    local popup = popups.network
    local function valid() return network_generation == generation and network_view == view and popup.visible end
    if not network_timer then
        network_timer = gears.timer({ timeout = 10, autostart = true, callback = function() M.show_network() end })
    end
    view.loading.visible = true
    if view.empty then view.list.visible = false end
    network_spinner = gears.timer({ timeout = 0.065, autostart = true, callback = function()
        view.phase = (view.phase + 1) % 12
        view.spinner:emit_signal("widget::redraw_needed")
    end })
    awful.spawn.easy_async_with_shell("LC_ALL=C nmcli -t --escape no -f DEVICE,TYPE,STATE,CONNECTION device status", function(device_output)
        if not valid() then return end
        local devices, networks, seen = {}, {}, {}
        local wifi_enabled = false
        for line in device_output:gmatch("[^\r\n]+") do
            local name, kind, state, connection = line:match("^([^:]*):([^:]*):([^:]*):(.*)$")
            if kind == "wifi" or kind == "ethernet" then
                devices[#devices + 1] = { name = name, kind = kind, state = state, connection = connection ~= "" and connection or state }
                if kind == "wifi" and state ~= "unavailable" then wifi_enabled = true end
            end
        end
        view.devices = devices
        view.wifi_enabled = wifi_enabled
        render_connection(view)
        local scan = "LC_ALL=C nmcli --wait 10 -t --escape no -f IN-USE,SSID,SIGNAL,SECURITY device wifi list --rescan " .. (refresh and "yes" or "auto")
        awful.spawn.easy_async_with_shell(scan, function(output, _, _, scan_code)
            if not valid() then return end
            for line in output:gmatch("[^\r\n]+") do
                local active, ssid, signal, security = line:match("^([^:]*):(.*):(%d+):([^:]*)$")
                if ssid and ssid ~= "" and not seen[ssid] then
                    local network = { ssid = ssid, signal = signal, security = security, active = active == "*", available = true }
                    networks[#networks + 1] = network
                    seen[ssid] = network
                end
            end
            awful.spawn.easy_async_with_shell("LC_ALL=C nmcli -t -f UUID,TYPE connection show", function(profiles)
                if not valid() then return end
                local uuids = {}
                for line in profiles:gmatch("[^\r\n]+") do
                    local uuid = line:match("^([^:]+):802%-11%-wireless$")
                    if uuid then uuids[#uuids + 1] = uuid end
                end
                local remaining = #uuids
                local function render()
                    if not valid() then return end
                    table.sort(networks, function(a, b)
                        if (a.uuid ~= nil) ~= (b.uuid ~= nil) then return a.uuid ~= nil end
                        if a.available ~= b.available then return a.available == true end
                        return (tonumber(a.signal) or 0) > (tonumber(b.signal) or 0)
                    end)
                    view.networks = networks
                    render_networks(view, scan_code ~= 0)
                    network_busy = false
                    if network_spinner then network_spinner:stop(); network_spinner = nil end
                    view.loading.visible = false
                end
                if remaining == 0 then render(); return end
                for _, uuid in ipairs(uuids) do
                    awful.spawn.easy_async({ "nmcli", "--escape", "no", "-g", "802-11-wireless.ssid", "connection", "show", "uuid", uuid }, function(value)
                        local ssid = value:gsub("[\r\n]+$", "")
                        if ssid ~= "" then
                            if seen[ssid] then seen[ssid].uuid = uuid else
                                local network = { ssid = ssid, uuid = uuid, signal = "", security = "", active = false, available = false }
                                networks[#networks + 1] = network
                                seen[ssid] = network
                            end
                        end
                        remaining = remaining - 1
                        if remaining == 0 then render() end
                    end)
                end
            end)
        end)
    end)
end

function M.toggle(kind)
    if kind == "network" then
        if popups.network and popups.network.visible then hide("network") else M.show_network() end
    else
        if popups.power and popups.power.visible then hide("power") else M.show_power() end
    end
end

return M
