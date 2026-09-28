local hardware = require("lua.hardware")
local effects_enabled = not hardware.vmware

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
        rounding = effects_enabled and 10 or 0,
        shadow = {
            -- Shadows and blur are disproportionately expensive on virtual
            -- GPUs and do not improve usability.
            enabled = false,
        },
        blur = {
            enabled = false,
        },
    },
    animations = {
        -- VMware's compositor path has very little frame-time headroom. Make
        -- every action immediate there while retaining effects on real GPUs.
        enabled = effects_enabled,
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
hl.animation({ leaf = "windows", enabled = true, speed = 7, bezier = "ease-out", style = "popin 96%" })
hl.animation({ leaf = "windowsMove", enabled = true, speed = 7, bezier = "ease-in-out" })
hl.animation({ leaf = "fade", enabled = true, speed = 8, bezier = "ease-out" })
hl.animation({ leaf = "layers", enabled = true, speed = 7, bezier = "ease-out", style = "fade" })
hl.animation({ leaf = "border", enabled = true, speed = 8, bezier = "ease-out" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 7, bezier = "ease-in-out", style = "slide" })
