return {
   {
      "akinsho/flutter-tools.nvim",
      dependencies = {
         "nvim-lua/plenary.nvim",
         "stevearc/dressing.nvim",
         "mfussenegger/nvim-dap",
      },
      ft = { "dart" },
      config = function()
         local function android_emulator()
            local executable_name = vim.fn.has("win32") == 1 and "emulator.exe" or "emulator"
            local executable = vim.fn.exepath(executable_name)
            if executable ~= "" then
               return executable
            end

            local separator = package.config:sub(1, 1)
            local sdk_roots = {}
            local function add_sdk_root(path)
               if path and path ~= "" then
                  table.insert(sdk_roots, path)
               end
            end

            add_sdk_root(vim.env.ANDROID_SDK_ROOT)
            add_sdk_root(vim.env.ANDROID_HOME)
            add_sdk_root(vim.env.LOCALAPPDATA and (vim.env.LOCALAPPDATA .. separator .. "Android" .. separator .. "Sdk"))
            add_sdk_root(vim.env.HOME and (vim.env.HOME .. separator .. "Android" .. separator .. "Sdk"))
            add_sdk_root(
               vim.env.HOME and (vim.env.HOME .. separator .. "Library" .. separator .. "Android" .. separator .. "sdk")
            )

            for _, sdk_root in ipairs(sdk_roots) do
               local candidate = sdk_root .. separator .. "emulator" .. separator .. executable_name
               if vim.fn.executable(candidate) == 1 then
                  return candidate
               end
            end
         end

         require("flutter-tools").setup({
            ui = {
               border = "rounded",
            },
            decorations = {
               statusline = {
                  app_version = true,
                  device = true,
               },
            },
            dev_log = {
               enabled = true,
               open_cmd = "tabedit",
            },
            widget_guides = {
               enabled = true,
            },
            lsp = {
               color = { enabled = true },
               on_attach = function(_, bufnr)
                  local function map(keys, cmd, desc)
                     vim.keymap.set("n", keys, cmd, { buffer = bufnr, desc = desc })
                  end

                  -- Flutter actions
                  map("<leader>dr", "<cmd>FlutterHotReload<CR>", "Flutter Hot Reload")
                  map("<leader>ds", "<cmd>FlutterHotRestart<CR>", "Flutter Hot Restart")
                  map("<leader>dq", "<cmd>FlutterQuit<CR>", "Flutter Quit")
                  map("<leader>dd", "<cmd>FlutterDevices<CR>", "Flutter Devices")
                  map("<leader>dl", "<cmd>FlutterLog<CR>", "Flutter Logs")

                  map("<leader>de", function()
                     local emulator = android_emulator()
                     if not emulator then
                        vim.notify(
                           "No se encontró Android Emulator. Configura ANDROID_SDK_ROOT o ANDROID_HOME.",
                           vim.log.levels.ERROR
                        )
                        return
                     end

                     vim.fn.jobstart({ emulator, "-list-avds" }, {
                        stdout_buffered = true,
                        on_stdout = function(_, data)
                           if data then
                              -- Limpiar ^M (\r) y filtrar líneas vacías o ruidosas
                              local avds = vim.tbl_filter(
                                 function(item)
                                    return item and item ~= "" and not item:match("INFO")
                                 end,
                                 vim.tbl_map(function(line)
                                    return line:gsub("\r", "")
                                 end, data)
                              )

                              -- Menú interactivo
                              vim.ui.select(avds, { prompt = "Selecciona un emulador AVD:" }, function(choice)
                                 if choice then
                                    vim.fn.jobstart({ emulator, "-avd", choice }, { detach = true })
                                 end
                              end)
                           end
                        end,
                        on_stderr = function(_, data)
                           if data then
                              vim.notify(table.concat(data, "\n"), vim.log.levels.ERROR)
                           end
                        end,
                     })
                  end, "Listar y ejecutar emulador Android")
               end,
            },
            debugger = {
               enabled = true,
               run_via_dap = true, -- true: DAP | false: flutter CLI
            },
            closing_tags = {
               highlight = "ErrorMsg",
               prefix = ">>",
            },
         })
      end,
   },
}
