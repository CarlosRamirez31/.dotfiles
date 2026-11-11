local awful = require("awful")
local gears = require("gears")
local wibox = require("wibox")
local lgi = require("lgi")
local Gio, GLib, GdkPixbuf = lgi.Gio, lgi.GLib, lgi.GdkPixbuf
local style = require("menu-style")
local colors = style.colors

local M = {}
local anchor, request
local panel_width = 402
local row_height = 88
local popup = awful.popup({ visible = false, ontop = true, type = "dialog",
    minimum_width = panel_width, maximum_width = panel_width, bg = colors.base, fg = colors.text,
    border_width = 1, border_color = colors.border, widget = wibox.widget.textbox(),
    shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 14) end,
})
local home = os.getenv("HOME")
local mime_icons = {
    ["application/pdf"] = "󰈦", ["application/zip"] = "󰀼",
    image = "󰋩", video = "󰕧", audio = "󰎆", text = "󰈙",
}
local thumbnails = {
    ["image/png"] = true, ["image/jpeg"] = true, ["image/webp"] = true, ["image/gif"] = true,
}
local function hide()
    popup.visible = false
    if request then request:cancel(); request = nil end
    popup.widget = wibox.widget.textbox()
end

local function surface(content, background, radius)
    return wibox.widget({ content, bg = background, shape_clip = true,
        shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, radius) end,
        widget = wibox.container.background })
end

local function action(symbol, label, callback, accent)
    local color = accent and colors.lavender or colors.muted
    local background = accent and "#383047" or "#292939"
    local content = wibox.widget({
        style.icon(symbol, 10, color, 14, 24),
        label and style.text(label, 8, accent and colors.lavender or colors.text, 24) or nil,
        spacing = 4, layout = wibox.layout.fixed.horizontal,
    })
    local button = surface(wibox.container.margin(content, 8, 8, 0, 0), background, 7)
    button:buttons(awful.button({}, 1, callback))
    button:connect_signal("mouse::enter", function() button.bg = accent and "#493c5c" or colors.raised end)
    button:connect_signal("mouse::leave", function() button.bg = background end)
    return button
end

local function copy_path(path)
    local process = Gio.Subprocess.new({ "xclip", "-selection", "clipboard" },
        Gio.SubprocessFlags.STDIN_PIPE + Gio.SubprocessFlags.STDOUT_SILENCE + Gio.SubprocessFlags.STDERR_SILENCE)
    if not process then return end
    process:communicate_async(GLib.Bytes.new(path), nil, function(source, result)
        source:communicate_finish(result)
    end)
end

local function load_thumbnail(item, token, show)
    if not thumbnails[item.mime] or item.size > 16 * 1024 * 1024 then return end
    item.file:read_async(GLib.PRIORITY_DEFAULT, token, function(file, result)
        local stream = file:read_finish(result)
        if not stream then return end
        GdkPixbuf.Pixbuf.new_from_stream_at_scale_async(stream, 54, 50, true, token, function(_, decode)
            local image = GdkPixbuf.Pixbuf.new_from_stream_finish(decode)
            stream:close_async(GLib.PRIORITY_DEFAULT, nil, nil)
            if image and request == token then show(awesome.pixbuf_to_surface(image._native, nil)) end
        end)
    end)
end

