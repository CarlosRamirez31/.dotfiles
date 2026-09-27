hl.monitor({
    output = "",
    mode = "1920x1080@60",
    position = "0x0",
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
    cursor = {
        -- Virtual machines can expose the hardware cursor while Hyprland also
        -- draws its software cursor, producing one large and one small arrow.
        no_hardware_cursors = 1,
        sync_gsettings_theme = true,
    },
    misc = {
        disable_hyprland_logo = true,
        force_default_wallpaper = 0,
        -- Git updates several Lua files in sequence. Reload only after the
        -- installer has finished, never while the tree is half updated.
        disable_autoreload = true,
    },
})

hl.gesture({
    fingers = 3,
    direction = "horizontal",
    action = "workspace",
})

hl.on("hyprland.start", function()
    -- GNOME applications commonly use D-Bus activation instead of keeping the
    -- process spawned by Rofi. Export the live Wayland display before starting
    -- any desktop components so those services can create visible windows.
    hl.exec_cmd("uwsm finalize XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE XCURSOR_THEME XCURSOR_SIZE HYPRCURSOR_THEME HYPRCURSOR_SIZE")
    hl.exec_cmd("uwsm app -- hyprpanel")
    hl.exec_cmd([[pgrep -x awww-daemon >/dev/null || awww-daemon & sleep 1; awww img "$HOME/.config/wallpapers/arch-bsod.png" --transition-type none]])
    hl.exec_cmd("hyprctl setcursor Bibata-Modern-Classic 24")
    hl.exec_cmd("systemctl --user start hyprpolkitagent.service")
end)
