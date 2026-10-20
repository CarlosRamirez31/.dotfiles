local M = {}
local reset_helper = vim.fs.dirname(debug.getinfo(1, "S").source:sub(2)) .. "/flutter-avd-reset.py"

local function fail(message)
   vim.notify(message, vim.log.levels.ERROR)
end

local function executable(name, directory)
   local suffix = vim.fn.has("win32") == 1 and ".exe" or ""
   local path = vim.fn.exepath(name .. suffix)
   if path ~= "" then
      return path
   end
   for _, root in ipairs({ vim.env.ANDROID_HOME or "", vim.env.ANDROID_SDK_ROOT or "" }) do
      local candidate = root .. "/" .. directory .. "/" .. name .. suffix
      if root ~= "" and vim.fn.executable(candidate) == 1 then
         return candidate
      end
   end
end

local function run(args, callback)
   local ok, err = pcall(vim.system, args, { text = true, timeout = 5000 }, function(result)
      vim.schedule(function()
         callback(result)
      end)
   end)
   if not ok then
      fail("No se pudo ejecutar la herramienta Android: " .. tostring(err))
   end
end

local function devices(adb, callback)
   run({ adb, "devices" }, function(result)
      if result.code ~= 0 then
         fail("No se pudo consultar ADB: " .. (result.stderr or ""))
         return
      end
      local emulators = {}
      for serial, state in result.stdout:gmatch("(emulator%-%d+)%s+(%S+)") do
         table.insert(emulators, { serial = serial, state = state })
      end
      callback(emulators)
   end)
end

local function stop_selected(adb, name, done)
   devices(adb, function(active)
      local function inspect(index)
         local device = active[index]
         if not device then
            done()
            return
         end
         if device.state ~= "device" then
            fail("Hay un emulador sin conexión a ADB. Ciérralo y vuelve a intentar el restablecimiento.")
            return
         end
         run({ adb, "-s", device.serial, "emu", "avd", "name" }, function(result)
            if result.code ~= 0 then
               fail("No se pudo identificar " .. device.serial .. ". Cierra los emuladores y vuelve a intentar.")
               return
            end
            if vim.trim(result.stdout:match("[^\r\n]+") or "") ~= name then
               inspect(index + 1)
               return
            end
            run({ adb, "-s", device.serial, "emu", "kill" }, function(stopped)
               if stopped.code ~= 0 then
                  fail("No se pudo cerrar " .. name .. ". Ciérralo manualmente y vuelve a intentar.")
                  return
               end
               local attempts = 0
               local function wait_for_exit()
                  devices(adb, function(remaining)
                     for _, item in ipairs(remaining) do
                        if item.serial == device.serial then
                           attempts = attempts + 1
                           if attempts >= 20 then
                              fail("El emulador no terminó de cerrar. No se inició el borrado.")
                           else
                              vim.defer_fn(wait_for_exit, 500)
                           end
                           return
                        end
                     end
                     -- Let QEMU release the AVD files after its console exits.
                     vim.defer_fn(function()
                        inspect(index + 1)
                     end, 1000)
                  end)
               end
               wait_for_exit()
            end)
         end)
      end
      inspect(1)
   end)
end

function M.wipe()
   local emulator = executable("emulator", "emulator")
   local adb = executable("adb", "platform-tools")
   local python = vim.fn.exepath("python3")
   if python == "" then
      python = vim.fn.exepath("python")
   end
   if python == "" then
      fail("Falta Python para limpiar el emulador sin arrancarlo.")
      return
   end
   if not emulator or not adb then
      fail("Falta Android Emulator o ADB. Abre Neovim dentro de Distrobox dev con el SDK configurado.")
      return
   end
   run({ emulator, "-list-avds" }, function(result)
      if result.code ~= 0 then
         fail("No se pudieron listar los emuladores: " .. (result.stderr or ""))
         return
      end
      local names = {}
      for line in result.stdout:gmatch("[^\r\n]+") do
         local name = vim.trim(line)
         if name:match("^[%w_.%-]+$") then
            table.insert(names, name)
         end
      end
      if #names == 0 then
         fail("No hay emuladores Android creados.")
         return
      end
      vim.ui.select(names, { prompt = "Restablecer emulador (borrar datos):" }, function(name)
         if not name then
            return
         end
         vim.ui.select({ "Cancelar", "Borrar datos (dejar apagado)" }, {
            prompt = "¿Borrar apps, cuentas y ajustes de " .. name .. "? Esta acción no se puede deshacer.",
         }, function(choice)
            if choice ~= "Borrar datos (dejar apagado)" then
               return
            end
            stop_selected(adb, name, function()
               run({ python, reset_helper, name }, function(reset)
                  if reset.code ~= 0 then
                     fail("No se pudo borrar " .. name .. ": " .. (reset.stderr or ""))
                     return
                  end
                  vim.notify(name .. ": datos borrados. El emulador permanece apagado.")
               end)
            end)
         end)
      end)
   end)
end

return M
