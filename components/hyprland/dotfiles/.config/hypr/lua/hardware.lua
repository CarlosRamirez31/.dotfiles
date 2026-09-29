local hardware = {
    virtual_machine = false,
    vmware = false,
}

-- Use systemd's hypervisor detection so cursor behavior applies to every VM,
-- while keeping the VMware flag for its renderer-specific workarounds.
local virt_process = io.popen("systemd-detect-virt --vm 2>/dev/null", "r")
if virt_process then
    local virtualization = (virt_process:read("*l") or ""):lower()
    virt_process:close()
    hardware.virtual_machine = virtualization ~= "" and virtualization ~= "none"
    hardware.vmware = virtualization == "vmware"
end

local vendor_file = io.open("/sys/class/dmi/id/sys_vendor", "r")
if vendor_file then
    local system_vendor = vendor_file:read("*l") or ""
    vendor_file:close()
    if system_vendor:lower():find("vmware", 1, true) ~= nil then
        hardware.virtual_machine = true
        hardware.vmware = true
    end
end

return hardware
