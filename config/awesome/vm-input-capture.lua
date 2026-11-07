-- Disable host mouse gestures only while SPICE actually owns the keyboard.
local gears = require("gears")
local M = { saved = setmetatable({}, { __mode = "k" }) }
local property = "_DOTFILES_VM_KEYBOARD_CAPTURED"

function M.matches(c)
    return c.valid and c.class == "Virt-manager" and (c.name or ""):match("^arch%-security on ") ~= nil
end

function M.restore(c)
    if M.saved[c] then
        if c.valid then c:buttons(M.saved[c]) end
        M.saved[c] = nil
    end
end

function M.update()
    for _, c in ipairs(client.get()) do
        local ok, value = pcall(function() return c:get_xproperty(property) end)
        if M.matches(c) and ok and value == "1" then
            if not M.saved[c] then
                M.saved[c] = c:buttons()
                c:buttons({})
            end
        else
            M.restore(c)
        end
    end
end

function M.stop()
    if M.timer then M.timer:stop(); M.timer = nil end
    for c in pairs(M.saved) do M.restore(c) end
end

function M.start()
    if M.timer then return end
    awesome.register_xproperty(property, "string")
    M.timer = gears.timer({ timeout = 0.05, autostart = true, call_now = true, callback = M.update })
end

return M
