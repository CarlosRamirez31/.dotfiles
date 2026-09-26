local function window_rule(match, effects)
    effects.match = match
    hl.window_rule(effects)
end

local function layer_rule(namespace, effects)
    effects.match = { namespace = namespace }
    hl.layer_rule(effects)
end

-- Application placement
local workspace_classes = {
    ["^(firefox|zen|floorp)$"] = "1",
    ["^neovide$"] = "4",
    ["^org.kde.kdeconnect.app$"] = "5",
    ["^(org.gnome.Nautilus|[Tt]hunar|Pcmanfm)$"] = "6",
    ["^(evince|obsidian|sioyek|org.pwmt.zathura)$"] = "7",
    ["^(Spotify|com.github.th_ch.youtube_music)$"] = "8",
    ["^vesktop$"] = "9",
    ["^[Aa]rm[Cc]ord$"] = "9 silent",
    ["^org.telegram.desktop$"] = "10 silent",
    ["^xdm-app$"] = "special",
}

for class, workspace in pairs(workspace_classes) do
    window_rule({ class = class }, { workspace = workspace })
end

-- Common floating windows and dialogs
local floating_titles = {
    "^(kcalc|zoom|file_progress|confirm|dialog|download|notification|error|splash|nwg-look)$",
    "^(org-example-App|confirmreset|Delete profile|blueberry.py|steam|guifetch)$",
    "^(New Download|new download)$",
    "^(File Operation Progress|Confirm to replace files|KDE Connect URL handler)$",
    "^(Open File|Select a File|Choose wallpaper|Open Folder|Save As|Library|File Upload).*$",
    "^fabric$",
    "^qBittorrent v4[.]6[.]2$",
}

for _, title in ipairs(floating_titles) do
    window_rule({ title = title }, { float = true })
end

window_rule({ class = "^(Plexamp|com.viber.Viber|one.alynx.showmethekey|showmethekey-gtk|xdm-app)$" }, { float = true })

local centered_dialogs = {
    "^Open File.*$",
    "^Select a File.*$",
    "^Choose wallpaper.*$",
    "^Open Folder.*$",
    "^Save As.*$",
    "^Library.*$",
    "^File Upload.*$",
}

for _, title in ipairs(centered_dialogs) do
    window_rule({ title = title }, { center = true })
end

-- Picture-in-picture keeps the previous size, position and pinning behavior.
window_rule(
    { title = "^[Pp]icture[- ]?[Ii]n[- ]?[Pp]icture.*$" },
    {
        float = true,
        pin = true,
        keep_aspect_ratio = true,
        move = { "monitor_w-window_w-20", "monitor_h-window_h-20" },
        size = { "monitor_w*0.36", "monitor_h*0.36" },
    }
)

window_rule(
    { class = "^one.alynx.showmethekey$" },
    { float = true, center = true, size = { "monitor_w*0.5", "monitor_h*0.7" } }
)
window_rule(
    { class = "^showmethekey-gtk$" },
    {
        float = true,
        pin = true,
        move = { "monitor_w-window_w-20", "monitor_h-window_h-20" },
        size = { "monitor_w*0.25", "monitor_h*0.1" },
    }
)
window_rule({ class = "^Waydroid$" }, { size = { "monitor_w*0.4", "monitor_h*0.85" } })
window_rule({ title = "^Minecraft.*$" }, { size = { "monitor_w", "monitor_h" } })
window_rule({ title = "^DOOM.*$" }, { size = { "monitor_w", "monitor_h" } })

-- Behavioral rules
window_rule({ class = ".*" }, { suppress_event = "maximize" })
window_rule({ class = ".*" }, { idle_inhibit = "fullscreen" })
window_rule({ title = ".*[.]exe$" }, { immediate = true })
window_rule({ class = "^steam_app.*$" }, { immediate = true })
window_rule({ float = false }, { no_shadow = true })
window_rule(
    { class = "^(zen-alpha|thunar|Slack|discord|Spotify|neovide|kitty|[Aa]rm[Cc]ord|vesktop|org.wezfurlong.wezterm|com.mitchellh.ghostty|YouTube Music)$" },
    { opacity = "0.90 0.90" }
)

-- Layer shell behavior
layer_rule(".*", { xray = true })

for _, namespace in ipairs({
    "^calendarmenu$", "^energymenu$", "^networkmneu$", "^audiomenu$",
    "^mediamenu$", "^selection$", "^dashboardmenu$", "^walker$", "^overview$",
    "^anyrun$", "^indicator.*$", "^osk$", "^hyprpicker$", "^noanim$",
}) do
    layer_rule(namespace, { no_anim = true })
end

layer_rule("^notificationsmenu$", { animation = "popin" })
layer_rule("^shell:.*$", { blur = true, ignore_alpha = 0.6 })
layer_rule("^gtk-layer-shell$", { blur = true, ignore_alpha = 0 })
layer_rule("^launcher$", { blur = true, ignore_alpha = 0.5 })
layer_rule("^notifications$", { blur = true, ignore_alpha = 0.69 })
layer_rule("^sideleft.*$", { animation = "slide left" })
layer_rule("^sideright.*$", { animation = "slide right" })
layer_rule("^session[0-9]*$", { blur = true })
