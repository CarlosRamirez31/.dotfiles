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
            class = { "Gpick", "flameshot" },
        },
        properties = { floating = true, placement = awful.placement.centered },
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
