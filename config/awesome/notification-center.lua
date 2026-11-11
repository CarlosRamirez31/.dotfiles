local awful = require("awful")
local gears = require("gears")
local naughty = require("naughty")
local wibox = require("wibox")
local style = require("menu-style")
local colors = style.colors

local M = {}
local history, unread, page = {}, 0, 1
local directory = (os.getenv("XDG_RUNTIME_DIR") or os.getenv("XDG_CACHE_HOME") or
    (os.getenv("HOME") .. "/.cache")) .. "/dotfiles-polybar-tags"
local status = directory .. "/notifications"
local anchor, below
local popup = awful.popup({ visible = false, ontop = true, type = "dialog",
    minimum_width = 344, maximum_width = 344, bg = colors.base, fg = colors.text,
    border_width = 1, border_color = colors.border,
    shape = function(cr, width, height) gears.shape.rounded_rect(cr, width, height, 14) end,
    widget = wibox.widget.textbox(),
})

local function publish()
    local glyph, color = "󰂚", colors.muted
    if naughty.is_suspended() then glyph, color = "󰂛", colors.yellow
    elseif unread > 0 then glyph, color = "󰂞", colors.lavender end
    local label = "%{F" .. color .. "}" .. glyph .. (unread > 0 and (" " .. unread) or "") .. "%{F-}"
    gears.filesystem.make_directories(directory)
    local file = io.open(status .. ".tmp", "w")
    if not file then return end
    file:write(label, "\n")
    if file:close() then os.rename(status .. ".tmp", status) end
end

local function text(value, size, color, height)
    return wibox.widget({ markup = '<span foreground="' .. color .. '">' .. gears.string.xml_escape(value) .. "</span>",
        font = "JetBrainsMono Nerd Font Bold " .. size, ellipsize = "end", valign = "center",
        forced_height = height, widget = wibox.widget.textbox })
end
local function button(value, callback, enabled, color)
    local label = text(value, 9, enabled and (color or colors.text) or colors.muted, 24)
    label.align = "center"
    local widget = wibox.widget({ { label, left = 8, right = 8, widget = wibox.container.margin },
        bg = colors.surface, shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 6) end,
        widget = wibox.container.background })
    if enabled then
        widget:buttons(awful.button({}, 1, callback))
        widget:connect_signal("mouse::enter", function() widget.bg = colors.raised end)
        widget:connect_signal("mouse::leave", function() widget.bg = colors.surface end)
    end
    return widget
end

local function hide()
    popup.visible = false
end

local function place()
    if not anchor then return end
    local g = popup.screen.workarea
    popup.x = math.max(g.x + 8, math.min(anchor.x - popup.width / 2, g.x + g.width - popup.width - 8))
    popup.y = math.max(g.y, math.min(below, g.y + g.height - popup.height - 8))
end
popup:connect_signal("property::height", place)

local render
function M.set_quiet(enabled)
    if enabled == naughty.is_suspended() then return end
    if not enabled then
        local pending = naughty.notifications.suspended
        naughty.resume()
        -- History already has these messages. Dismiss the suspended popups
        -- in the same event turn so returning to normal doesn't replay them.
        for _, notice in ipairs(pending) do naughty.destroy(notice) end
    else
        naughty.suspend()
    end
    publish()
    if popup.visible then render() end
end

