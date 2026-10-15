local awful = require("awful")
local gears = require("gears")
local wibox = require("wibox")

local M = {}
local popups = {}
local palette = {
    base = "#181825",
    surface = "#242438",
    raised = "#313244",
    border = "#45475a",
    text = "#cdd6f4",
    muted = "#a6adc8",
    lavender = "#cba6f7",
    green = "#a6e3a1",
    yellow = "#f9e2af",
    red = "#f38ba8",
    blue = "#89dceb",
}

local function escape(value)
    return gears.string.xml_escape(tostring(value or ""))
end

local function label(value, font, color)
    return wibox.widget({
        markup = string.format('<span foreground="%s">%s</span>', color or palette.text, escape(value)),
        font = font or "Lexend 10",
        widget = wibox.widget.textbox,
    })
end

local function shell_quote(value)
    return "'" .. tostring(value):gsub("'", "'\\''") .. "'"
end

local function hide(kind)
    if popups[kind] then popups[kind].visible = false end
end

local function make_popup(kind, title, subtitle, content, width)
    local close = wibox.widget({
        markup = '<span foreground="#a6adc8"></span>',
        font = "JetBrainsMono Nerd Font 14",
        align = "center",
        valign = "center",
        forced_width = 24,
        forced_height = 24,
        widget = wibox.widget.textbox,
    })
    close:buttons(gears.table.join(awful.button({}, 1, function() hide(kind) end)))

    local heading = wibox.widget({
        {
            {
                label(title, "Lexend Bold 12", palette.text),
                label(subtitle, "Lexend 9", palette.muted),
                spacing = 3,
                layout = wibox.layout.fixed.vertical,
            },
            nil,
            close,
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
    local icon_widget = label(icon, "JetBrainsMono Nerd Font 16", accent)
    icon_widget.align = "center"
    icon_widget.valign = "center"
    icon_widget.forced_width = 26
    icon_widget.forced_height = 28

    local text = wibox.widget({
        label(title, "Lexend 10", palette.text),
        label(detail, "Lexend 8", palette.muted),
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
        rows:add(label("¿Seguro que quieres " .. verb .. " el equipo?", "Lexend 10", palette.text))
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

local function network_row(ssid, signal, security, active)
    local details = string.format("%s%%  ·  %s", signal ~= "" and signal or "--", security ~= "" and security or "Abierta")
    local title = active and ("✓  " .. ssid) or ssid
    return action_row("󰤨", title, details, active and palette.green or palette.lavender, function()
        hide("network")
        local command = "nmcli -w 12 device wifi connect " .. shell_quote(ssid)
        awful.spawn.easy_async_with_shell(command .. " 2>&1", function(_, _, _, exit_code)
            if exit_code == 0 then return end
            awful.spawn.easy_async_with_shell("rofi -dmenu -password -p " .. shell_quote("Clave de " .. ssid), function(password)
                password = password:gsub("[\r\n]+$", "")
                if password == "" then return end
                awful.spawn.easy_async_with_shell(
                    command .. " password " .. shell_quote(password) .. " >/dev/null 2>&1",
                    function() end
                )
            end)
        end)
    end)
end

local function network_content(devices, wifi_enabled, networks)
    local rows = wibox.widget({ spacing = 7, layout = wibox.layout.fixed.vertical })
    local interface_count = #devices.ethernet + #devices.wifi

    for _, device in ipairs(devices.ethernet) do
        local connected = device.state == "connected" or device.state:match("^connected ") ~= nil
        local detail = connected and ("Conectado · " .. (device.connection ~= "" and device.connection or device.name)) or "Cable desconectado"
        rows:add(action_row("󰈀", "Ethernet", detail, connected and palette.green or palette.red, function() end))
    end

    for _, device in ipairs(devices.wifi) do
        local connected = device.state == "connected" or device.state:match("^connected ") ~= nil
        local status
        if not wifi_enabled then
            status = "Wi-Fi apagado"
        elseif connected then
            status = "Conectado · " .. (device.ssid ~= "" and device.ssid or device.connection)
        elseif device.state == "unavailable" then
            status = "Adaptador no disponible"
        else
            status = "Sin una red conectada"
        end
        rows:add(action_row("󰤨", "Wi-Fi", status, connected and palette.green or (wifi_enabled and palette.muted or palette.yellow), function() end))
    end

    if interface_count == 0 then
        rows:add(label("No se detectaron adaptadores de red", "Lexend 9", palette.muted))
        return rows
    end

    if #devices.wifi == 0 then
        rows:add(label("No hay adaptador Wi-Fi", "Lexend 9", palette.muted))
        return rows
    end

    rows:add(wibox.widget({ forced_height = 5, widget = wibox.widget.textbox }))
    if wifi_enabled then
        rows:add(label("REDES WI-FI", "Lexend Bold 8", palette.muted))
        rows:add(wibox.widget({ forced_height = 3, widget = wibox.widget.textbox }))
        local count = 0
        for _, network in ipairs(networks) do
            if network.ssid ~= "" and count < 5 then
                rows:add(network_row(network.ssid, network.signal, network.security, network.active))
                count = count + 1
            end
        end
        if count == 0 then rows:add(label("No se encontraron redes", "Lexend 9", palette.muted)) end
    end

    rows:add(wibox.widget({ forced_height = 5, widget = wibox.widget.textbox }))
    rows:add(action_row(wifi_enabled and "󰖪" or "󰖩", wifi_enabled and "Apagar Wi-Fi" or "Encender Wi-Fi", "", wifi_enabled and palette.yellow or palette.green, function()
        awful.spawn.easy_async_with_shell("nmcli radio wifi " .. (wifi_enabled and "off" or "on"), function()
            M.show_network()
        end)
    end))
    return rows
end

function M.show_network()
    hide("network")
    make_popup("network", "Conexiones", "Estado y redes Wi-Fi", label("Revisando adaptadores…", "Lexend 9", palette.muted), 340)

    awful.spawn.easy_async_with_shell("nmcli -t --escape no -f DEVICE,TYPE,STATE,CONNECTION device status 2>/dev/null", function(device_output)
        local devices = { ethernet = {}, wifi = {} }
        for line in device_output:gmatch("[^\r\n]+") do
            local name, kind, state, connection = line:match("^([^:]*):([^:]*):([^:]*):(.*)$")
            if name and (kind == "ethernet" or kind == "wifi") then
                local entry = { name = name, state = state or "unknown", connection = connection or "" }
                if kind == "ethernet" then
                    devices.ethernet[#devices.ethernet + 1] = entry
                else
                    devices.wifi[#devices.wifi + 1] = entry
                end
            end
        end

        awful.spawn.easy_async_with_shell("nmcli -t -f WIFI general status 2>/dev/null", function(wifi_output)
            local wifi_enabled = wifi_output:match("enabled") ~= nil
            local function render(networks)
                if popups.network and popups.network.visible then
                    for _, device in ipairs(devices.wifi) do
                        device.ssid = ""
                        for _, network in ipairs(networks) do
                            if network.active then device.ssid = network.ssid; break end
                        end
                    end
                    hide("network")
                    make_popup("network", "Conexiones", "Estado y redes Wi-Fi", network_content(devices, wifi_enabled, networks), 340)
                end
            end

            if #devices.wifi == 0 or not wifi_enabled then
                render({})
                return
            end

            awful.spawn.easy_async_with_shell(
                "nmcli -t --escape no -f IN-USE,SSID,SIGNAL,SECURITY device wifi list --rescan yes 2>/dev/null",
                function(output)
                    local networks, seen = {}, {}
                    for line in output:gmatch("[^\r\n]+") do
                        local in_use, ssid, signal, security = line:match("^([^:]*):([^:]*):([^:]*):(.*)$")
                        if ssid and ssid ~= "" and not seen[ssid] then
                            seen[ssid] = true
                            networks[#networks + 1] = {
                                ssid = ssid,
                                signal = signal or "",
                                security = security or "",
                                active = in_use == "*" or in_use == "yes",
                            }
                        end
                    end
                    table.sort(networks, function(a, b) return (tonumber(a.signal) or 0) > (tonumber(b.signal) or 0) end)
                    render(networks)
                end
            )
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
