local monitor_mode = "preferred"
local vendor_file = io.open("/sys/class/dmi/id/sys_vendor", "r")
if vendor_file then
    local system_vendor = vendor_file:read("*l") or ""
    vendor_file:close()
    if system_vendor:lower():find("vmware", 1, true) then
        -- VMware advertises 1280x800 as preferred even when the virtual
        -- display is configured for 1080p.
        monitor_mode = "1920x1080@60"
    end
end

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
        -- Let the VM transport its hardware cursor instead of baking a second
        -- software cursor into the framebuffer. This avoids the two-pointer
        -- effect with SPICE/QEMU and VirtualBox mouse integration.
        no_hardware_cursors = 0,
        -- Bibata is installed as an XCursor theme. Keeping one cursor backend
        -- also prevents clients and Hyprland from selecting different sizes.
        enable_hyprcursor = false,
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
    -- Start UWSM's lightweight application daemon in the background now. Its
    -- shell client is much faster than importing the Python CLI on every app.
    hl.exec_cmd("uwsm finalize GDK_BACKEND GSK_RENDERER MOZ_ENABLE_WAYLAND ELECTRON_OZONE_PLATFORM_HINT XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE XCURSOR_THEME XCURSOR_SIZE HYPRCURSOR_THEME HYPRCURSOR_SIZE && uwsm-app -- /usr/bin/true")
    hl.exec_cmd("uwsm app -- hyprpanel")
    hl.exec_cmd([[pgrep -x awww-daemon >/dev/null || awww-daemon & sleep 1; awww img "$HOME/.config/wallpapers/arch-bsod.png" --transition-type none]])
    hl.exec_cmd("hyprctl setcursor Bibata-Modern-Classic 24")
    hl.exec_cmd("systemctl --user start hyprpolkitagent.service")
end)
