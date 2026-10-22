-- End-to-end explorer action -> Python backend -> restore, using only /tmp data.
vim.opt.rtp:prepend(vim.fn.getcwd() .. "/config/nvim")
local root = vim.fn.tempname()
vim.fn.mkdir(root .. "/project/folder/nested", "p")
vim.fn.writefile({ "keep me" }, root .. "/project/folder/nested/file.txt")
local system, notify, select = vim.system, vim.notify, vim.ui.select
local messages, commands = {}, {}
vim.notify = function(message)
   table.insert(messages, message)
end
vim.system = function(command, options, callback)
   assert(command[2]:match("nvim%-trash%.py$"), "only the trash backend may touch test data")
   table.insert(commands, vim.deepcopy(command))
   table.insert(command, 3, "--root")
   table.insert(command, 4, root .. "/trash")
   return system(command, options, callback)
end
local updates = 0
package.loaded["snacks.explorer.tree"] = { refresh = function() end }
package.loaded["snacks.explorer.watch"] = {
   refresh = function()
      updates = updates + 1
   end,
}
package.loaded["snacks.explorer.actions"] = {
   update = function()
      error("trash must not force a second explorer rebuild")
   end,
}
_G.Snacks = {
   picker = {
      get = function()
         return {}
      end,
      util = {
         path = function(item)
            return item.file
         end,
         confirm = function(_, callback)
            callback()
         end,
      },
   },
   bufdelete = function() end,
}
local spec = dofile("config/nvim/lua/plugins/trash.lua")
local action = spec[1].opts.picker.sources.explorer.actions.explorer_del
local picker = {
   selected = function()
      return {
         { file = root .. "/project/folder" },
         { file = root .. "/project/folder/nested/file.txt" },
      }
   end,
   list = { set_selected = function() end },
}
action(picker)
assert(
   vim.wait(5000, function()
      return updates > 0
   end, 10),
   table.concat(messages, "\n")
)
assert(not vim.uv.fs_stat(root .. "/project/folder"))
assert(updates == 1, "one deletion must queue just one shared explorer refresh")
local records = vim.fn.glob(root .. "/trash/items/*/info.json", false, true)
assert(#records == 1, "deleting a folder with a selected child must produce one entry")
assert(commands[1][3] == "put", "explorer d must use recoverable trash")
local restored = false
vim.ui.select = function(entries, _, callback)
   assert(#entries == 1 and entries[1].kind == "directory")
   callback(entries[1])
end
require("util.trash").open(function()
   restored = true
end)
assert(
   vim.wait(5000, function()
      return restored
   end, 10),
   table.concat(messages, "\n")
)
assert(vim.fn.readfile(root .. "/project/folder/nested/file.txt")[1] == "keep me")
assert(updates == 2, "one restore must queue just one shared explorer refresh")
assert(#vim.fn.glob(root .. "/trash/items/*/info.json", false, true) == 0)
vim.system, vim.notify, vim.ui.select = system, notify, select
_G.Snacks = nil
vim.fn.delete(root, "rf")
print("Explorer trash and restore integration passed (temporary files only)")
