-- Controls embedded in the existing system dashboard; no background polling.
local awful = require('awful')
local gears = require('gears')
local wibox = require('wibox')
local style = require('menu-style')
local mixer = require('audio-mixer')
local colors = style.colors
local M = {}
local helper = os.getenv('HOME') .. '/.local/bin/dotfiles-polybar'
local audio = os.getenv('HOME') .. '/.local/bin/dotfiles-audio-mixer'
local dragging, applying, epoch = false, false, 0
local changed

function M.busy() return dragging or applying or mixer.is_dragging() end
function M.close()
    epoch = epoch + 1
    if dragging then mousegrabber.stop() end
    mixer.cancel_drag()
    dragging, applying, changed = false, false, nil
end

local function apply(command)
    if applying then return end
    applying = true
    local token = epoch
    awful.spawn.easy_async(command, function(_, stderr, _, code)
        if token ~= epoch then return end
        applying = false
        if code ~= 0 then
            require('naughty').notify({ title = 'Control unavailable', text = stderr ~= '' and stderr or 'Please try again.' })
        end
        if changed then changed() end
    end)
end

local function slider(label, level, accent, command, muted)
    if not level then return style.text(label .. ' · Unavailable', 9, colors.muted, 35) end
    local value = style.text(muted and 'Muted' or (level .. '%'), 9, colors.muted, 25)
    value.align, value.forced_width = 'right', 55
    local bar = wibox.widget({ max_value = 100, value = math.min(level, 100), color = accent,
        background_color = colors.raised, forced_height = 7,
        shape = gears.shape.rounded_bar, bar_shape = gears.shape.rounded_bar, widget = wibox.widget.progressbar })
    local track = wibox.container.margin(bar, 0, 0, 9, 9)
    track:connect_signal('button::press', function(_, x, _, button, _, geometry)
        if button ~= 1 or M.busy() or geometry.widget_width <= 0 then return end
        local left, width = mouse.coords().x - x, geometry.widget_width
        local function preview(px)
            local target = math.floor(math.max(0, math.min(1, px / width)) * 100 + .5)
            value.text, bar.value = target .. '%', target
            return target
        end
        dragging = true
        preview(x)
        mousegrabber.run(function(state)
            local target = preview(state.x - left)
            if state.buttons[1] then return true end
            dragging = false
            apply(command(target))
            return false
        end, 'hand1')
    end)
    return wibox.widget({ { style.text(label, 10, accent, 25), nil, value,
        layout = wibox.layout.align.horizontal }, track, layout = wibox.layout.fixed.vertical })
end

function M.refresh(callback, on_change)
    changed = on_change
    local token, pending, data = epoch, 3, {}
    local function query(key, command)
        awful.spawn.easy_async(command, function(output, _, _, code)
            if token ~= epoch then return end
            data[key] = code == 0 and output or ''
            pending = pending - 1
            if pending ~= 0 then return end
            local rows = wibox.layout.fixed.vertical()
            rows.spacing = 10
            rows:add(style.text('CONTROLS', 11, colors.lavender, 30))
            local volume = tonumber(data.volume:match('^Volume:%s+([%d.]+)'))
            local muted = data.volume:find('[MUTED]', 1, true) ~= nil
            rows:add(slider((muted and '󰖁' or '󰕾') .. '  Output volume', volume and math.floor(volume * 100 + .5), colors.lavender,
                function(v) return { 'wpctl', 'set-volume', '--limit', '1', '@DEFAULT_AUDIO_SINK@', v .. '%' } end,
                data.volume:find('[MUTED]', 1, true)))
            rows:add(slider('󰃠  Brightness', tonumber(data.brightness:match('(%d+)%%')), colors.yellow,
                function(v) return { helper, '--brightness', 'set', tostring(v) } end))
            rows:add(wibox.widget({ style.action(muted and '󰖁  Muted · On' or '󰕾  Mute · Off', function()
                apply({ 'wpctl', 'set-mute', '@DEFAULT_AUDIO_SINK@', 'toggle' }) end, muted and colors.lavender or colors.muted),
                style.action(require('naughty').is_suspended() and '󰂛  Quiet · On' or '󰂚  Quiet · Off', function()
                    local notices = require('notification-center')
                    notices.set_quiet(not require('naughty').is_suspended())
                    if changed then changed() end
                end), spacing = 7, layout = wibox.layout.flex.horizontal }))
            rows:add(style.action('󰓃  Outputs & profiles   ·   Alt+F5', function()
                require('desktop-panels').hide()
                require('audio-devices').toggle()
            end, colors.lavender))
            rows:add(style.action('󰍬  Inputs   ›', function()
                require('desktop-panels').hide()
                require('audio-devices').toggle('inputs')
            end, colors.lavender))
            rows:add(style.text('APPLICATION AUDIO', 9, colors.muted, 25))
            rows:add(mixer.section(data.apps, function(id, v) apply({ audio, id, tostring(v) }) end))
            rows:add(style.action('󰒓  Focus current window   ·   Alt+F10', function()
                require('desktop-panels').hide()
                require('window-actions').toggle_focus()
            end, colors.lavender))
            rows:add(style.action('󰂚  Notifications   ›', function()
                require('desktop-panels').hide()
                require('notification-center').toggle()
            end))
            callback(rows)
        end)
    end
    query('volume', { 'wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@' })
    query('brightness', { helper, '--brightness', 'status' })
    query('apps', { audio })
end
return M
