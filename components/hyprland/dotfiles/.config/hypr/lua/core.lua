local hardware = require("lua.hardware")

-- VMware reports 1280x800 as preferred even when its virtual display is set
-- to 1080p. This is hardware detection, not a host-specific configuration:
-- physical machines and other hypervisors still use their preferred mode.
local monitor_mode = hardware.vmware and "1920x1080@60" or "preferred"

-- Let the compositor manage ordinary GTK window frames.  This prevents the
-- close, minimize, and maximize buttons that client-side decorations add.
hl.env("GTK_CSD", "0")

hl.monitor({
    output = "",
    mode = monitor_mode,
    position = "auto",
    scale = 1,
})

-- A machine may add private monitor rules without changing the portable base.
-- Copy local.lua.example to local.lua; the installer deliberately ignores it.
local local_config = os.getenv("HOME") .. "/.config/hypr/local.lua"
local local_file = io.open(local_config, "r")
if local_file then
    local_file:close()
    dofile(local_config)
end

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
        -- Keep Hyprland's pointer visible on both physical and virtual machines.
        invisible = false,
        -- VMware behaves more reliably when cursor rendering stays in software.
        no_hardware_cursors = hardware.vmware and 1 or 0,
        -- Bibata is installed as an XCursor theme. Keeping one cursor backend
        -- also prevents clients and Hyprland from selecting different sizes.
        enable_hyprcursor = false,
        sync_gsettings_theme = true,
    },
    gestures = {
        -- Workspaces 1-4 are the complete set; swiping at either end must not
        -- create an additional workspace.
        workspace_swipe_create_new = false,
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
        -- Let a replacement locker recover the protected session when a lock
        -- client crashes. This is required by the VMware Gtklock fallback
        -- after Hyprlock's vmwgfx failure.
        allow_session_lock_restore = true,
        -- Git updates several Lua files in sequence. Reload only after the
        -- installer has finished, never while the tree is half updated.
        disable_autoreload = true,
    },
})

-- Keep all four workspaces alive even while they are empty. Together with the
-- gesture setting above, workspace navigation stays bounded to this set.
for workspace = 1, 4 do
    hl.workspace_rule({
        workspace = tostring(workspace),
        persistent = true,
    })
end

hl.gesture({
    fingers = 3,
    direction = "horizontal",
    action = "workspace",
})

-- File dialogs should behave like dialogs, without changing regular Yazi or
-- terminal windows. The portal assigns this class only to its Yazi picker.
hl.window_rule({
    name = "center-file-picker",
    match = { class = "^dotfiles-file-picker$" },
    float = true,
    center = true,
    size = "1100 750",
})

hl.on("hyprland.start", function()
    -- GNOME applications commonly use D-Bus activation instead of keeping the
    -- process spawned by Rofi. Export the live Wayland display before starting
    -- any desktop components so those services can create visible windows.
    -- Start UWSM's lightweight application daemon in the background now. Its
    -- shell client is much faster than importing the Python CLI on every app.
    hl.exec_cmd("uwsm finalize PATH GDK_BACKEND GSK_RENDERER GTK_USE_PORTAL GTK_CSD MOZ_ENABLE_WAYLAND ELECTRON_OZONE_PLATFORM_HINT TERMINAL XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE XCURSOR_THEME XCURSOR_SIZE HYPRCURSOR_THEME HYPRCURSOR_SIZE SSH_AUTH_SOCK && uwsm-app -- true")
    -- Session services (panel, polkit and clipboard) and XDG autostart apps
    -- (including Blueman) are already started by graphical-session.target.
    hl.exec_cmd([[bash "$HOME/.local/bin/dotfiles-wallpaper" restore]])
    hl.exec_cmd("hyprctl setcursor Bibata-Modern-Classic 24")
end)
