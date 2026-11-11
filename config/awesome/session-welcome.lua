local awful = require('awful')
local gears = require('gears')
local wibox = require('wibox')
local style = require('menu-style')
local colors = style.colors
local M = {}
local runtime = os.getenv('XDG_RUNTIME_DIR')
local marker = runtime and (runtime .. '/dotfiles-welcome-shown')
local token = 0
local popup = awful.popup({ visible = false, ontop = true, type = 'notification',
    minimum_width = 390, maximum_width = 390, bg = '#171722f5', fg = colors.text,
    border_width = 1, border_color = colors.border,
    shape = function(cr, w, h) gears.shape.rounded_rect(cr, w, h, 18) end,
    widget = wibox.widget.textbox() })
local hide = gears.timer({ timeout = 9, single_shot = true, callback = function() popup.visible = false end })
popup:connect_signal('mouse::enter', function() if hide.started then hide:stop() end end)
popup:connect_signal('mouse::leave', function() hide:again() end)
local function dismiss()
    token = token + 1; popup.visible = false
    if hide.started then hide:stop() end
end
function M.show()
    token = token + 1
    local generation = token
    local hour = tonumber(os.date('%H'))
    local greeting = hour < 12 and 'Good morning' or hour < 18 and 'Good afternoon' or 'Good evening'
    local name = os.getenv('USER') or ''
    local music = style.text('Your desktop is ready.', 9, colors.muted, 30)
    local clock = style.text(os.date('%H:%M'), 35, colors.text, 62)
    local rows = wibox.widget({
        { style.text('WELCOME BACK', 9, colors.lavender, 24), nil, style.action('×', dismiss),
            layout = wibox.layout.align.horizontal },
        clock, style.text(os.date('%A, %d %B'), 10, colors.muted, 25),
        style.text(greeting .. ', ' .. name .. '.', 12, colors.lavender, 35), music,
        { style.action('󰒓  Controls', function() dismiss(); require('desktop-panels').toggle('system') end),
            style.action('󰇚  Downloads', function() dismiss(); require('recent-downloads').toggle() end),
            spacing = 8, layout = wibox.layout.flex.horizontal },
        spacing = 6, layout = wibox.layout.fixed.vertical })
    popup.screen = awful.screen.focused()
    popup.widget = wibox.container.margin(rows, 20, 20, 16, 16)
    style.reveal(popup)
    local area = popup.screen.workarea
    popup.x = area.x + math.floor((area.width - popup.width) / 2)
    popup.y = area.y + math.min(60, math.floor(area.height * .08))
    hide:again()
    awful.spawn.easy_async({ os.getenv('HOME') .. '/.local/bin/dotfiles-desktop-panel', 'music' }, function(output)
        if token ~= generation then return end
        local data = {}
        for key, value in output:gmatch('([^\t\n]+)\t([^\n]*)\n') do data[key] = value end
        if data.title and data.title ~= '' then
            music.text = (data.state == 'Playing' and '󰎆  Playing · ' or '󰏤  Last track · ') .. data.title
            awful.tooltip({ objects = { music }, text = data.title .. (data.artist and (' · ' .. data.artist) or '') })
        end
    end)
end
function M.start()
    if M.started then return end
    M.started = true
    if not awesome.startup or not marker or gears.filesystem.file_readable(marker) then return end
    local file = io.open(marker, 'w')
    if not file then return end
    file:write('shown\n'); file:close()
    gears.timer.start_new(2, function() M.show(); return false end)
end
return M
