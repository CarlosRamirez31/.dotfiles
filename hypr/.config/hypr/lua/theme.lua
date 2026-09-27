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
        rounding = 10,
        shadow = {
            enabled = true,
            range = 14,
            render_power = 2,
            color = 0x44000000,
        },
        blur = {
            enabled = true,
            size = 3,
            passes = 2,
            new_optimizations = true,
            ignore_opacity = true,
        },
    },
    animations = {
        enabled = true,
    },
})

hl.curve("ease-out", {
    type = "bezier",
    points = {{0.22, 1}, {0.36, 1}},
})

hl.curve("ease-in-out", {
    type = "bezier",
    points = {{0.65, 0}, {0.35, 1}},
})

-- Short, calm transitions: noticeable enough to feel polished without slowing
-- down keyboard-driven navigation.
hl.animation({ leaf = "windows", enabled = true, speed = 2.5, bezier = "ease-out", style = "popin 92%" })
hl.animation({ leaf = "windowsMove", enabled = true, speed = 2.5, bezier = "ease-in-out" })
hl.animation({ leaf = "fade", enabled = true, speed = 2, bezier = "ease-out" })
hl.animation({ leaf = "layers", enabled = true, speed = 2.5, bezier = "ease-out", style = "slide top" })
hl.animation({ leaf = "border", enabled = true, speed = 2.5, bezier = "ease-out" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 3, bezier = "ease-in-out", style = "slide" })

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
