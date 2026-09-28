local function run(keys, command)
    hl.bind(keys, hl.dsp.exec_cmd(command))
end

-- Applications. Use absolute paths for the two recovery shortcuts so they also
-- work when a freshly installed session has a minimal PATH.
local terminal = [[bash "$HOME/.local/bin/dotfiles-terminal"]]
run("CTRL + ALT + T", terminal)
run("SUPER + Return", terminal)
-- Rofi is short-lived and can start directly. Selected applications are still
-- placed in UWSM's graphical slice by the launcher itself.
local app_launcher = [[bash "$HOME/.local/bin/dotfiles-app-launcher"]]
run("ALT + F2", app_launcher)
hl.bind("SUPER + space", hl.dsp.exec_cmd(app_launcher), {
    description = "Application launcher (Rofi)",
})
run("SUPER + D", app_launcher)
run("SUPER + E", "uwsm-app -- thunar")
run("SUPER + L", "loginctl lock-session")
run("SUPER + C", [[bash "$HOME/.local/bin/dotfiles-clipboard"]])

-- Screenshots: complete screen, selected area, or selected area with editor.
run("Print", [[bash "$HOME/.local/bin/dotfiles-screenshot" full]])
run("SUPER + Print", [[bash "$HOME/.local/bin/dotfiles-screenshot" area]])
run("SUPER + SHIFT + S", [[bash "$HOME/.local/bin/dotfiles-screenshot" edit]])

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
hl.bind("SUPER + Q", hl.dsp.window.close())
hl.bind("SUPER + F", hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }))
hl.bind("SUPER + V", hl.dsp.window.float({ action = "toggle" }))
hl.bind("SUPER + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind("SUPER + mouse:273", hl.dsp.window.resize(), { mouse = true })

local directions = {
    H = "l",
    J = "d",
    K = "u",
    L = "r",
}

for key, direction in pairs(directions) do
    hl.bind("SUPER + " .. key, hl.dsp.focus({ direction = direction }))
    hl.bind("SUPER + SHIFT + " .. key, hl.dsp.window.move({ direction = direction }))
end

-- Four dedicated workspaces, matching the four icons shown by HyprPanel.
for workspace = 1, 4 do
    hl.bind("SUPER + " .. workspace, hl.dsp.focus({ workspace = workspace }))
    hl.bind("SUPER + SHIFT + " .. workspace, hl.dsp.window.move({
        workspace = workspace,
        follow = true,
    }))
end

run("SUPER + SHIFT + E", "uwsm stop")
