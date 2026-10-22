local M = {}
local helper = vim.fs.dirname(debug.getinfo(1, "S").source:sub(2)) .. "/nvim-trash.py"

local function notify(message, level)
   vim.notify(message, level or vim.log.levels.INFO, { title = "Papelera de Neovim" })
end

local function run(arguments, callback)
   local python = vim.fn.exepath("python3")
   if python == "" then
      python = vim.fn.exepath("python")
   end
   if python == "" then
      notify("Falta Python. Se canceló la operación; no se borró ningún archivo.", vim.log.levels.ERROR)
      return
   end
   local command = { python, helper }
   vim.list_extend(command, arguments)
   local ok, err = pcall(vim.system, command, { text = true }, function(result)
      vim.schedule(function()
         local decoded, data = pcall(vim.json.decode, result.stdout or "")
         if not decoded or type(data) ~= "table" or result.code ~= 0 or data.error then
            local message = type(data) == "table" and data.error or result.stderr
            notify(message or "Error de papelera", vim.log.levels.ERROR)
            return
         end
         for _, error in ipairs(data.errors or {}) do
            notify(error.path .. ": " .. error.error, vim.log.levels.ERROR)
         end
         if callback then
            callback(data)
         end
      end)
   end)
   if not ok then
      notify(tostring(err), vim.log.levels.ERROR)
   end
end

local function refresh(paths)
   if not _G.Snacks then
      return
   end
   local tree = require("snacks.explorer.tree")
   local refreshed = {}
   for _, path in ipairs(paths) do
      local directory = vim.fs.dirname(path)
      if not refreshed[directory] then
         tree:refresh(directory)
         refreshed[directory] = true
      end
   end
   -- Use the explorer's own debounced refresh. The filesystem watcher can
   -- report the same move before this callback; both must share one finder
   -- run instead of forcing overlapping rebuilds of the visible tree.
   require("snacks.explorer.watch").refresh()
end

local function close_deleted_buffers(entries)
   for _, buf in ipairs(vim.api.nvim_list_bufs()) do
      local name = vim.api.nvim_buf_get_name(buf)
      for _, entry in ipairs(entries) do
         local path = entry.original
         local inside = entry.kind == "directory" and name:sub(1, #path + 1) == path .. "/"
         -- Preserve unsaved text even when its on-disk file was trashed.
         if (name == path or inside) and not vim.bo[buf].modified then
            if _G.Snacks then
               Snacks.bufdelete({ buf = buf })
            else
               pcall(vim.api.nvim_buf_delete, buf, {})
            end
            break
         end
      end
   end
end

function M.put(paths, callback)
   local arguments = { "put", "--" }
   vim.list_extend(arguments, paths)
   run(arguments, function(data)
      local entries = data.entries or {}
      close_deleted_buffers(entries)
      if #entries > 0 then
         notify(#entries .. " entrada(s) en papelera durante 5 horas. Space f u para recuperar.")
         refresh(vim.tbl_map(function(entry)
            return entry.original
         end, entries))
      end
      if callback then
         callback(entries)
      end
   end)
end

function M.open(callback)
   run({ "list" }, function(data)
      if #data.entries == 0 then
         notify("La papelera está vacía.")
         return
      end
      vim.ui.select(data.entries, {
         prompt = "Papelera · selecciona para restaurar en su ruta original:",
         format_item = function(entry)
            local minutes = math.max(0, math.ceil((entry.expires_at - os.time()) / 60))
            local kind = entry.kind == "directory" and "Carpeta" or "Archivo"
            return string.format(
               "[%s] %s · quedan %dh %02dm",
               kind,
               entry.original,
               math.floor(minutes / 60),
               minutes % 60
            )
         end,
      }, function(entry)
         if not entry then
            return
         end
         run({ "restore", entry.id }, function(result)
            notify("Restaurado: " .. result.restored.original)
            refresh({ result.restored.original })
            if callback then
               callback()
            end
         end)
      end)
   end)
end

function M.snacks_delete(picker)
   local paths = vim.tbl_map(Snacks.picker.util.path, picker:selected({ fallback = true }))
   if #paths == 0 then
      return
   end
   Snacks.picker.util.confirm("¿Mover " .. #paths .. " selección(es) a la papelera durante 5 horas?", function()
      M.put(paths, function()
         if not picker.closed then
            picker.list:set_selected()
         end
      end)
   end)
end

function M.telescope_delete(prompt_bufnr)
   local picker = require("telescope.actions.state").get_current_picker(prompt_bufnr)
   local selected = require("telescope._extensions.file_browser.utils").get_selected_files(prompt_bufnr, true)
   local paths = {}
   for _, path in ipairs(selected) do
      local absolute = path:absolute()
      if absolute == vim.fs.dirname(picker.finder.path) or absolute == picker.finder.cwd then
         notify("No se puede borrar la carpeta de navegación actual.", vim.log.levels.ERROR)
         return
      end
      table.insert(paths, absolute)
   end
   if #paths == 0 then
      return
   end
   vim.ui.select({ "Cancelar", "Mover a papelera (5 horas)" }, { prompt = "¿Borrar la selección?" }, function(choice)
      if choice ~= "Mover a papelera (5 horas)" then
         return
      end
      M.put(paths, function()
         pcall(picker.refresh, picker, picker.finder)
      end)
   end)
end

function M.setup()
   vim.api.nvim_create_user_command("NvimTrash", function()
      M.open()
   end, {
      desc = "Ver papelera y recuperar archivos (5 horas)",
      force = true,
   })
   vim.keymap.set("n", "<leader>fu", function()
      M.open()
   end, { desc = "Papelera: recuperar archivos (5h)" })
   if M.timer then
      return
   end
   -- Also clean while editing on platforms without a user systemd instance.
   M.timer = vim.uv.new_timer()
   M.timer:start(
      60000,
      60000,
      vim.schedule_wrap(function()
         run({ "purge" })
      end)
   )
   M.timer:unref()
end

return M
