local beautiful = require("beautiful")
dpi = require("beautiful.xresources").apply_dpi
beautiful.transparent = "#00000000"
beautiful.xbackground = "#1e1e2e"
beautiful.xforeground = "#d9e0ee"
beautiful.xcolor0 = "#6e6c7e"
beautiful.xcolor1 = "#f28fad"
beautiful.xcolor2 = "#abe9b3"
beautiful.xcolor3 = "#fae3b0"
beautiful.xcolor4 = "#96cdfb"
beautiful.accent = beautiful.xcolor4
beautiful.wibar_bg = "#1a1826"
beautiful.wibar_widget_bg = "#302d41"
beautiful.font_name = "Iosevka "
beautiful.icon_font_name = "Material Icons "
beautiful.font = beautiful.font_name .. "Regular 8"
beautiful.icon_font = beautiful.icon_font_name .. "18"
beautiful.font_taglist = beautiful.icon_font_name .. "16"
beautiful.bg_dark = beautiful.wibar_bg
beautiful.bg_normal = beautiful.xbackground
beautiful.bg_focus = beautiful.xbackground
beautiful.bg_urgent = beautiful.xbackground
beautiful.bg_minimize = beautiful.xbackground
beautiful.fg_normal = beautiful.xforeground
beautiful.fg_focus = beautiful.accent
beautiful.fg_urgent = beautiful.xcolor1
beautiful.fg_minimize = beautiful.xcolor0
beautiful.border_width = dpi(0)
beautiful.battery_happy_color = "#abe9b3"
beautiful.battery_sad_color = "#f28fad"
beautiful.battery_ok_color = "#fae3b0"
beautiful.battery_charging_color = "#f5c2e7"
beautiful.systray_icon_size = 15
beautiful.border_radius = 10
beautiful.useless_gap = 5

-- The upstream bar uses Awesome's themed layout glyphs.  The local theme did
-- not define them, so layoutbox fell back to the literal word "tile".
local default_theme = dofile(require("gears.filesystem").get_themes_dir() .. "default/theme.lua")
default_theme = require("beautiful.theme_assets").recolor_layout(default_theme, beautiful.xforeground)
for name, value in pairs(default_theme) do
    if name:match("^layout_") then
        beautiful[name] = value
    end
end
modkey = "Mod1"
-- The visible panel is ZProger's Polybar menu.  Keep this bridge inert so
-- Awesome does not create a second wibar underneath it.
return function() end
