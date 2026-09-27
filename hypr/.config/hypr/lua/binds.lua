local function run(keys, command)
    hl.bind(keys, hl.dsp.exec_cmd(command))
end

-- Applications. Use absolute paths for the two recovery shortcuts so they also
-- work when a freshly installed session has a minimal PATH.
run("CTRL + ALT + T", "/usr/bin/ghostty")
run("SUPER + Return", "/usr/bin/ghostty")
-- Rofi only selects an entry. The helper launches its real Desktop Entry with
-- GIO so D-Bus activated applications work just like they do under GNOME.
local app_launcher = [[/usr/bin/bash "$HOME/.local/bin/dotfiles-app-launcher"]]
run("ALT + F2", app_launcher)
hl.bind("SUPER + space", hl.dsp.exec_cmd(app_launcher), {
    description = "Application launcher (Rofi)",
})
run("SUPER + D", app_launcher)

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

-- Workspaces.
for workspace = 1, 9 do
    hl.bind("SUPER + " .. workspace, hl.dsp.focus({ workspace = workspace }))
    hl.bind("SUPER + SHIFT + " .. workspace, hl.dsp.window.move({
        workspace = workspace,
        follow = true,
    }))
end

run("SUPER + SHIFT + E", "uwsm stop")
