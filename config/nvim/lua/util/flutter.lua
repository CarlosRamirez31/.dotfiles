local M = {}

function M.root()
   local file = vim.api.nvim_buf_get_name(0)
   return vim.fs.root(file ~= "" and file or vim.fn.getcwd(), "pubspec.yaml")
end

function M.sdk(root)
   root = root or M.root()
   local suffix = vim.fn.has("win32") == 1 and ".bat" or ""
   local project_sdk = root and (root .. "/.fvm/flutter_sdk/bin/flutter" .. suffix)
   if project_sdk and vim.fn.executable(project_sdk) == 1 then
      return project_sdk
   end
   local executable = vim.fn.exepath("flutter")
   return executable ~= "" and executable or nil
end

function M.start()
   local root = M.root()
   if not root then
      vim.notify("Abre un archivo dentro de un proyecto con pubspec.yaml.", vim.log.levels.WARN)
      return
   end
   local sdk = M.sdk(root)
   if not sdk then
      vim.notify("No se encontró Flutter. Ejecuta el instalador y abre una terminal nueva.", vim.log.levels.ERROR)
      return
   end
   vim.cmd("wall")
   require("lazy").load({ plugins = { "flutter-tools.nvim" } })
   require("flutter-tools.config").set({ flutter_path = sdk })
   require("flutter-tools.executable").reset_paths()
   require("flutter-tools").setup_project({ cwd = root })
   -- Query devices for every new session; never persist a phone's serial number.
   if require("flutter-tools.utils.config_utils").has_flutter_dependency_in_pubspec(root) then
      vim.cmd("FlutterDevices")
   else
      vim.cmd("FlutterDebug")
   end
end

return M
