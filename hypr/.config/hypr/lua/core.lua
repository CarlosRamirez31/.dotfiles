hl.monitor({
    output = "",
    mode = "preferred",
    position = "auto",
    scale = 1,
})

hl.config({
    general = {
        layout = "dwindle",
        resize_on_border = true,
        allow_tearing = false,
    },
    dwindle = {
        preserve_split = true,
    },
    input = {
        kb_layout = "us",
        follow_mouse = 1,
        touchpad = {
            natural_scroll = true,
        },
    },
    misc = {
        disable_hyprland_logo = true,
        force_default_wallpaper = 0,
    },
})

hl.gesture({
    fingers = 3,
    direction = "horizontal",
    action = "workspace",
})

hl.on("hyprland.start", function()
    hl.exec_cmd("waybar")
    hl.exec_cmd("awww-daemon")
    hl.exec_cmd("systemctl --user start hyprpolkitagent.service")
end)
