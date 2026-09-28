vim.g.mapleader = " "

vim.opt.encoding = "utf-8"
vim.opt.fileencoding = "utf-8"

vim.opt.number = true

vim.opt.title = true
vim.opt.autoindent = true
vim.opt.smartindent = true
vim.opt.hlsearch = true
vim.opt.backup = false
vim.opt.showcmd = true
vim.opt.cmdheight = 1
vim.opt.laststatus = 3
vim.opt.expandtab = true
vim.opt.scrolloff = 10
vim.opt.backupskip = { "/tmp/*", "/private/tmp/*" }
vim.opt.inccommand = "split"
vim.opt.ignorecase = true -- Case insensitive searching UNLESS /C or capital in search
vim.opt.smarttab = true
vim.opt.breakindent = true
vim.opt.shiftwidth = 2
vim.opt.tabstop = 2
vim.opt.wrap = false -- No Wrap lines
vim.opt.backspace = { "start", "eol", "indent" }
vim.opt.path:append({ "**" }) -- Finding files - Search down into subfolders
vim.opt.wildignore:append({ "*/node_modules/*" })
vim.opt.splitbelow = true -- Put new windows below current
vim.opt.splitright = true -- Put new windows right of current
vim.opt.splitkeep = "cursor"
vim.opt.mouse = ""

-- Use the native shell on each platform instead of forcing a user-specific
-- Windows setup on Linux. Prefer PowerShell 7 on Windows when it is present.
if vim.fn.has("win32") == 1 then
   if vim.fn.executable("pwsh.exe") == 1 then
      vim.opt.shell = "pwsh.exe"
   else
      vim.opt.shell = "powershell.exe"
   end
elseif vim.env.SHELL and vim.fn.executable(vim.env.SHELL) == 1 then
   vim.opt.shell = vim.env.SHELL
elseif vim.fn.executable("fish") == 1 then
   vim.opt.shell = "fish"
else
   vim.opt.shell = "sh"
end

vim.o.guifont = "FiraCode Nerd Font:h14"
vim.opt.swapfile = false
vim.g.autoformat = false

-- Undercurl
vim.cmd([[let &t_Cs = "\e[4:3m"]])
vim.cmd([[let &t_Ce = "\e[4:0m"]])

-- Add asterisks in block comments
vim.opt.formatoptions:append({ "r" })

vim.cmd([[au BufNewFile,BufRead *.astro setf astro]])
vim.cmd([[au BufNewFile,BufRead Podfile setf ruby]])

if vim.fn.has("nvim-0.8") == 1 then
   vim.opt.cmdheight = 0
end

-- File types
vim.filetype.add({
   extension = {
      mdx = "mdx",
   },
})

vim.g.lazyvim_prettier_needs_config = true
-- vim.g.lazyvim_picker = "telescope"
vim.g.lazyvim_cmp = "blink.cmp"
