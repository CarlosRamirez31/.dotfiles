local standalone = vim.g.single_file_mode == true

return {
   {
      "neovim/nvim-lspconfig",
      opts = function(_, opts)
         -- No workspace means Marksman only receives documents opened in the editor.
         opts.servers.marksman = vim.tbl_deep_extend("force", opts.servers.marksman or {}, {
            root_dir = function(_, on_dir)
               on_dir(nil)
            end,
            workspace_required = false,
            single_file_support = true,
         })
         -- Assign empty lists after merging so inherited root markers cannot survive.
         opts.servers.marksman.root_markers = {}
         opts.servers.marksman.workspace_folders = nil

         if standalone then
            for name, server in pairs(opts.servers) do
               if name ~= "marksman" and name ~= "*" then
                  opts.servers[name] = vim.tbl_extend("force", type(server) == "table" and server or {}, {
                     enabled = false,
                  })
               end
            end
         end
      end,
   },
   -- These plugins start their own servers, outside nvim-lspconfig.
   { "akinsho/flutter-tools.nvim", optional = true, enabled = not standalone },
   { "mrcjkb/rustaceanvim", optional = true, enabled = not standalone },
   { "github/copilot.vim", optional = true, enabled = not standalone },
   { "zbirenbaum/copilot.lua", optional = true, enabled = not standalone },
}
