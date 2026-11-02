-- Turn off paste mode when leaving insert
vim.api.nvim_create_autocmd("InsertLeave", {
   pattern = "*",
   command = "set nopaste",
})

-- Disable spell checking in plain text and Markdown files.
vim.api.nvim_create_autocmd("FileType", {
   pattern = { "text", "markdown" },
   callback = function()
      vim.opt_local.spell = false
   end,
})

-- Disable the concealing in some file formats
-- The default conceallevel is 3 in LazyVim
vim.api.nvim_create_autocmd("FileType", {

   pattern = { "json", "jsonc", "markdown" },
   callback = function()
      vim.opt.conceallevel = 0
   end,
})
