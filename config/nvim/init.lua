if vim.loader then
   vim.loader.enable()
end

-- An explicit file is a standalone editing session; directories opt into a project.
vim.g.single_file_mode = vim.fn.argc() == 1 and vim.fn.isdirectory(vim.fn.argv(0)) == 0

_G.dd = function(...)
   require("util.debug").dump(...)
end
vim.print = _G.dd

require("config.lazy")
