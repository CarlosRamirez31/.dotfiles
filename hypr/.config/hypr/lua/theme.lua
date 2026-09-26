-- Effective values from the previous profound theme, without its dead duplicates.
hl.config({
    general = {
        gaps_in = 3,
        gaps_out = 5,
        border_size = 2,
        col = {
            active_border = "rgb(cba6f7)",
            inactive_border = "rgb(24273A)",
        },
    },
    decoration = {
        rounding = 0,
        shadow = {
            enabled = true,
            range = 30,
            color = 0x44000000,
        },
        blur = {
            enabled = true,
            size = 4,
            passes = 4,
            new_optimizations = true,
            ignore_opacity = true,
            xray = false,
        },
    },
    animations = {
        enabled = true,
    },
})

local curves = {
    linear = {{0, 0}, {1, 1}},
    md3_standard = {{0.2, 0}, {0, 1}},
    md3_decel = {{0.05, 0.5}, {0.1, 1}},
    md3_accel = {{0.3, 0}, {0.6, 0.15}},
    overshot = {{0.05, 0.9}, {0.1, 1.1}},
    crazyshot = {{0.1, 1.2}, {0.76, 0.92}},
    hyprnostretch = {{0.05, 0.9}, {0.1, 1.0}},
    menu_decel = {{0.1, 1}, {0, 1}},
    menu_accel = {{0.38, 0.04}, {1, 0.07}},
    easeInOutCirc = {{0.85, 0}, {0.15, 1}},
    easeOutCirc = {{0, 0.55}, {0.45, 1}},
    easeOutExpo = {{0.16, 1}, {0.3, 1}},
    softAcDecel = {{0.26, 0.26}, {0.15, 1}},
    md2 = {{0.4, 0}, {0.2, 1}},
    liner = {{1, 1}, {1, 1}},
}

for name, points in pairs(curves) do
    hl.curve(name, { type = "bezier", points = points })
end

hl.animation({ leaf = "windows", enabled = true, speed = 3, bezier = "md3_decel", style = "popin 60%" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 3, bezier = "md3_decel", style = "popin 60%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 3, bezier = "md3_accel", style = "popin 60%" })
hl.animation({ leaf = "border", enabled = true, speed = 0.5, bezier = "liner" })
hl.animation({ leaf = "fade", enabled = true, speed = 5, bezier = "md3_decel" })
hl.animation({ leaf = "layersIn", enabled = true, speed = 4, bezier = "menu_decel", style = "slide" })
hl.animation({ leaf = "layersOut", enabled = true, speed = 1.6, bezier = "menu_accel" })
hl.animation({ leaf = "fadeLayersIn", enabled = true, speed = 1, bezier = "menu_decel" })
hl.animation({ leaf = "fadeLayersOut", enabled = true, speed = 2.5, bezier = "menu_accel" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 5, bezier = "menu_decel", style = "slide" })
