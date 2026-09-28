local hardware = require("lua.hardware")

-- VMware reports 1280x800 as preferred even when its virtual display is set
-- to 1080p. This is hardware detection, not a host-specific configuration:
-- physical machines and other hypervisors still use their preferred mode.
local monitor_mode = hardware.vmware and "1920x1080@60" or "preferred"

hl.monitor({
    output = "",
    mode = monitor_mode,
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
    cursor = {
        -- VMware already draws the host pointer over the guest display. Hide
        -- Hyprland's copy there so only one pointer remains visible.
        invisible = hardware.vmware,
        no_hardware_cursors = 0,
        -- Bibata is installed as an XCursor theme. Keeping one cursor backend
        -- also prevents clients and Hyprland from selecting different sizes.
        enable_hyprcursor = false,
        sync_gsettings_theme = true,
    },
    render = {
        -- Avoid the extra queued frame introduced by triple buffering. This
        -- measured lower CPU usage and input latency on vmwgfx.
        new_render_scheduling = false,
        -- vmwgfx exposes neither HDR nor CTM; avoid an extra color pipeline.
        cm_enabled = not hardware.vmware,
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
    -- Start UWSM's lightweight application daemon in the background now. Its
    -- shell client is much faster than importing the Python CLI on every app.
    hl.exec_cmd("uwsm finalize PATH GDK_BACKEND GSK_RENDERER MOZ_ENABLE_WAYLAND ELECTRON_OZONE_PLATFORM_HINT TERMINAL XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE XCURSOR_THEME XCURSOR_SIZE HYPRCURSOR_THEME HYPRCURSOR_SIZE && uwsm-app -- true")
    hl.exec_cmd("uwsm-app -- hyprpanel")
    hl.exec_cmd([[pgrep -x awww-daemon >/dev/null || awww-daemon & sleep 1; awww img "$HOME/.config/wallpapers/arch-bsod.png" --transition-type none]])
    hl.exec_cmd("hyprctl setcursor Bibata-Modern-Classic 24")
    hl.exec_cmd("systemctl --user start hyprpolkitagent.service")
end)
