return {
   {
      "folke/snacks.nvim",
      keys = {
         {
            "<leader>gk",
            function()
               Snacks.terminal({ "lazydocker" }, {
                  cwd = vim.fn.getcwd(),
                  win = { position = "float", width = 0.9, height = 0.85, border = "rounded", title = " LazyDocker " },
               })
            end,
            desc = "LazyDocker (contenedores)",
         },
      },
   },
}
