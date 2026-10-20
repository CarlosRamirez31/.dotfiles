local shape = dofile("components/awesome/dotfiles/.config/awesome/emulator-shape.lua")

local function client(name)
    return {
        class = "Emulator", name = name, valid = true, border_width = 2,
        size_hints = { user_size = { width = 566, height = 1007 } },
        signals = {},
        connect_signal = function(self, name, callback) self.signals[name] = callback end,
    }
end

local function rectangle(c, w, h, expected_w, expected_h)
    c.shape({ rectangle = function(_, x, y, width, height)
        assert(x == 0 and y == 0)
        assert(width == expected_w and height == expected_h,
            string.format("got %dx%d, expected %dx%d", width, height, expected_w, expected_h))
    end }, w, h)
end

local c = client("Android Emulator - Beambollow:5554")
shape.attach(c)
assert(c.floating == nil, "must not force floating")
rectangle(c, 945, 1011, 570, 1011) -- Extra space to the right.
c.size_hints.user_size = { width = 273, height = 486 }
c.signals["property::size_hints"]()
rectangle(c, 277, 1011, 277, 490) -- Extra space below, as in the screenshot.
c.size_hints.user_size = { width = 1007, height = 566 }
c.signals["property::size_hints"]()
rectangle(c, 1011, 945, 1011, 570) -- Landscape rotation.
rectangle(c, 800, 400, 800, 400) -- Never expand beyond assigned geometry.
c.size_hints = {}
rectangle(c, 945, 1011, 945, 1011) -- No hints yet: keep the whole screen.

local toolbar = client("Emulator")
shape.attach(toolbar)
assert(toolbar.shape == nil, "toolbar must remain visible")
toolbar.name = "Android Emulator - Other:5556"
toolbar.signals["property::name"]()
assert(type(toolbar.shape) == "function", "handle titles set after manage")
local original = toolbar.shape
shape.attach(toolbar)
assert(toolbar.shape == original, "attach must be idempotent")
print("Emulator shape checks passed")
