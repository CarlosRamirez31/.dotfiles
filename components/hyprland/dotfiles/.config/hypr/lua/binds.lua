local function run(keys, command)
    hl.bind(keys, hl.dsp.exec_cmd(command))
end

-- Applications. Use absolute paths for the two recovery shortcuts so they also
-- work when a freshly installed session has a minimal PATH.
local terminal = [[bash "$HOME/.local/bin/dotfiles-terminal"]]
run("CTRL + ALT + T", terminal)
run("ALT + Return", terminal)
-- Rofi is short-lived and can start directly. Selected applications are still
-- placed in UWSM's graphical slice by the launcher itself.
local app_launcher = [[bash "$HOME/.local/bin/dotfiles-app-launcher"]]
run("ALT + F2", app_launcher)
hl.bind("ALT + space", hl.dsp.exec_cmd(app_launcher), {
    description = "Application launcher (Rofi)",
})
run("ALT + D", app_launcher)
run("ALT + B", "uwsm-app -- firefox")
run("ALT + E", [[bash "$HOME/.local/bin/dotfiles-terminal" --class dotfiles-yazi --title "Archivos" -e yazi]])
run("CTRL + ALT + E", "uwsm-app -- thunar")
run("ALT + W", [[bash "$HOME/.local/bin/dotfiles-wallpaper" choose]])
run("CTRL + SHIFT + B", [[bash "$HOME/.local/bin/dotfiles-lock"]])
run("ALT + C", [[bash "$HOME/.local/bin/dotfiles-clipboard"]])
run("SUPER + C", [[bash "$HOME/.local/bin/dotfiles-clipboard"]])

-- Screenshots: complete screen, selected area, or selected area with editor.
run("Print", [[bash "$HOME/.local/bin/dotfiles-screenshot" full]])
run("ALT + Print", [[bash "$HOME/.local/bin/dotfiles-screenshot" area]])
run("ALT + SHIFT + S", [[bash "$HOME/.local/bin/dotfiles-screenshot" edit]])
run("ALT + SHIFT + R", [[bash "$HOME/.local/bin/dotfiles-record" area]])
run("ALT + SHIFT + C", "hyprpicker --autocopy")

-- Hardware media keys continue working while the session is locked. Repeating
-- volume and brightness bindings feel natural when a key is held down.
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), {
    locked = true,
    repeating = true,
})
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), {
    locked = true,
    repeating = true,
})
hl.bind("XF86AudioMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), {
    locked = true,
})
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), {
    locked = true,
})
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("brightnessctl set 5%+"), {
    locked = true,
    repeating = true,
})
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl set 5%-"), {
    locked = true,
    repeating = true,
})
hl.bind("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"), { locked = true })
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"), { locked = true })

-- Windows.
hl.bind("ALT + Q", hl.dsp.window.close())
hl.bind("ALT + F", hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }))
hl.bind("ALT + V", hl.dsp.window.float({ action = "toggle" }))
hl.bind("ALT + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind("ALT + mouse:273", hl.dsp.window.resize(), { mouse = true })

local directions = {
    H = "l",
    J = "d",
    K = "u",
    L = "r",
}

for key, direction in pairs(directions) do
    hl.bind("ALT + " .. key, hl.dsp.focus({ direction = direction }))
    hl.bind("ALT + SHIFT + " .. key, hl.dsp.window.move({ direction = direction }))
end

local resize_steps = {
    H = { x = -30, y = 0 },
    J = { x = 0, y = 30 },
    K = { x = 0, y = -30 },
    L = { x = 30, y = 0 },
}

for key, delta in pairs(resize_steps) do
    hl.bind("ALT + CTRL + " .. key, hl.dsp.window.resize({
        x = delta.x,
        y = delta.y,
        relative = true,
    }), { repeating = true })
end

-- Four dedicated workspaces, matching the four icons shown by HyprPanel.
for workspace = 1, 4 do
    hl.bind("ALT + " .. workspace, hl.dsp.focus({ workspace = workspace }))
    hl.bind("ALT + SHIFT + " .. workspace, hl.dsp.window.move({
        workspace = workspace,
        follow = true,
    }))
end

run("ALT + SHIFT + E", "uwsm stop")
