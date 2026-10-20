return {
   {
      "akinsho/flutter-tools.nvim",
      dependencies = { "nvim-lua/plenary.nvim", "stevearc/dressing.nvim", "mfussenegger/nvim-dap" },
      ft = { "dart" },
      cmd = {
         "FlutterRun",
         "FlutterDebug",
         "FlutterDevices",
         "FlutterEmulators",
         "FlutterReload",
         "FlutterRestart",
         "FlutterQuit",
         "FlutterLogToggle",
         "FlutterPubGet",
         "FlutterOpenDevTools",
      },
      config = function()
         local sdk = require("util.flutter").sdk()
         if not sdk then
            vim.notify("Falta Flutter en PATH. Instala el SDK y reinicia Neovim.", vim.log.levels.WARN)
            return
         end
         require("flutter-tools").setup({
            -- Resolve the SDK from PATH, or the project's .fvm/flutter_sdk.
            flutter_path = sdk,
            root_patterns = { "pubspec.yaml", ".git" },
            ui = { border = "rounded" },
            decorations = { statusline = { app_version = true, device = true } },
            dev_log = { enabled = true, open_cmd = "botright 12split", focus_on_open = false },
            widget_guides = { enabled = true },
            emulators = {
               launcher = function(emulator)
                  local launcher = vim.fn.exepath("flutter-emulator")
                  if launcher == "" then
                     return
                  end
                  local args = { emulator.id }
                  if emulator.cold_boot then
                     table.insert(args, "-no-snapshot-load")
                  end
                  return { command = launcher, args = args }
               end,
            },
            lsp = {
               color = { enabled = vim.fn.has("nvim-0.12") == 0 },
               on_attach = function(_, bufnr)
                  if vim.fn.has("nvim-0.12") == 1 then
                     vim.lsp.document_color.enable(true, { bufnr = bufnr })
                  end
               end,
            },
            debugger = {
               enabled = true,
               exception_breakpoints = { "Unhandled" },
               register_configurations = function()
                  local root = require("util.flutter").root()
                  if root and vim.fn.filereadable(root .. "/.vscode/launch.json") == 1 then
                     require("dap.ext.vscode").load_launchjs(root .. "/.vscode/launch.json", { dart = { "dart" } })
                  end
               end,
            },
            closing_tags = { highlight = "ErrorMsg", prefix = ">>" },
         })

         local group = vim.api.nvim_create_augroup("UserFlutterKeys", { clear = true })
         vim.api.nvim_create_autocmd("FileType", {
            group = group,
            pattern = "dart",
            callback = function(event)
               local function map(keys, action, desc)
                  vim.keymap.set("n", keys, action, { buffer = event.buf, desc = desc })
               end
               map("<leader>dr", "<cmd>FlutterReload<CR>", "Flutter: Hot Reload")
               map("<leader>ds", "<cmd>FlutterRestart<CR>", "Flutter: Hot Restart")
               map("<leader>dq", "<cmd>FlutterQuit<CR>", "Flutter: Quit")
               map("<leader>dd", function()
                  require("util.flutter").start()
               end, "Flutter: Select Device and Debug")
               map("<leader>dl", "<cmd>FlutterLogToggle<CR>", "Flutter: Toggle Logs")
               map("<leader>de", "<cmd>FlutterEmulators<CR>", "Flutter: Launch Emulator")
               map("<leader>dp", "<cmd>FlutterPubGet<CR>", "Flutter: Pub Get")
               map("<F4>", "<cmd>FlutterReload<CR>", "Flutter: Hot Reload")
               map("<S-F4>", "<cmd>FlutterRestart<CR>", "Flutter: Hot Restart")
            end,
         })
      end,
   },
   {
      "neovim/nvim-lspconfig",
      opts = {
         -- flutter-tools owns Dart LSP; avoid a second server/Mason SDK.
         servers = { dartls = { enabled = false } },
      },
   },
}
