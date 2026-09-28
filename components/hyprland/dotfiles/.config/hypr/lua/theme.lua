local hardware = require("lua.hardware")
local effects_enabled = not hardware.vmware
local animation_speed = hardware.vmware and 18 or 7
local fade_speed = hardware.vmware and 20 or 8
local workspace_speed = hardware.vmware and 16 or 7
local window_style = hardware.vmware and "popin 99%" or "popin 96%"

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
        -- Keep motion feedback in VMware, but make it brief enough that its
        -- virtual GPU does not make the desktop feel delayed.
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
hl.animation({ leaf = "windows", enabled = true, speed = animation_speed, bezier = "ease-out", style = window_style })
hl.animation({ leaf = "windowsMove", enabled = true, speed = animation_speed, bezier = "ease-in-out" })
hl.animation({ leaf = "fade", enabled = true, speed = fade_speed, bezier = "ease-out" })
hl.animation({ leaf = "layers", enabled = true, speed = animation_speed, bezier = "ease-out", style = "fade" })
hl.animation({ leaf = "border", enabled = true, speed = fade_speed, bezier = "ease-out" })
hl.animation({ leaf = "workspaces", enabled = true, speed = workspace_speed, bezier = "ease-in-out", style = "slide" })
