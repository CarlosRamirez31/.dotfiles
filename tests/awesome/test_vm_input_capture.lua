local clients = {}
client = { get = function() return clients end }
awesome = { register_xproperty = function() end }
package.loaded.gears = { timer = function(options)
    if options.call_now then options.callback() end
    return { stop = function() end }
end }
local function window(class, name)
    local c = { valid = true, class = class, name = name, state = "0", bindings = { "move", "resize" } }
    function c:buttons(value) if value then self.bindings = value end; return self.bindings end
    function c:get_xproperty() if self.fail then error("Viewer closed") end; return self.state end
    clients[#clients + 1] = c
    return c
end
local vm = window("Virt-manager", "arch-security on QEMU/KVM")
local other = window("Virt-manager", "win11 on QEMU/KVM")
local terminal = window("kitty", "Terminal")
local bindings = vm:buttons()
local capture = dofile("config/awesome/vm-input-capture.lua")
capture.start()
assert(vm:buttons() == bindings, "Released viewer must keep host gestures")
vm.state, other.state, terminal.state = "1", "1", "1"
capture.update()
assert(#vm:buttons() == 0, "Captured lab must pass mouse gestures to the guest")
assert(#other:buttons() == 2 and #terminal:buttons() == 2, "Other windows must be unchanged")
vm.state = "0"; capture.update()
assert(vm:buttons() == bindings, "Releasing must restore the original bindings")
vm.state = "1"; capture.update(); vm.fail = true; capture.update()
assert(vm:buttons() == bindings, "Missing capture state must restore host gestures")
vm.fail = false; capture.update(); capture.stop()
assert(vm:buttons() == bindings, "Stopping must restore host gestures")
print("VM capture: capture/release, scope, failure and stop passed")
