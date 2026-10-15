local beautiful = require("beautiful")

beautiful.init({
    font = "Lexend 10",
    mono_font = "JetBrainsMono Nerd Font 10",
    bg_normal = "#1e1e2e",
    bg_focus = "#45475a",
    bg_urgent = "#f38ba8",
    bg_minimize = "#181825",
    fg_normal = "#cdd6f4",
    fg_focus = "#cdd6f4",
    fg_urgent = "#11111b",
    fg_minimize = "#a6adc8",
    border_width = 2,
    border_normal = "#242438",
    border_focus = "#cba6f7",
    border_marked = "#f5c2e7",
    useless_gap = 10,
    notification_font = "Lexend 10",
    notification_bg = "#242438",
    notification_fg = "#cdd6f4",
    notification_border_color = "#cba6f7",
})

return beautiful