local function render(directory, files, message, token)
    local rows = wibox.layout.fixed.vertical()
    rows.spacing = 8
    local badge = surface(style.icon("󰇚", 14, colors.lavender, 34, 34), "#383047", 9)
    local heading = wibox.widget({ badge, style.text("Recent downloads", 12, colors.lavender, 34),
        spacing = 10, layout = wibox.layout.fixed.horizontal })
    rows:add(wibox.widget({ heading, nil, wibox.container.place(action("󰅖", nil, hide)),
        layout = wibox.layout.align.horizontal }))
    if message then rows:add(style.text(message, 9, colors.muted, 25)) end
    for _, item in ipairs(files) do
        local path = item.file:get_path()
        local symbol = mime_icons[item.mime] or mime_icons[item.mime:match("^[^/]+")] or "󰈔"
        local icon = wibox.widget({ style.icon(symbol, 17, colors.blue, 64, 60),
            forced_width = 64, forced_height = 60, layout = wibox.layout.stack })
        load_thumbnail(item, token, function(image)
            local preview = wibox.widget.imagebox(image, false)
            icon:set_children({ wibox.container.place(preview, "center", "center") })
        end)
        local actions = wibox.widget({
            action("󰏌", "Open", function() hide(); awful.spawn({ "xdg-open", path }) end),
            action("󰆏", "Copy path", function() copy_path(path); hide() end),
            action("󰆍", "Yazi", function()
                hide()
                awful.spawn({ home .. "/.local/bin/dotfiles-terminal", "--", "yazi", "--", path })
            end, true),
            spacing = 6, layout = wibox.layout.fixed.horizontal,
        })
        local metadata = GLib.format_size(item.size) .. "  ·  " .. os.date("%b %d, %H:%M", item.modified)
        local details = wibox.widget({ style.text(item.name, 10, colors.text, 20),
            style.text(metadata, 8, colors.muted, 16), actions, spacing = 2,
            layout = wibox.layout.fixed.vertical })
        local file = wibox.widget({ wibox.container.place(surface(icon, "#292939", 8)),
            wibox.container.margin(details, 10, 0, 0, 0), nil, layout = wibox.layout.align.horizontal })
        rows:add(surface(wibox.container.margin(file, 9, 9, 8, 8), colors.surface, 9))
    end
    if directory then
        rows:add(action("󰉋", "Open Downloads folder", function()
            hide()
            awful.spawn({ "xdg-open", directory:get_path() })
        end))
    end
    popup.widget = wibox.widget({ rows, margins = 11, widget = wibox.container.margin })
    style.reveal(popup)
    style.place_below_bar(popup, anchor)
end

popup:connect_signal("property::height", function()
    if popup.visible and anchor then style.place_below_bar(popup, anchor) end
end)

local function recent(directory, limit)
    local attributes = "standard::name,standard::display-name,standard::type,standard::is-hidden,standard::size,"
        .. "standard::content-type,time::modified,time::modified-usec"
    local enumerator = directory:async_enumerate_children(attributes, Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS)
    if not enumerator then return nil end
    local newest = {}
    while true do
        local files, err = enumerator:async_next_files(64)
        if not files or #files == 0 then
            enumerator:async_close()
            if err then return nil end
            return newest
        end
        for _, info in ipairs(files) do
            local name = info:get_name()
            local extension = name:lower():match("%.([^%.]+)$")
            if info:get_file_type() == "REGULAR" and not info:get_is_hidden()
                and extension ~= "part" and extension ~= "crdownload" and extension ~= "download" and extension ~= "tmp" then
                newest[#newest + 1] = { file = enumerator:get_child(info), name = info:get_display_name(),
                    mime = info:get_content_type() or "", size = info:get_size(),
                    modified = info:get_attribute_uint64("time::modified"),
                    micros = info:get_attribute_uint32("time::modified-usec") }
                table.sort(newest, function(a, b)
                    if a.modified ~= b.modified then return a.modified > b.modified end
                    if a.micros ~= b.micros then return a.micros > b.micros end
                    return a.name < b.name
                end)
                if #newest > limit then table.remove(newest) end
            end
        end
    end
end

function M.toggle()
    if popup.visible then hide(); return end
    popup.screen = awful.screen.focused()
    local area = popup.screen.workarea
    anchor = { x = area.x + area.width - panel_width / 2 - 18, y = area.y }
    local path = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) or (home .. "/Downloads")
    local directory = Gio.File.new_for_path(path)
    local token = Gio.Cancellable()
    request = token
    render(directory, {}, "Loading…", token)
    local limit = math.max(1, math.min(6, math.floor((area.height - 112) / row_height)))
    Gio.Async.start(function()
        local ok, files = pcall(recent, directory, limit)
        if request ~= token then return end
        if not ok or not files then render(nil, {}, "Downloads folder unavailable", token)
        else render(directory, files, #files == 0 and "No downloads yet" or nil, token) end
    end, token)()
end

return M
