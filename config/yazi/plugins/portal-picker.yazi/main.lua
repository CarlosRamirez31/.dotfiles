local M = {}

local snapshot = ya.sync(function(state)
    local current = cx.active.current
    local hovered = current.hovered
    local selected = {}
    for _, file in pairs(cx.active.selected) do
        selected[#selected + 1] = tostring(file.url)
    end
    return {
        cwd = tostring(current.cwd),
        name = state.name or os.getenv("DOTFILES_PICKER_NAME") or "",
        hovered = hovered and tostring(hovered.url),
        directory = hovered and hovered.cha.is_dir,
        selected = selected,
    }
end)

local set_name = ya.sync(function(state, name)
    state.name = name
    ui.render()
end)

local function notify(message)
    ya.notify { title = "Yazi file picker", content = message, timeout = 5, level = "warn" }
end

function M:setup()
    local mode = os.getenv("DOTFILES_PICKER_MODE")
    if not mode then return end
    Header:children_add(function()
        local label = mode == "save" and (" SAVE AS: " .. (self.name or os.getenv("DOTFILES_PICKER_NAME") or ""))
            or mode == "directory" and " CHOOSE FOLDER" or " CHOOSE FILES"
        return ui.Line { ui.Span(ui.printable(label .. " · ")):fg("blue"):bold() }
    end, 0, Header.LEFT)
    function Status:name()
        local hint = mode == "save" and " F2 Name · ↵ Save · q Cancel "
            or " ↵ Select · Space Mark · q Exit "
        return ui.Line { ui.Span(hint):fg("blue") }
    end
    function Status:perm() return "" end
end

function M:entry(job)
    local mode = os.getenv("DOTFILES_PICKER_MODE")
    if not mode then return end
    local state = snapshot()
    if job.args[1] == "name" then
        local value, event = ya.input {
            title = "Filename:", value = state.name,
            pos = { "top-center", y = 3, w = 60 },
        }
        if event ~= 1 then return end
        if not value or value == "" or value == "." or value == ".." or value:find("[/\r\n%z]") then
            return notify("Enter a filename only; use h/l to navigate folders.")
        end
        set_name(value)
        return
    end

    local selected = state.selected
    if mode == "save" then
        if state.name == "" or state.name:find("[/\r\n%z]") then
            return notify("Press F2 to enter a valid filename.")
        end
        local target = state.cwd .. "/" .. state.name
        local existing = fs.cha(Url(target))
        if existing then
            if existing.is_dir then return notify("A folder already has this name. Press F2 to change it.") end
            if not ya.confirm {
                pos = { "center", w = 65, h = 12 }, title = "Replace file?",
                body = "This file already exists:\n" .. ui.printable(target) .. "\n\nAllow the application to replace it?",
            } then return end
        end
        selected = { target }
    elseif mode == "directory" then
        selected = { state.cwd }
    else
        if #selected == 0 then
            if state.directory then return ya.emit("enter", {}) end
            if not state.hovered then return notify("Choose a file.") end
            selected = { state.hovered }
        end
        if os.getenv("DOTFILES_PICKER_MULTIPLE") ~= "1" and #selected > 1 then
            return notify("This application allows only one file.")
        end
        for _, path in ipairs(selected) do
            local info = fs.cha(Url(path), true)
            if not info or info.is_dir then return notify("Choose files; use h/l to navigate folders.") end
        end
    end
    for _, path in ipairs(selected) do
        if path:sub(1, 1) ~= "/" then return notify("Choose a local file or folder.") end
        if path:find("[\r\n%z]") then return notify("The portal does not support newlines in filenames.") end
    end
    local ok, err = fs.write(Url(os.getenv("DOTFILES_PICKER_RESULT")), table.concat(selected, "\n") .. "\n")
    if not ok then return notify(tostring(err)) end
    ya.emit("quit", {})
end

return M
