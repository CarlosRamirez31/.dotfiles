local programs = {
    terminal = "uwsm app -- ghostty",
    file_manager = "uwsm app -- nautilus",
    menu = "uwsm app -- rofi -show drun",
    emoji = "fuzzel-emoji",
    browser = "uwsm app -- zen-browser",
    discord = "uwsm app -- vesktop",
}

local function run(keys, command, flags)
    hl.bind(keys, hl.dsp.exec_cmd(command), flags)
end

-- Mouse and workspace wheel
hl.bind("SUPER + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind("SUPER + mouse_up", hl.dsp.focus({ workspace = "e-1" }))
hl.bind("SUPER + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind("SUPER + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Laptop controls
run("XF86AudioMute", "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle", { locked = true })
run("SUPER + SHIFT + M", "swayosd-client --input-volume mute-toggle", { locked = true })
run("XF86AudioRaiseVolume", "wpctl set-mute @DEFAULT_AUDIO_SINK@ 0; wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 10%+", { locked = true, repeating = true })
run("XF86AudioLowerVolume", "wpctl set-mute @DEFAULT_AUDIO_SINK@ 0; wpctl set-volume @DEFAULT_AUDIO_SINK@ 10%-", { locked = true, repeating = true })
run("XF86MonBrightnessDown", "brightnessctl set 5%-")
run("XF86MonBrightnessUp", "brightnessctl set 5%+")
run("XF86Calculator", "QT_QPA_PLATFORMTHEME=qt5ct kcalc")
run("XF86AudioMedia", "playerctl play-pause", { locked = true })
run("XF86AudioPlay", "playerctl play-pause", { locked = true })
run("XF86AudioStop", "playerctl stop", { locked = true })
run("XF86AudioPrev", "playerctl previous", { locked = true })
run("XF86AudioNext", "playerctl next", { locked = true })

-- Applications
run("SUPER + Return", programs.terminal)
run("SUPER + Space", "pkill rofi || " .. programs.menu)
run("SUPER + comma", "pkill fuzzel || " .. programs.emoji)
run("ALT + Space", "pkill rofi || rofi -show window")
run("SUPER + B", programs.browser)
run("SUPER + D", programs.discord)
run("SUPER + E", programs.file_manager)
run("SUPER + T", "swaync-client -t -sw")
run("SUPER + V", "pkill fuzzel || cliphist list | fuzzel --match-mode fzf --dmenu --anchor center --lines 15 --width 80 | cliphist decode | wl-copy")
run("SUPER + M", "youtube-music")
run("SUPER + O", "obsidian")
run("SUPER + CTRL + L", "hyprlock")

-- Windows and workspaces
hl.bind("SUPER + U", hl.dsp.focus({ urgent_or_last = true }))
hl.bind("SUPER + I", function()
    local workspace = hl.get_active_special_workspace() or hl.get_active_workspace()
    if not workspace then
        return
    end

    local next_layout = workspace.tiled_layout == "dwindle" and "master" or "dwindle"
    local selector = workspace.special and tostring(workspace.name) or "name:" .. tostring(workspace.name)
    hl.workspace_rule({ workspace = selector, layout = next_layout })
    hl.notification.create({ text = "Layout: " .. next_layout, timeout = 1500 })
end)
hl.bind("SUPER + S", hl.dsp.window.float({ action = "toggle" }))
run("SUPER + A", "if hyprctl activewindow | grep -q 'floating: 0'; then hyprctl dispatch 'hl.dsp.window.float({ action = \"toggle\" })'; fi; hyprctl dispatch 'hl.dsp.window.pin()'")
hl.bind("SUPER + W", hl.dsp.window.close())

for workspace = 1, 10 do
    local key = workspace % 10
    hl.bind("SUPER + " .. key, hl.dsp.focus({ workspace = workspace }))
    hl.bind("SUPER + CTRL + " .. key, hl.dsp.window.move({ workspace = workspace, follow = true }))
    hl.bind("SUPER + SHIFT + " .. key, hl.dsp.window.move({ workspace = workspace, follow = false }))
end

local directions = {
    H = "l",
    L = "r",
    K = "u",
    J = "d",
}

for key, direction in pairs(directions) do
    hl.bind("SUPER + " .. key, hl.dsp.focus({ direction = direction }), { release = true })
    hl.bind("SUPER + SHIFT + " .. key, hl.dsp.window.move({ direction = direction }), { release = true })
end

hl.bind("SUPER + CTRL + K", hl.dsp.focus({ monitor = "l" }), { release = true })
hl.bind("SUPER + CTRL + J", hl.dsp.focus({ monitor = "r" }), { release = true })
hl.bind("SUPER + ALT + H", hl.dsp.layout("splitratio -0.1"), { release = true })
hl.bind("SUPER + ALT + L", hl.dsp.layout("splitratio +0.1"), { release = true })

hl.bind("SUPER + grave", hl.dsp.workspace.toggle_special(""))
hl.bind("SUPER + SHIFT + grave", hl.dsp.window.move({ workspace = "special", follow = true }))
hl.bind("SUPER + backslash", hl.dsp.window.fullscreen({ mode = "maximized", action = "toggle" }))
hl.bind("SUPER + F", hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }))
hl.bind("SUPER + P", hl.dsp.window.pseudo())
hl.bind("SUPER + SHIFT + Return", hl.dsp.layout("swapwithmaster"))
hl.bind("SUPER + SHIFT + period", hl.dsp.layout("orientationnext"))
hl.bind("SUPER + SHIFT + comma", hl.dsp.layout("orientationprev"))
hl.bind("SUPER + CTRL + Return", hl.dsp.layout("focusmaster"))

-- Screenshots
run("Print", [[mkdir -p "$(xdg-user-dir PICTURES)/Screenshots"; grimblast --notify save output "$(xdg-user-dir PICTURES)/Screenshots/$(date +'%Y%m%d%H%M%S_1.png')"]], { locked = true })
run("SUPER + Print", "grimblast --notify save screen")
run("SUPER + SHIFT + Print", "grimblast save output - | swappy -f -")
run("SUPER + CTRL + S", [[mkdir -p "$(xdg-user-dir PICTURES)/Screenshots"; grimblast --notify save area "$(xdg-user-dir PICTURES)/Screenshots/$(date +'%Y%m%d%H%M%S_1.png')"]])
run("SUPER + SHIFT + S", "grimblast --notify copy area")
run("SUPER + ALT + S", "grimblast --notify copy")

-- Power
run("SUPER + SHIFT + Q", "shutdown now")
run("SUPER + SHIFT + R", "reboot")
run("SUPER + CTRL + Q", "uwsm stop")
