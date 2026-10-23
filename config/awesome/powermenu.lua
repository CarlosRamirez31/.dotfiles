local awful = require("awful")
local gears = require("gears")
local wibox = require("wibox")
local widgets = require("widgets")

local dashboard

local function text(markup, font)
    return wibox.widget({ markup = markup, font = font or "JetBrainsMono Nerd Font Medium 10", widget = wibox.widget.textbox })
end

local function card(child)
    return wibox.widget({
        child,
        bg = "#242438",
        shape = gears.shape.rounded_rect,
        widget = wibox.container.background,
    })
end

local function button(icon, label, color, callback)
    local body = wibox.widget({
        {
            text(string.format('<span foreground="%s">%s</span>', color, icon), "JetBrainsMono Nerd Font 10"),
            text(string.format('<span foreground="#cdd6f4">%s</span>', label), "JetBrainsMono Nerd Font Medium 9"),
            spacing = 8,
            layout = wibox.layout.fixed.horizontal,
        },
        left = 11,
        right = 11,
        top = 7,
        bottom = 7,
        widget = wibox.container.margin,
    })
    local widget = wibox.widget({ body, bg = "#313244", shape = gears.shape.rounded_rect, widget = wibox.container.background })
    widget:buttons(gears.table.join(awful.button({}, 1, callback)))
    return widget
end

local function spawn(command)
    return function() awful.spawn.with_shell(command) end
end

local function build(screen)
    local heading = wibox.widget({
        text('<span foreground="#f5c2e7">Dashboard</span><span foreground="#a6adc8">  ·  Awesome X11</span>', "JetBrainsMono Nerd Font Bold 14"),
        bottom = 10,
        widget = wibox.container.margin,
    })
    local time = wibox.widget.textclock("%I:%M %p")
    time.font = "JetBrainsMono Nerd Font Bold 28"
    local date = wibox.widget.textclock("%A, %d de %B")
    date.font = "JetBrainsMono Nerd Font Medium 9"
    local profile = card({
        {
            {
                text('<span foreground="#89dceb">󰀄</span>', "JetBrainsMono Nerd Font 11"),
                text('<span foreground="#cdd6f4">beambollow</span>', "JetBrainsMono Nerd Font Medium 10"),
                spacing = 8,
                layout = wibox.layout.fixed.horizontal,
            },
            time,
            date,
            spacing = 4,
            layout = wibox.layout.fixed.vertical,
        },
        left = 16,
        right = 16,
        top = 12,
        bottom = 12,
        widget = wibox.container.margin,
    })

    local apps = wibox.layout.fixed.vertical()
    apps.spacing = 8
    apps:add(button("󰆍", "Terminal", "#89dceb", spawn("dotfiles-terminal")))
    apps:add(button("󰈹", "Firefox", "#f9e2af", spawn("firefox")))
    apps:add(button("󰉋", "Archivos", "#a6e3a1", spawn("thunar")))
    apps:add(button("󰘔", "Aplicaciones", "#cba6f7", spawn("dotfiles-app-launcher")))

    local status = wibox.layout.fixed.vertical()
    status.spacing = 9
    status:add(text('<span foreground="#a6adc8">ESTADO DEL SISTEMA</span>', "JetBrainsMono Nerd Font Medium 8"))
    status:add(widgets.volume())
    status:add(widgets.network())
    status:add(widgets.memory())
    status:add(widgets.cpu())

    local session = wibox.layout.fixed.horizontal()
    session.spacing = 8
    session:add(button("󰌾", "Bloquear", "#89dceb", spawn("$HOME/.local/bin/dotfiles-lock")))
    session:add(button("󰒲", "Suspender", "#cba6f7", function()
        dashboard.visible = false
        awful.spawn.with_shell("$HOME/.local/bin/dotfiles-sleep")
    end))
    session:add(button("󰍃", "Salir", "#f9e2af", function() awesome.quit() end))
    session:add(button("󰜉", "Reiniciar", "#fab387", spawn("systemctl reboot")))
    session:add(button("󰐥", "Apagar", "#f38ba8", spawn("systemctl poweroff")))

    local content = wibox.widget({
        heading,
        {
            {
                profile,
                { apps, top = 12, widget = wibox.container.margin },
                layout = wibox.layout.fixed.vertical,
            },
            {
                card({
                    status,
                    left = 14,
                    right = 14,
                    top = 14,
                    bottom = 14,
                    widget = wibox.container.margin,
                }),
                forced_width = 175,
                widget = wibox.container.constraint,
            },
            spacing = 10,
            layout = wibox.layout.fixed.horizontal,
        },
        { session, top = 10, widget = wibox.container.margin },
        layout = wibox.layout.fixed.vertical,
    })

    dashboard = awful.popup({
        screen = screen,
        ontop = true,
        visible = true,
        type = "dialog",
        bg = "#181825",
        border_width = 1,
        border_color = "#45475a",
        shape = gears.shape.rounded_rect,
        placement = awful.placement.centered,
        widget = {
            content,
            left = 18,
            right = 18,
            top = 16,
            bottom = 16,
            widget = wibox.container.margin,
        },
    })
end

return function()
    if dashboard then
        dashboard.visible = not dashboard.visible
    else
        build(awful.screen.focused())
    end
end
