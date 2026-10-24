local clock, pointer, commands, writes = 0, { x = 960, y = 20 }, {}, 0
local island = { class = 'Coucou', type = 'dock', valid = true, name = 'Coucou Island | compact | 288 | 32',
    hidden = false, opacity = 1 }
local s = {}
island.screen = s
local geometry = { x = 599, y = 48, width = 720, height = 320 }
function island:geometry(value)
    if value then for k, v in pairs(value) do geometry[k] = v end; writes = writes + 1 end
    return geometry
end
function island:connect_signal() end
function island:buttons(value) if value then self._buttons = value end; return self._buttons or {} end
function island:emit_signal(signal, context) self.last_activation = { signal, context } end
local bar = { class = 'Polybar', geometry = function() return { x = 19, y = 5, width = 1881, height = 44 } end }
local clients, signals = { island, bar }, {}
client = { get = function() return clients end, connect_signal = function(name, fn) signals[name] = fn end }
mouse = { coords = function() return pointer end }
package.loaded.awful = { spawn = function(command) commands[#commands + 1] = command end,
    button = function(_, _, callback) return { callback = callback } end }
package.loaded.lgi = { GLib = { get_monotonic_time = function() return clock * 1000000 end } }
package.loaded.lgi.cairo = {
    Format = { A1 = 1 },
    ImageSurface = function(_, width, height)
        return { _native = { width = width, height = height }, finish = function() end }
    end,
    Context = function(surface)
        return { set_source_rgba = function() end,
            rectangle = function(_, x, y, w, h) surface._native.rectangle = { x, y, w, h } end,
            fill = function() end }
    end,
}
local callback
package.loaded.gears = { table = { join = function(_, button) return { button } end }, timer = function(options)
    callback = options.callback
    return { started = options.autostart, start = function(self) self.started = true end,
        stop = function(self) self.started = false end }
end }
local m = dofile('config/awesome/coucou-polybar.lua')
m.start()
assert(island.focusable, 'allow deliberate keyboard focus for the chat field')
assert(island.shape_input.width == 0 and island.shape_input.height == 0, 'hidden Awesome frame must not reserve an input zone')
callback();clock = .2;callback();assert(#commands == 0)
clock = .31;callback();assert(#commands == 1, 'open after a short deliberate hover')
for i = 1, 5 do clock = .31 + i * .05; callback() end
assert(#commands == 1, 'never spam toggle while waiting for the app')
island.name = 'Coucou Island | expanded | 640 | 160'
pointer = { x = 100, y = 600 }
clock = .6; callback();
assert(island.shape_input.width == geometry.width, 'expanded frame restores input')
assert(island.shape_input.rectangle[3] == 640, 'expanded input follows the visible panel only')
clock = 1.21; callback()
assert(#commands == 2, 'acknowledgement removes fixed 1.5 second dead time')
island.name = 'Coucou Island | compact | 288 | 32'
pointer = { x = 960, y = 20 };clock = 1.3;callback();
assert(island.shape_input.width == 0, 'collapse immediately empties the parent frame, with no leave timeout')
clock = 1.61;callback()
assert(#commands == 3, 'can reopen promptly after closing')
local before = writes
for i = 1, 30 do callback() end
assert(writes == before, 'stable polling must not reposition the window')
m.timer:stop();m.start();assert(m.timer.started, 'start recovers a stopped detector')
print('Coucou hover: debounce, acknowledgement, stable geometry and timer recovery passed')

-- Coucou restarts: the previous client's object must never disable the detector.
island.valid = false
local replacement = { class = nil, type = 'dock', valid = true, name = 'Coucou', screen = s,
    hidden = false, opacity = 1, geometry = island.geometry, connect_signal = island.connect_signal }
clients = { replacement, bar }
signals.manage(replacement)
replacement.class = 'Coucou'
replacement.name = 'Coucou Island | compact | 288 | 32'
signals['property::name'](replacement)
local count = #commands
clock = 3;callback();clock = 3.31;callback()
assert(#commands == count + 1, 'late WM_CLASS/title reattaches after Coucou restarts')
-- A different Coucou dock (Flow/Mochi) must not steal the island reference.
local other = { class = 'Coucou', type = 'dock', valid = true, name = 'Mochi', screen = s }
signals.manage(other)
replacement.name = 'Coucou Island | expanded | 640 | 160'
pointer = { x = 100, y = 600 };clock = 3.6;callback();clock = 4.21;callback()
assert(#commands == count + 2, 'unrelated Coucou windows cannot break hover dismissal')
replacement.valid = false
local recovered = { class = 'Coucou', type = 'dock', valid = true,
    name = 'Coucou Island | hidden | 184 | 0', screen = s, hidden = false, opacity = 1,
    geometry = island.geometry, connect_signal = island.connect_signal }
clients = { recovered, bar }
pointer = { x = 960, y = 20 };clock = 5;callback();clock = 5.31;callback()
assert(#commands == count + 3, 'poll recovers an island even when manage was missed')
print('Coucou hover: stale client recovery, late GTK identity and unrelated docks passed')
