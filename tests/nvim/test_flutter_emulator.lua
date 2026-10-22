-- Run with: nvim --headless -u NONE -l tests/nvim/test_flutter_emulator.lua
vim.opt.rtp:prepend(vim.fn.getcwd() .. "/config/nvim")
local module = dofile("config/nvim/lua/util/flutter-emulator.lua")
local original = {
   system = vim.system,
   schedule = vim.schedule,
   defer_fn = vim.defer_fn,
   notify = vim.notify,
   select = vim.ui.select,
   exepath = vim.fn.exepath,
   jobstart = vim.fn.jobstart,
}

local function scenario(options)
   local calls, resets, notices = {}, {}, {}
   local selects, polls = 0, 0
   vim.schedule = function(fn)
      fn()
   end
   vim.defer_fn = function(fn)
      fn()
   end
   vim.notify = function(message)
      table.insert(notices, message)
   end
   vim.fn.exepath = function(name)
      return "/fake/" .. name
   end
   vim.fn.jobstart = function(args, _)
      error("reset must never launch an emulator")
   end
   vim.ui.select = function(items, _, callback)
      selects = selects + 1
      if selects == 1 then
         if options.cancel_selection then
            callback(nil)
         else
            callback(items[1])
         end
      else
         assert(items[1] == "Cancelar", "default must cancel")
         callback(options.confirm and items[2] or items[1])
      end
   end
   vim.system = function(args, _, callback)
      table.insert(calls, args)
      local result = { code = 0, stdout = "", stderr = "" }
      if args[2] == "-list-avds" then
         result.stdout = options.empty and "" or "Beambollow\nOther_AVD\n"
      elseif args[1] == "/fake/python3" then
         assert(args[2]:match("flutter%-avd%-reset%.py$"))
         table.insert(resets, args)
      elseif args[2] == "devices" then
         polls = polls + 1
         result.stdout = "List of devices attached\nphysical-phone\tdevice\n"
         if options.running and (polls <= 2 or options.never_stops) then
            result.stdout = result.stdout .. "emulator-5554\t" .. (options.offline and "offline" or "device") .. "\n"
         end
      elseif args[4] == "emu" and args[5] == "avd" then
         result.stdout = (options.other_avd and "Other_AVD" or "Beambollow") .. "\r\nOK\r\n"
      elseif args[5] == "kill" then
         assert(args[3] == "emulator-5554", "never stop a physical phone")
         if options.stop_fails then
            result.code = 1
         end
      else
         error("Unexpected command: " .. vim.inspect(args))
      end
      callback(result)
   end
   module.wipe()
   return calls, resets, notices
end

local _, resets = scenario({ cancel_selection = true })
assert(#resets == 0)
local calls
calls, resets = scenario({})
assert(#resets == 0 and #calls == 1, "cancel must not inspect or stop devices")
_, resets = scenario({ confirm = true, empty = true })
assert(#resets == 0)
_, resets = scenario({ confirm = true })
assert(#resets == 1)
assert(resets[1][1] == "/fake/python3" and resets[1][3] == "Beambollow" and #resets[1] == 3)
calls, resets = scenario({ confirm = true, running = true })
assert(#resets == 1 and #calls == 7, "wait for selected emulator to stop before wiping")
calls, resets = scenario({ confirm = true, running = true, other_avd = true })
assert(#resets == 1 and #calls == 4, "leave other AVDs running")
_, resets = scenario({ confirm = true, running = true, offline = true })
assert(#resets == 0, "do not wipe when an offline emulator cannot be identified")
_, resets = scenario({ confirm = true, running = true, stop_fails = true })
assert(#resets == 0, "stop failure must prevent wipe")
_, resets = scenario({ confirm = true, running = true, never_stops = true })
assert(#resets == 0, "shutdown timeout must prevent wipe")

vim.system, vim.schedule, vim.defer_fn, vim.notify =
   original.system, original.schedule, original.defer_fn, original.notify
vim.ui.select, vim.fn.exepath, vim.fn.jobstart = original.select, original.exepath, original.jobstart

-- Register from the ordinary keymaps, with neither Dart nor Flutter loaded.
vim.g.mapleader = " "
vim.bo.filetype = ""
dofile("config/nvim/lua/config/keymaps.lua")
assert(vim.fn.exists(":FlutterWipeData") == 2)
local mapping = vim.fn.maparg(" dW", "n", false, true)
assert(
   mapping.rhs == "<cmd>FlutterWipeData<CR>" and mapping.buffer == 0,
   "reset must be available globally, including the dashboard"
)
local invoked = false
package.loaded["util.flutter-emulator"] = {
   wipe = function()
      invoked = true
   end,
}
vim.cmd("FlutterWipeData")
assert(invoked, "global command must open the reset flow without a running emulator")
package.loaded["util.flutter-emulator"] = nil
print("Flutter emulator reset checks passed (no real devices used)")