render = function()
    local body = wibox.layout.fixed.vertical()
    body.spacing = 8
    local function clear()
        history, unread, page = {}, 0, 1
        publish()
        render()
    end
    local quiet = naughty.is_suspended()
    body:add(wibox.widget({ text("Notifications", 11, colors.lavender, 24), nil, button("×", hide, true),
        layout = wibox.layout.align.horizontal }))
    body:add(wibox.widget({ button(quiet and "Do Not Disturb · On" or "Do Not Disturb · Off",
        function() M.set_quiet(not naughty.is_suspended()) end,
        true, quiet and colors.yellow or nil), nil, button("Clear", clear, #history > 0),
        layout = wibox.layout.align.horizontal }))

    local groups, order, sorted = {}, {}, {}
    for _, item in ipairs(history) do
        if not groups[item.app] then
            order[#order + 1] = item.app
            groups[item.app] = {}
        end
        table.insert(groups[item.app], item)
    end
    for _, app in ipairs(order) do
        for _, item in ipairs(groups[app]) do sorted[#sorted + 1] = item end
    end
    local size = math.max(1, math.min(5, math.floor((popup.screen.workarea.height - 130) / 92)))
    local pages = math.max(1, math.ceil(#sorted / size))
    page = math.min(page, pages)
    if #sorted == 0 then body:add(text("No notifications", 10, colors.muted, 30)) end
    local previous
    for index = (page - 1) * size + 1, math.min(page * size, #sorted) do
        local item = sorted[index]
        if item.app ~= previous then body:add(text(item.app, 9, colors.blue, 16)) end
        previous = item.app
        local row = wibox.layout.fixed.vertical()
        row:add(wibox.widget({ text(item.title ~= "" and item.title or item.message, 10, colors.text, 19),
            nil, text(item.time, 8, colors.muted, 19), layout = wibox.layout.align.horizontal }))
        if item.title ~= "" and item.message ~= "" then
            local message = text(item.message, 9, colors.muted, 34)
            message.wrap = "word_char"
            row:add(message)
        end
        local glyph = item.icon and wibox.widget({ image = item.icon, resize = true,
            forced_width = 28, forced_height = 28, widget = wibox.widget.imagebox })
            or style.icon("󰂚", 16, colors.lavender, 28, 28)
        local content = wibox.widget({ wibox.container.margin(glyph, 0, 8, 3, 0), row,
            layout = wibox.layout.fixed.horizontal })
        row.forced_width = 266
        local card = wibox.widget({ { content, left = 8, right = 8, top = 5, bottom = 5, widget = wibox.container.margin },
            bg = colors.surface, shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 8) end,
            widget = wibox.container.background })
        local detail = item.title == "" and item.message or item.title .. "\n" .. item.message
        if #detail > 70 then awful.tooltip({ objects = { card }, text = detail }) end
        body:add(card)
    end
    if pages > 1 then
        local counter = text(page .. " / " .. pages, 9, colors.muted, 24)
        counter.align = "center"
        body:add(wibox.widget({ button("‹", function() page = page - 1; render() end, page > 1),
            counter, button("›", function() page = page + 1; render() end, page < pages),
            layout = wibox.layout.align.horizontal }))
    end
    popup.widget = wibox.widget({ body, margins = 12, widget = wibox.container.margin })
    style.reveal(popup)
    place()
end

local function compact(value, limit)
    local cleaned = tostring(value or ""):gsub("[%c%s]+", " "):match("^%s*(.-)%s*$")
    if not utf8.len(cleaned) then return "" end
    local cut = utf8.offset(cleaned, limit + 1)
    return cut and (cleaned:sub(1, cut - 1) .. "…") or cleaned
end

local function thumbnail(icon)
    if not icon then return end
    if type(icon) == "string" then
        if icon:sub(1, 7) == "file://" then
            icon = icon:sub(8):gsub("%%(%x%x)", function(byte) return string.char(tonumber(byte, 16)) end)
        elseif not gears.filesystem.file_readable(icon) then
            icon = require("menubar.utils").lookup_icon(icon)
        end
        if not icon then return end
    end
    local source, err = gears.surface.load_uncached_silently(icon)
    if err or not source then return end
    local width, height = gears.surface.get_size(source)
    if width <= 0 or height <= 0 then return end
    local cairo = require("lgi").cairo
    local result = cairo.ImageSurface.create(cairo.Format.ARGB32, 28, 28)
    local cr = cairo.Context(result)
    local scale = math.min(28 / width, 28 / height)
    cr:translate((28 - width * scale) / 2, (28 - height * scale) / 2)
    cr:scale(scale, scale)
    cr:set_source_surface(source, 0, 0)
    cr:paint()
    return result
end

function M.start()
    if M.started then publish(); return end
    M.started = true
    local previous = naughty.config.notify_callback
    naughty.config.notify_callback = function(args)
        if previous then args = previous(args) end
        if not args then return end
        local preset = args.preset or {}
        local app = compact(args.appname or preset.appname or "System", 45)
        args.shape = args.shape or function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 14) end
        args.margin = args.margin or 13
        args.icon_size = args.icon_size or 40
        args.border_width = args.border_width or 1
        if not args.icon and not preset.icon then
            args.icon = require("menubar.utils").lookup_icon(app:lower())
                or require("menubar.utils").lookup_icon("dialog-information")
        end
        local title = compact(args.title or preset.title, 120)
        local message = compact(args.text or preset.text, 240)
        local last = history[1]
        if (title ~= "" or message ~= "") and not
            (last and last.app == app and last.title == title and last.message == message) then
            table.insert(history, 1, { app = app ~= "" and app or "System", title = title,
                message = message, time = os.date("%H:%M"), icon = thumbnail(args.icon or preset.icon) })
            if #history > 40 then table.remove(history) end
            if popup.visible then render() else unread = math.min(40, unread + 1) end
            publish()
        end
        return args
    end
    publish()
end

function M.toggle()
    if popup.visible then hide(); return end
    unread, page = 0, 1
    publish()
    anchor = mouse.coords()
    local s = mouse.screen or awful.screen.focused()
    popup.screen = s
    below = s.workarea.y + 8
    for _, bar in ipairs(client.get(s)) do
        if bar.class == "Polybar" then
            local geometry = bar:geometry()
            if anchor.x >= geometry.x and anchor.x <= geometry.x + geometry.width then
                below = geometry.y + geometry.height + 8
                break
            end
        end
    end
    render()
end

return M
