local awful = require("awful")
local gears = require("gears")
local wibox = require("wibox")
local style = require("menu-style")
local colors = style.colors

local M = {}
local popup = awful.popup({ visible = false, ontop = true, type = "notification",
    minimum_width = 344, maximum_width = 344, bg = colors.base, fg = colors.text,
    border_width = 1, border_color = colors.border, widget = wibox.widget.textbox(),
    shape = function(cr, width, height) gears.shape.rounded_rect(cr, width, height, 14) end,
})
local timer
local function place()
    local area = popup.screen.workarea
    popup.x = area.x + math.max(0, area.width - popup.width - 18)
    popup.y = area.y + math.max(0, area.height - popup.height - 18)
end
local function hide()
    timer:stop()
    popup.visible = false
    popup.widget = wibox.widget.textbox()
end
timer = gears.timer({ timeout = 8, single_shot = true, callback = hide })
popup:connect_signal("property::height", place)
popup:connect_signal("mouse::enter", function() timer:stop() end)
popup:connect_signal("mouse::leave", function() if popup.visible then timer:again() end end)

local function label(value, color)
    return wibox.widget({ markup = '<span foreground="' .. color .. '">' .. gears.string.xml_escape(value) .. "</span>",
        font = "JetBrainsMono Nerd Font Bold 9", ellipsize = "end", valign = "center",
        forced_height = 24, widget = wibox.widget.textbox })
end

local function button(title, callback, color)
    local text = label(title, color or colors.text)
    text.align = "center"
    local result = wibox.widget({ { text, left = 8, right = 8, widget = wibox.container.margin },
        bg = colors.surface, shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 7) end,
        widget = wibox.container.background })
    result:buttons(awful.button({}, 1, callback))
    result:connect_signal("mouse::enter", function() result.bg = colors.raised end)
    result:connect_signal("mouse::leave", function() result.bg = colors.surface end)
    return result
end

function M.show(path, destination)
    if type(path) ~= "string" or path:sub(1, 1) ~= "/" then return false end
    destination = destination or path
    local folder = destination:match("^(.+)/[^/]+$")
    local image, err = require("artwork-style").load(path)
    if not folder or err or not image then return false end
    local function run(argv)
        return function() hide(); awful.spawn(argv) end
    end
    local function edit()
        local editor = "/usr/bin/satty"
        if not gears.filesystem.file_executable(editor) then
            editor = os.getenv("HOME") .. "/.local/bin/satty"
        end
        if not gears.filesystem.file_executable(editor) then
            require("naughty").notify({ title = "Screenshot editor", text = "Install Satty to edit screenshots." })
            return
        end
        local output = destination:gsub("%%", "%%%%")
        run({ "/usr/bin/env", "ADW_DEBUG_COLOR_SCHEME=prefer-dark", editor,
            "--filename", path, "--initial-tool", "brush", "--output-filename", output,
            "--actions-on-enter", "save-to-clipboard", "--actions-on-escape", "exit",
            "--copy-command", "xclip -selection clipboard -t image/png -i" })()
    end
    hide()
    popup.screen = mouse.screen or awful.screen.focused()
    popup.widget = wibox.widget({ {
        { label(destination == path and "Screenshot" or "Screenshot · not saved", colors.lavender), nil, button("×", hide, colors.muted),
            layout = wibox.layout.align.horizontal },
        { { { image = image, resize = true, widget = wibox.widget.imagebox },
                halign = "center", valign = "center", forced_height = 166, widget = wibox.container.place },
            bg = colors.surface, shape_clip = true,
            shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 8) end,
            widget = wibox.container.background },
        { button("Save", function()
                if path == destination then hide(); return end
                awful.spawn.easy_async({ "cp", "--", path, destination }, function(_, err, _, code)
                    if code == 0 then hide() else require("naughty").notify({title="Screenshot",text=err}) end
                end)
            end, colors.lavender), button("Edit", edit, colors.lavender),
            button("Folder", run({ "xdg-open", folder })), spacing = 6, layout = wibox.layout.flex.horizontal },
        spacing = 8, layout = wibox.layout.fixed.vertical },
        margins = 11, widget = wibox.container.margin })
    style.reveal(popup)
    place()
    timer:again()
    return true
end

return M
