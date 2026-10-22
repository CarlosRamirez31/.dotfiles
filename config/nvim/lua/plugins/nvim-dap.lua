return {
   {
      "mfussenegger/nvim-dap",
      recommended = true,
      desc = "Debugging support. Requires language specific adapters to be configured. (see lang extras)",

      dependencies = {
         "rcarriga/nvim-dap-ui",
         {
            "theHamsta/nvim-dap-virtual-text",
            opts = {},
         },
      },

      keys = {
         {
            "<F5>",
            function()
               local dap = require("dap")
               if dap.session() then
                  dap.continue()
               elseif require("util.flutter").root() then
                  require("util.flutter").start()
               else
                  dap.continue()
               end
            end,
            desc = "DAP: Start / Continue",
         },
         {
            "<S-F5>",
            function()
               require("dap").terminate()
            end,
            desc = "DAP: Terminate",
         },
         {
            "<C-F5>",
            function()
               require("dap").run_last()
            end,
            desc = "DAP: Repeat Last Debug Session",
         },
         {
            "<F6>",
            function()
               require("dap").pause()
            end,
            desc = "DAP: Pause",
         },
         {
            "<F7>",
            function()
               require("dap").repl.toggle()
            end,
            desc = "DAP: Toggle REPL",
         },
         {
            "<F8>",
            function()
               require("dap").run_to_cursor()
            end,
            desc = "DAP: Run to Cursor",
         },
         {
            "<F9>",
            function()
               require("dap").toggle_breakpoint()
            end,
            desc = "DAP: Toggle Breakpoint",
         },
         {
            "<C-F9>",
            function()
               require("dap").set_breakpoint(vim.fn.input("Breakpoint condition: "))
            end,
            desc = "DAP: Conditional Breakpoint",
         },
         {
            "<S-F9>",
            function()
               require("dap").set_exception_breakpoints({ "uncaught" })
               print("🟠 Break on UNCAUGHT exceptions enabled")
            end,
            desc = "DAP: Break on Uncaught Exceptions",
         },
         {
            "<C-S-F9>",
            function()
               require("dap").set_exception_breakpoints({ "all" })
               print("🔴 Break on ALL exceptions enabled")
            end,
            desc = "DAP: Break on All Exceptions",
         },
         {
            "<C-M-F9>",
            function()
               require("dap").set_exception_breakpoints({})
               print("⚪ Break on Exceptions DISABLED")
            end,
            desc = "DAP: Disable Break on Exceptions",
         },
         {
            "<F10>",
            function()
               require("dap").step_over()
            end,
            desc = "DAP: Step Over",
         },
         {
            "<F11>",
            function()
               require("dap").step_into()
            end,
            desc = "DAP: Step Into",
         },
         {
            "<S-F11>",
            function()
               require("dap").step_out()
            end,
            desc = "DAP: Step Out",
         },
         {
            "<F12>",
            function()
               local widgets = require("dap.ui.widgets")
               widgets.hover()
            end,
            desc = "DAP: Hover variable",
         },
         {
            "<C-S-F5>",
            function()
               require("dap").restart()
            end,
            desc = "DAP: Restart Session",
         },
         {
            "<leader>db",
            function()
               require("dap").list_breakpoints()
               vim.cmd("copen")
            end,
            desc = "DAP: List Breakpoints",
         },
      },

      config = function()
         if LazyVim.has("mason-nvim-dap.nvim") then
            require("mason-nvim-dap").setup(LazyVim.opts("mason-nvim-dap.nvim"))
         end

         vim.api.nvim_set_hl(0, "DapStoppedLine", { default = true, link = "Visual" })

         for name, sign in pairs(LazyVim.config.icons.dap) do
            sign = type(sign) == "table" and sign or { sign }
            vim.fn.sign_define(
               "Dap" .. name,
               { text = sign[1], texthl = sign[2] or "DiagnosticInfo", linehl = sign[3], numhl = sign[3] }
            )
         end

         local vscode = require("dap.ext.vscode")
         local json = require("plenary.json")
         vscode.json_decode = function(str)
            return vim.json.decode(json.json_strip_comments(str))
         end

         -- Navegar entre breakpoints si estás usando "🔴" como símbolo
         vim.keymap.set("n", "<leader>bn", function()
            vim.cmd("/🔴") -- o el símbolo que uses en `sign_define` para los breakpoints
         end, { desc = "Next Breakpoint" })

         vim.keymap.set("n", "<leader>bp", function()
            vim.cmd("?🔴")
         end, { desc = "Previous Breakpoint" })
      end,
   },

   {
      "rcarriga/nvim-dap-ui",
      dependencies = {
         "mfussenegger/nvim-dap",
         "nvim-neotest/nvim-nio",
      },
      config = function()
         local dap, dapui = require("dap"), require("dapui")

         dapui.setup({
            layouts = {
               {
                  elements = {
                     "scopes",
                     "breakpoints",
                     "stacks",
                     "watches",
                  },
                  size = 40,
                  position = "left",
               },
               {
                  elements = {
                     "repl",
                     "console",
                  },
                  size = 10,
                  position = "bottom",
               },
            },
         })

         dap.listeners.after.event_initialized["dapui_config"] = function()
            dapui.open()
         end
         dap.listeners.before.event_terminated["dapui_config"] = function()
            dapui.close()
         end
         dap.listeners.before.event_exited["dapui_config"] = function()
            dapui.close()
         end

         vim.keymap.set("n", "<leader>du", function()
            dapui.toggle()
         end, { desc = "DAP: Toggle UI" })
      end,
   },

   {
      "theHamsta/nvim-dap-virtual-text",
      dependencies = { "mfussenegger/nvim-dap" },
      opts = {
         commented = true,
         virt_text_pos = "eol",
      },
   },
}
