local awful = require("awful")
local gears = require("gears")
local wibox = require("wibox")
local style = require("menu-style")
local colors = style.colors

local M = {}
local helper = os.getenv("HOME") .. "/.local/bin/dotfiles-audio-mixer"
local anchor, generation = nil, 0
local pending, dragging, applying = false, false, false
local timer
local previous, page = nil, 1
local popup = awful.popup({ visible = false, ontop = true, type = "dialog",
    minimum_width = 350, maximum_width = 350, bg = colors.base, fg = colors.text,
    border_width = 1, border_color = colors.border, widget = wibox.widget.textbox(),
    shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 14) end,
})

local function hide()
    generation = generation + 1
    if timer.started then timer:stop() end
    if dragging then mousegrabber.stop(); dragging = false end
    popup.visible, pending, applying = false, false, false
end

local refresh
local function apply(id, value)
    if applying or not popup.visible then return end
    applying = true
    local token = generation
    awful.spawn.easy_async({ helper, id, tostring(value) }, function()
        if token ~= generation then return end
        applying = false
        previous = nil
        refresh()
    end)
end

local function application(id, muted, level, name, change)
    change = change or apply
    local accent = muted and colors.muted or colors.lavender
    local title = style.text(name, 10, colors.text, 24)
    local value = wibox.widget({ text = string.format("%d%%", level), font = "JetBrainsMono Nerd Font Bold 9",
        forced_width = 43, align = "right", widget = wibox.widget.textbox })
    local meter = wibox.widget({ max_value = 100, value = math.min(100, level), forced_height = 10,
        color = accent, background_color = colors.raised,
        shape = gears.shape.rounded_bar, bar_shape = gears.shape.rounded_bar, widget = wibox.widget.progressbar })
    local track = wibox.container.margin(meter, 0, 0, 6, 6)
    track:connect_signal("button::press", function(_, x, _, button, _, geometry)
        if button ~= 1 or dragging or applying then return end
        local left, width = mouse.coords().x - x, geometry.widget_width
        if width <= 0 then return end
        local function preview(relative)
            local percent = math.floor(math.max(0, math.min(1, relative / width)) * 100 + .5)
            value.text = percent .. "%"
            meter.value = percent
            return percent
        end
        dragging = true
        preview(x)
        mousegrabber.run(function(state)
            local percent = preview(state.x - left)
            if state.buttons[1] then return true end
            dragging = false
            change(id, percent)
            return false
        end, "hand1")
    end)
    local header = wibox.widget({ nil, title, value, layout = wibox.layout.align.horizontal })
    local content = wibox.widget({ header, track, spacing = 1, layout = wibox.layout.fixed.vertical })
    local mute = wibox.widget({ style.icon(muted and "󰖁" or "󰕾", 14, accent, 30, 30),
        bg = colors.raised, forced_width = 30, forced_height = 30,
        shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 7) end,
        widget = wibox.container.background })
    mute:buttons(awful.button({}, 1, function() change(id, "mute") end))
    return wibox.widget({ { { nil, wibox.container.margin(content, 0, 9, 0, 0),
            wibox.container.place(mute, "center", "center"),
            layout = wibox.layout.align.horizontal }, margins = 9, widget = wibox.container.margin },
        bg = colors.surface, shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 9) end,
        widget = wibox.container.background })
end

-- The dashboard shares these controls with the full, paginated mixer.
function M.section(output, change)
    local rows = wibox.layout.fixed.vertical()
    rows.spacing = 7
    local count = 0
    for id, mute, volume, name in output:gmatch("(%x+)\t([01])\t(%d+)\t([^\n]*)\n") do
        count = count + 1
        if count <= 3 then rows:add(application(id, mute == "1", tonumber(volume), name, change)) end
    end
    if count == 0 then rows:add(style.text("No apps playing audio", 9, colors.muted, 30)) end
    if count > 3 then rows:add(style.action("All applications   ›", function()
        require("desktop-panels").hide()
        M.toggle()
    end)) end
    return rows
end

function M.is_dragging() return dragging end
function M.cancel_drag()
    if dragging then mousegrabber.stop(); dragging = false end
end

local function render(output, failed)
    local rows = wibox.layout.fixed.vertical()
    rows.spacing = 8
    rows:add(wibox.widget({ style.text("App volume", 11, colors.lavender, 28), nil,
        style.action("×", hide, colors.muted), layout = wibox.layout.align.horizontal }))
    local entries = {}
    for id, mute, volume, name in output:gmatch("(%x+)\t([01])\t(%d+)\t([^\n]*)\n") do
        entries[#entries + 1] = { id, mute == "1", tonumber(volume), name }
    end
    if #entries == 0 then
        rows:add(style.text(failed and "Audio unavailable" or "No apps playing audio", 9, colors.muted, 29))
    end
    local count = math.max(1, math.min(8, math.floor((popup.screen.workarea.height - 110) / 75)))
    local pages = math.max(1, math.ceil(#entries / count))
    page = math.min(page, pages)
    for index = (page - 1) * count + 1, math.min(page * count, #entries) do
        rows:add(application(table.unpack(entries[index])))
    end
    if pages > 1 then
        local label = style.text(page .. " / " .. pages, 9, colors.muted, 27)
        label.align = "center"
        rows:add(wibox.widget({
            page > 1 and style.action("‹", function() page = page - 1; render(output, failed) end) or nil,
            label,
            page < pages and style.action("›", function() page = page + 1; render(output, failed) end) or nil,
            layout = wibox.layout.align.horizontal,
        }))
    end
    popup.widget = wibox.widget({ rows, margins = 11, widget = wibox.container.margin })
    style.reveal(popup)
    style.place_below_bar(popup, anchor)
end

refresh = function()
    if pending or dragging or applying then return end
    local token = generation
    pending = true
    awful.spawn.easy_async({ helper }, function(output, _, _, code)
        if token ~= generation then return end
        pending = false
        if dragging or applying then return end
        local data = code == 0 and output or false
        if data ~= previous then
            previous = data
            render(data or "", data == false)
        end
    end)
end
timer = gears.timer({ timeout = 1, callback = refresh })
popup:connect_signal("property::height", function()
    if popup.visible and anchor then style.place_below_bar(popup, anchor) end
end)

function M.toggle()
    if popup.visible or pending then hide(); return end
    popup.screen = mouse.screen or awful.screen.focused()
    anchor = mouse.coords()
    previous, page = nil, 1
    refresh()
    timer:start()
end

return M
