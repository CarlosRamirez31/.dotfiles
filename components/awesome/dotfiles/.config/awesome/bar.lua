local awful = require("awful")
local beautiful = require("beautiful")
local gears = require("gears")
local wibox = require("wibox")
local widgets = require("widgets")
local powermenu = require("powermenu")

return function(s)
    local taglist = awful.widget.taglist({ screen = s, filter = awful.widget.taglist.filter.all })
    local title = wibox.widget.textbox()
    local function update_title()
        local focused = client.focus
        if focused and focused.screen == s then
            title.text = focused.name or ""
        else
            title.text = ""
        end
    end

    client.connect_signal("focus", update_title)
    client.connect_signal("unfocus", update_title)
    client.connect_signal("property::name", function(c)
        if client.focus == c then update_title() end
    end)

    local clock = wibox.widget.textclock("󰥔 %a %d %b  %H:%M")
    local menu = wibox.widget({ markup = " 󰀻 ", widget = wibox.widget.textbox })
    menu:buttons(gears.table.join(awful.button({}, 1, powermenu)))
    local separator = wibox.widget({ markup = "  ", widget = wibox.widget.textbox })
    local geometry = s.geometry
    s.wibar = awful.wibar({
        position = "top",
        screen = s,
        height = 36,
        width = geometry.width - 28,
        x = geometry.x + 14,
        y = geometry.y + 8,
        bg = beautiful.bg_normal,
        shape = gears.shape.rounded_rect,
    })
    s.wibar:setup({
        layout = wibox.layout.align.horizontal,
        {
            layout = wibox.layout.fixed.horizontal,
            menu,
            wibox.container.margin(title, 8, 12, 0, 0),
            widgets.htb(),
        },
        taglist,
        {
            layout = wibox.layout.fixed.horizontal,
            widgets.volume(),
            separator,
            widgets.network(),
            separator,
            widgets.memory(),
            separator,
            widgets.cpu(),
            separator,
            clock,
            separator,
            wibox.widget.systray(),
        },
    })
    update_title()
end
