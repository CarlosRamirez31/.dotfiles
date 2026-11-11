local awful = require("awful")
local gears = require("gears")

local function prepare_mouse_geometry(c)
    c.fullscreen = false
    c.maximized = false
    c.maximized_horizontal = false
    c.maximized_vertical = false
    c.floating = true
    c:emit_signal("request::activate", "mouse_click", { raise = true })
end

local function resize_with_mouse(c)
    prepare_mouse_geometry(c)
    awful.mouse.client.resize(c)
end

-- Alt + Shift and a mouse drag turns the client floating, then moves it.
local floating_client_buttons = gears.table.join(
    awful.button({ "Mod1", "Shift" }, 1, function(c)
        prepare_mouse_geometry(c)
        awful.mouse.client.move(c)
    end),
    -- Resize from the nearest corner, independently in both dimensions.
    awful.button({ "Mod1" }, 3, resize_with_mouse),
    awful.button({ "Mod1", "Shift" }, 3, resize_with_mouse)
)

return {
    {
        rule = {},
        properties = {
            border_width = 2,
            border_color = "#242438",
            focus = awful.client.focus.filter,
            raise = true,
            screen = awful.screen.preferred,
            -- Ignore a new application's remembered desktop. Keep restored
            -- windows in place on restart and dialogs with their parent.
            tag = function(c)
                if awesome.startup or c.type == "dock" or c.type == "desktop" then return nil end
                if c.transient_for then return c.transient_for.first_tag end
                return awful.screen.focused().selected_tag
            end,
            placement = awful.placement.no_overlap + awful.placement.no_offscreen,
            buttons = floating_client_buttons,
            sticky = false,
            -- Ordinary applications always join the active tag's tiling
            -- layout.  Dialogs below deliberately override this behavior.
            floating = false,
            -- Tiled clients must fit their allocation even when the app asks
            -- for a larger minimum; otherwise a column can cross monitors.
            size_hints_honor = false,
            maximized = false,
            fullscreen = false,
            ontop = false,
        },
    },
    {
        rule_any = { type = { "dock" }, class = { "Polybar" } },
        properties = {
            border_width = 0,
            focusable = false,
            floating = true,
            sticky = true,
            ontop = true,
            skip_taskbar = true,
            size_hints_honor = true,
        },
    },
    {
        -- Keep the usual layout; mask only Qt's unused area around Android.
        rule = { class = "Emulator" },
        properties = {
            size_hints_honor = true,
            titlebars_enabled = false,
        },
        callback = function(c) require("emulator-shape").attach(c) end,
    },
    {
        rule = { role = "dotfiles-file-tray-edge" },
        properties = {
            placement = function() end,
            screen = function(c)
                local x, y, w, h = (c.name or ""):match("^File tray edge | (%-?%d+) | (%-?%d+) | (%d+) | (%d+)$")
                if x then
                    x, y = tonumber(x) + tonumber(w) / 2, tonumber(y) + tonumber(h) / 2
                    for s in screen do
                        local g = s.geometry
                        if x >= g.x and x < g.x + g.width and y >= g.y and y < g.y + g.height then return s end
                    end
                end
                return mouse.screen
            end,
        },
        callback = function(c)
            local x, y, w, h = (c.name or ""):match("^File tray edge | (%-?%d+) | (%-?%d+) | (%d+) | (%d+)$")
            if x then
                x, y, w, h = tonumber(x), tonumber(y), tonumber(w), tonumber(h)
                local width = math.min(640, w - 40)
                c:geometry({x=x+math.floor((w-width)/2), y=y+h-5, width=width, height=5})
            end
        end,
    },
    {
        rule = { role = "dotfiles-file-tray" },
        properties = {
            floating = true, ontop = true, sticky = true, skip_taskbar = true,
            focusable = true, border_width = 0, size_hints_honor = true,
            screen = function() return mouse.screen end,
            placement = function() end,
        },
        callback = function(c)
            local function outline(cr, w, h)
                local wing, rise, r = 16, 16, 22
                local left, right, k = wing, w - wing, r * 0.55228475
                local fx, fy = wing * 0.55228475, rise * 0.55228475
                cr:move_to(0, h)
                cr:curve_to(fx, h, left, h - rise + fy, left, h - rise)
                cr:line_to(left, r)
                cr:curve_to(left, r - k, left + r - k, 0, left + r, 0)
                cr:line_to(right - r, 0)
                cr:curve_to(right - r + k, 0, right, r - k, right, r)
                cr:line_to(right, h - rise)
                cr:curve_to(right, h - rise + fy, w - fx, h, w, h)
                cr:close_path()
            end
            -- Keep the RGBA edge rendered by GTK; a binary visual mask clips
            -- its antialiasing. Only the invisible mouse area needs a mask.
            c.shape = nil
            c.shape_bounding, c.shape_clip = nil, nil
            local function input_shape()
                if not c.valid then return end
                local cairo = require("lgi").cairo
                local surface = cairo.ImageSurface(cairo.Format.A1, c.width, c.height)
                local cr = cairo.Context(surface)
                outline(cr, c.width, c.height)
                cr:set_source_rgba(1, 1, 1, 1)
                cr:fill()
                c.shape_input = surface._native
                surface:finish()
            end
            c:connect_signal("property::size", input_shape)
            input_shape()
        end,
    },
    {
        rule_any = { class = { "DotfilesBackup", "DotfilesMount" } },
        properties = {
            floating = true,
            ontop = true,
            placement = awful.placement.centered,
        },
        callback = function(c)
            local area = c.screen.workarea
            c:geometry({ width = math.min(560, math.floor(area.width * 0.9)), height = math.min(c.class == "DotfilesMount" and 430 or 280, math.floor(area.height * 0.8)) })
            awful.placement.centered(c, { honor_workarea = true })
        end,
    },
    {
        rule = { class = "DotfilesLazyDocker" },
        properties = {
            floating = true,
            placement = awful.placement.centered,
        },
        callback = function(c)
            local area = c.screen.workarea
            c:geometry({ width = math.floor(area.width * 0.85), height = math.floor(area.height * 0.8) })
            awful.placement.centered(c, { honor_workarea = true })
        end,
    },
    {
        rule = { role = "dotfiles-displays" },
        properties = {
            floating = true,
            placement = awful.placement.centered,
            titlebars_enabled = false,
        },
    },
    {
        rule_any = {
            type = { "dialog", "utility", "toolbar", "splash" },
            class = { "Gpick" },
        },
        properties = {
            floating = true,
            size_hints_honor = true,
            placement = awful.placement.centered,
        },
    },
    {
        rule = { class = "Emulator", name = "^Emulator$" },
        properties = {
            floating = true,
            -- Qt's utility window must not be centered or placed as a new
            -- independent application by the generic rules above.
            placement = function() end,
        },
        callback = function(c) require("emulator-toolbar").attach(c) end,
    },
    {
        rule = { class = "Emulator", name = "^Extended [Cc]ontrols" },
        properties = {
            floating = true,
            maximized = false,
            fullscreen = false,
            placement = awful.placement.centered + awful.placement.no_offscreen,
        },
    },
}
