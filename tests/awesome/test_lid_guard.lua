local source = (arg[0]:match('^(.*)/tests/') or '.')
local callback, tick
local acquired, closed = 0, 0
local fdlist = { steal_fds = function() return {42} end }
package.preload.awful = function() return {spawn = {easy_async = function(argv, cb)
    assert(argv[2] == '--lid-inhibit-state'); callback = cb
end}} end
package.preload.gears = function() return {
    timer = function(args) tick = args.callback; tick(); return {} end,
    debug = {print_warning = function(message) error(message) end},
} end
package.preload.lgi = function() return {
    GLib = {Variant = function(kind, args)
        assert(args[1] == 'handle-lid-switch' and args[4] == 'block'); return args
    end, VariantType = {new = function() end}},
    Gio = {BusType = {SYSTEM = 1}, DBusCallFlags = {NONE = 0},
        bus_get_sync = function() return {call_with_unix_fd_list_sync = function()
            acquired = acquired + 1
            return {get_child_value = function() return {get_handle = function() return 0 end} end}, fdlist
        end} end},
    GioUnix = {InputStream = {new = function(fd, own)
        assert(fd == 42 and own)
        return {close = function() closed = closed + 1 end}
    end}},
} end
local guard = dofile(source .. '/config/awesome/lid-guard.lua')
guard.start(); callback('1\n', '', '', 0)
assert(acquired == 1 and closed == 0)
tick(); callback('1\n', '', '', 0)
assert(acquired == 1, 'Do not acquire duplicate inhibitors')
tick(); callback('', '', '', 1)
assert(closed == 0, 'A failed query must preserve the existing inhibitor')
tick(); callback('0\n', '', '', 0)
assert(closed == 1, 'Release lid handling when the external display disappears or policy changes')
tick(); callback('1\n', '', '', 0)
assert(acquired == 2)
print('Lid guard: acquisition, reuse, query failure and release passed')
