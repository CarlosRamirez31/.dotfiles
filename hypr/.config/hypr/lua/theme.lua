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
        },
    },
    animations = {
        enabled = true,
    },
})

hl.curve("smooth", {
    type = "bezier",
    points = {{0.2, 0}, {0, 1}},
})

hl.animation({ leaf = "windows", enabled = true, speed = 4, bezier = "smooth", style = "popin 85%" })
hl.animation({ leaf = "fade", enabled = true, speed = 4, bezier = "smooth" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 4, bezier = "smooth", style = "slide" })

-- Keep the terminal usable without letting a single window cover the wallpaper.
hl.window_rule({
    name = "floating-ghostty",
    match = {
        class = "^com.mitchellh.ghostty$",
    },
    float = true,
    center = true,
    size = { "monitor_w * 0.72", "monitor_h * 0.72" },
    rounding = 10,
})
