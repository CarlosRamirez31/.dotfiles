return {
   "github/copilot.vim",
   event = "InsertEnter",
   config = function()
      -- Disable the default <Tab> mapping provided by the plugin
      vim.g.copilot_no_tab_map = true
      vim.g.copilot_snippet_separator = ""
      vim.g.copilot_assume_mapped = true

      local map = vim.keymap.set
      map(
         "i",
         "<C-j>",
         "copilot#Accept('<CR>')",
         { noremap = true, silent = true, expr = true, replace_keycodes = false }
      )

      -- Optional: Create normal mode mapping to open the Copilot panel
      vim.keymap.set("n", "<leader>cp", "<cmd>Copilot panel<CR>", {
         noremap = true,
         silent = true,
         desc = "Open Copilot panel",
      })

      -- Optional: Mappings to enable or disable Copilot on the fly
      vim.api.nvim_create_user_command("CopilotEnable", function()
         vim.cmd("Copilot enable")
      end, { desc = "Enable GitHub Copilot" })

      vim.api.nvim_create_user_command("CopilotDisable", function()
         vim.cmd("Copilot disable")
      end, { desc = "Disable GitHub Copilot" })
   end,
}
