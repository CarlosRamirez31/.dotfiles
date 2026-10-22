local M = {}

-- Keep the language set explicit so a fresh machine is ready before the
-- first project is opened. This covers the main development stacks plus
-- common configuration, documentation, database, and shell formats.
M.parsers = {
   "bash",
   "c",
   "cpp",
   "c_sharp",
   "cmake",
   "css",
   "csv",
   "dart",
   "diff",
   "dockerfile",
   "editorconfig",
   "git_config",
   "git_rebase",
   "gitattributes",
   "gitcommit",
   "gitignore",
   "go",
   "graphql",
   "html",
   "http",
   "ini",
   "java",
   "javascript",
   "jsdoc",
   "json",
   "kotlin",
   "lua",
   "luadoc",
   "luap",
   "make",
   "markdown",
   "markdown_inline",
   "nginx",
   "php",
   "powershell",
   "prisma",
   "printf",
   "python",
   "query",
   "regex",
   "requirements",
   "rust",
   "sql",
   "ssh_config",
   "svelte",
   "swift",
   "toml",
   "tsx",
   "typescript",
   "vim",
   "vimdoc",
   "vue",
   "xml",
   "yaml",
}

function M.install()
   require("lazy").load({ plugins = { "nvim-treesitter" } })
   local treesitter = require("nvim-treesitter")
   treesitter.install(M.parsers, { summary = true }):wait(600000)

   local installed = treesitter.get_installed()
   local missing = vim.tbl_filter(function(parser)
      return not vim.tbl_contains(installed, parser)
   end, M.parsers)

   if #missing > 0 then
      error("No se pudieron instalar estos parsers de Tree-sitter: " .. table.concat(missing, ", "))
   end
end

return M
