return {
   {
      "nvim-treesitter/nvim-treesitter",
      opts = {
         ensure_installed = require("config.treesitter").parsers,
      },
   },
}
