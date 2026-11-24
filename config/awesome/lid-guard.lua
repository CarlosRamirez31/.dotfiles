-- logind can miss monitors driven by a secondary GPU. Only take over its
-- lid handling while an external output is active and docked policy is ignore.
local awful = require('awful')
local gears = require('gears')
local lgi = require('lgi')
local Gio, GLib = lgi.Gio, lgi.GLib
local UnixInputStream = Gio.UnixInputStream or lgi.GioUnix.InputStream
local M = {}
local inhibitor, busy

local function refresh()
    if busy then return end
    busy = true
    awful.spawn.easy_async({os.getenv('HOME') .. '/.local/bin/dotfiles-display', '--lid-inhibit-state'},
        function(output, _, _, code)
            busy = false
            if code ~= 0 then return end
            if output:match('^1%s*$') and not inhibitor then
                local ok, stream = pcall(function()
                    local bus = Gio.bus_get_sync(Gio.BusType.SYSTEM)
                    local reply, descriptors = bus:call_with_unix_fd_list_sync(
                        'org.freedesktop.login1', '/org/freedesktop/login1',
                        'org.freedesktop.login1.Manager', 'Inhibit',
                        GLib.Variant('(ssss)', {'handle-lid-switch', 'dotfiles-displays',
                            'Monitores externos activos; política de tapa: no suspender', 'block'}),
                        GLib.VariantType.new('(h)'), Gio.DBusCallFlags.NONE, 2000, nil, nil)
                    local handle = reply:get_child_value(0):get_handle()
                    -- Transfer ownership so releasing the stream closes the only
                    -- descriptor, without waiting for Lua to collect the FD list.
                    local fds = descriptors:steal_fds()
                    return UnixInputStream.new(fds[handle + 1], true)
                end)
                if ok then inhibitor = stream
                else gears.debug.print_warning('Lid guard: ' .. tostring(stream)) end
            elseif output:match('^0%s*$') and inhibitor then
                inhibitor:close(nil)
                inhibitor = nil
            end
        end)
end

function M.start()
    if M.started then return end
    M.started = true
    M.timer = gears.timer({timeout = 3, autostart = true, call_now = true, callback = refresh})
end

return M
