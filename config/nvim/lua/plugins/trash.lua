return {
   {
      "folke/snacks.nvim",
      opts = {
         picker = {
            sources = {
               explorer = {
                  actions = {
                     explorer_del = function(picker)
                        require("util.trash").snacks_delete(picker)
                     end,
                     nvim_trash = function()
                        require("util.trash").open()
                     end,
                  },
                  win = { list = { keys = { ["R"] = "nvim_trash" } } },
               },
            },
         },
      },
   },
}
