local awful = require("awful")
local gears = require("gears")

-- Alt + Shift and a mouse drag turns the client floating, then moves it.
local floating_client_buttons = gears.table.join(
    awful.button({ "Mod1", "Shift" }, 1, function(c)
        c.floating = true
        c:emit_signal("request::activate", "mouse_click", { raise = true })
        awful.mouse.client.move(c)
    end)
)

return {
    {
        rule = {},
        properties = {
            border_width = 2,
            border_color = "#242438",
            focus = awful.client.focus.filter,
            raise = true,
            screen = awful.screen.preferred,
            placement = awful.placement.no_overlap + awful.placement.no_offscreen,
            buttons = floating_client_buttons,
        },
    },
    {
        rule_any = { type = { "dock" }, class = { "Polybar" } },
        properties = {
            border_width = 0,
            focusable = false,
            floating = true,
            ontop = true,
            skip_taskbar = true,
        },
    },
    {
        rule_any = {
            type = { "dialog", "utility", "toolbar", "splash" },
            class = { "Gpick", "flameshot" },
        },
        properties = { floating = true, placement = awful.placement.centered },
    },
    { rule = { class = "Firefox" }, properties = { tag = "󰊢" } },
    { rule = { class = "Alacritty" }, properties = { tag = "" } },
}
