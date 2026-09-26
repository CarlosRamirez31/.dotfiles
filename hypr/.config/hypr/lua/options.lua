hl.config({
    general = {
        resize_on_border = false,
        allow_tearing = false,
        layout = "dwindle",
    },
    dwindle = {
        preserve_split = true,
    },
    misc = {
        force_default_wallpaper = -1,
        disable_hyprland_logo = false,
        enable_swallow = true,
    },
    binds = {
        workspace_back_and_forth = true,
    },
    input = {
        kb_layout = "us",
        follow_mouse = 1,
        repeat_rate = 50,
        repeat_delay = 250,
        touchpad = {
            natural_scroll = true,
        },
    },
})

hl.gesture({
    fingers = 3,
    direction = "horizontal",
    action = "workspace",
})
