local awful = require("awful")
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
