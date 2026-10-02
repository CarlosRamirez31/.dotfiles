local hardware = {
    vmware = false,
}

-- Detect VMware for its renderer-specific workarounds.
local virt_process = io.popen("systemd-detect-virt --vm 2>/dev/null", "r")
if virt_process then
    local virtualization = (virt_process:read("*l") or ""):lower()
    virt_process:close()
    hardware.vmware = virtualization == "vmware"
end

local vendor_file = io.open("/sys/class/dmi/id/sys_vendor", "r")
if vendor_file then
    local system_vendor = vendor_file:read("*l") or ""
    vendor_file:close()
    if system_vendor:lower():find("vmware", 1, true) ~= nil then
        hardware.vmware = true
    end
end

return hardware
