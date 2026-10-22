-- Regression: delete/restore with real Snacks watchers must not duplicate tree rows.
local config = vim.fn.getcwd() .. "/config/nvim"
vim.opt.rtp:prepend(config)
vim.opt.rtp:prepend(vim.fn.stdpath("data") .. "/lazy/snacks.nvim")
local root = vim.fn.tempname()
local project = root .. "/project"
vim.fn.mkdir(project, "p")
vim.fn.writefile({ "live" }, project .. "/live.txt")
assert(vim.system({ "git", "init", "-q", project }):wait().code == 0)
local system = vim.system
vim.system = function(command, options, callback)
   if command[2] and command[2]:match("nvim%-trash%.py$") then
      table.insert(command, 3, "--root")
      table.insert(command, 4, root .. "/trash")
   end
   return system(command, options, callback)
end
local options = dofile(config .. "/lua/plugins/trash.lua")[1].opts
options.explorer = { enabled = true, replace_netrw = false }
options.picker.enabled = true
require("snacks").setup(options)
vim.cmd.edit(project .. "/live.txt")
local picker = Snacks.explorer({ cwd = project, watch = true, git_status = true, diagnostics = false })
assert(picker)
Snacks.picker.util.confirm = function(_, callback)
   callback()
end
local trash = require("util.trash")
local function settled(predicate)
   assert(
      vim.wait(5000, function()
         return not picker:is_active() and predicate()
      end, 10),
      "explorer did not settle"
   )
   vim.wait(300, function()
      return false
   end, 10) -- Allow queued fs/git updates to run.
   local seen, roots = {}, 0
   for _, item in ipairs(picker:items()) do
      assert(not seen[item.file], "duplicate row: " .. tostring(item.file))
      seen[item.file] = true
      if item.file == project then
         roots = roots + 1
      end
   end
   assert(roots == 1, "project root must appear exactly once")
end
settled(function()
   return #picker:items() > 0
end)
for index = 1, 3 do
   local folder = project .. "/folder" .. index
   vim.fn.mkdir(folder .. "/nested", "p")
   vim.fn.writefile({ "keep" }, folder .. "/nested/file.txt")
   settled(function()
      for _, item in ipairs(picker:items()) do
         if item.file == folder then
            return true
         end
      end
      return false
   end)
   -- Cover deleting a directory containing the file shown in the main editor.
   vim.api.nvim_set_current_win(picker.main)
   vim.cmd.edit(folder .. "/nested/file.txt")
   settled(function()
      return true
   end)
   picker.list.win:focus()
   picker.selected = function()
      return { { file = folder } }
   end
   trash.snacks_delete(picker)
   settled(function()
      if vim.uv.fs_stat(folder) then
         return false
      end
      for _, item in ipairs(picker:items()) do
         if item.file == folder then
            return false
         end
      end
      return true
   end)
   local restored = false
   vim.ui.select = function(entries, _, callback)
      callback(entries[1])
   end
   trash.open(function()
      restored = true
   end)
   settled(function()
      return restored
   end)
   assert(vim.fn.readfile(folder .. "/nested/file.txt")[1] == "keep")
end
picker:close()
require("snacks.explorer.watch").abort()
vim.system = system
vim.cmd.enew()
vim.fn.delete(root, "rf")
print("Real explorer delete/restore regression passed: no duplicate roots or rows")
