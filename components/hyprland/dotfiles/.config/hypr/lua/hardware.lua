local hardware = {
    vmware = false,
}

local vendor_file = io.open("/sys/class/dmi/id/sys_vendor", "r")
if vendor_file then
    local system_vendor = vendor_file:read("*l") or ""
    vendor_file:close()
    hardware.vmware = system_vendor:lower():find("vmware", 1, true) ~= nil
end

return hardware
