"""Local DiceBear catalogue and photo crop editor embedded in Appearance."""
import concurrent.futures
import json
import os
from pathlib import Path
import pwd
import secrets
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'dotfiles/avatar'


def render(request):
    result = subprocess.run(['node', str(ROOT / 'libexec/avatar/render.mjs')],
                            input=json.dumps(request), text=True, capture_output=True, timeout=30, check=True)
    return json.loads(result.stdout)


def build_page(parent):
    from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
    css = Gtk.CssProvider()
    css.load_from_data(b"""
        #avatar-parts { background:#1e1e2e; color:#cdd6f4;
            border:1px solid #45475a; border-radius:12px; }
        #avatar-parts list, #avatar-parts row { background:transparent; border:0; }
        #avatar-parts row { padding:1px 0; }
        #avatar-parts button { background:transparent; color:#cdd6f4; border:0;
            border-radius:7px; padding:8px 10px; box-shadow:none; text-shadow:none;
            outline-style:none; }
        #avatar-parts button:hover, #avatar-parts button:active {
            background:#353047; color:#cba6f7; }
        #avatar-parts button:focus { box-shadow:inset 0 0 0 1px #cba6f7; }
        #avatar-parts entry { background:#181825; color:#cdd6f4;
            border:1px solid #45475a; border-radius:8px; padding:6px 8px;
            box-shadow:none; }
        #avatar-parts entry:focus { border-color:#cba6f7; }
    """)
    Gtk.StyleContext.add_provider_for_screen(parent.get_screen(), css, 601)
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    state = {'style': 'pixel-art', 'options': {'seed': secrets.token_hex(4)}, 'photo': None, 'pixbuf': None, 'token': 0}
    status = Gtk.Label(label='Loading the local avatar catalogue…', xalign=0, wrap=True)
    preview = Gtk.Image()
    preview.set_size_request(160, 160)
    heading = Gtk.Label(label='Login avatar · SDDM', xalign=0)
    page.pack_start(heading, False, False, 0)
    page.pack_start(preview, False, False, 0)
    page.pack_start(status, False, False, 0)
    credit = Gtk.Label(xalign=0, wrap=True, selectable=True)
    seed = Gtk.Entry(text=state['options']['seed'], placeholder_text='Avatar name / seed')
    search = Gtk.SearchEntry(placeholder_text='Search styles…')
    gallery = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=5,
                          min_children_per_line=1, row_spacing=6, column_spacing=6, homogeneous=True)
    gallery.set_filter_func(lambda child: search.get_text().casefold() in child.get_child().style_name)
    search.connect('search-changed', lambda _: gallery.invalidate_filter())
    page.pack_start(search, False, False, 0)
    page.pack_start(gallery, False, False, 0)
    page.pack_start(seed, False, False, 0)
    options = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    expander = Gtk.Expander(label='Customize this style')
    expander.add(options)
    page.pack_start(expander, False, False, 0)
    page.pack_start(credit, False, False, 0)

    def svg_image(svg, size):
        loader = GdkPixbuf.PixbufLoader.new_with_type('svg')
        loader.set_size(size, size)
        loader.write(svg.encode())
        loader.close()
        return loader.get_pixbuf().copy()

    def async_job(fn, callback, finished=None):
        future = pool.submit(fn)
        def done():
            try:
                result = future.result()
                callback(result)
            except Exception as error:
                if isinstance(error, subprocess.CalledProcessError):
                    if error.cmd and error.cmd[0] == 'pkexec':
                        message = ('Authorization was cancelled. Your login image was not changed.' if error.returncode == 126 else
                                   'Could not authorize the avatar change. Check the password dialog and try again.')
                    else:
                        message = 'Could not prepare the avatar. Please choose another option and try again.'
                else:
                    message = 'Could not complete the action: ' + str(error)[:160]
                if hasattr(parent, 'status'):
                    parent.status.set_text(message)
                else:
                    status.set_text(message)
            finally:
                if finished: finished()
            return False
        future.add_done_callback(lambda _: GLib.idle_add(done))

    def update(rebuild=False):
        state['photo'] = None
        state['options']['seed'] = seed.get_text()[:128]
        state['token'] += 1
        token = state['token']
        request = {'style': state['style'], 'options': dict(state['options'])}
        def loaded(data):
            if token != state['token']:
                return
            state['resolved'] = data.get('resolved', {})
            state['pixbuf'] = svg_image(data['svg'], 512)
            preview.set_from_pixbuf(state['pixbuf'].scale_simple(160, 160, GdkPixbuf.InterpType.NEAREST))
            status.set_text(state['style'].replace('-', ' ').title())
            if rebuild:
                customize(data['fields'])
        async_job(lambda: render(request), loaded)

    def option_changed(key, value):
        state['options'][key] = value
        update()

    def friendly(key):
        import re
        key = re.sub(r'Variant$', '', key)
        key = re.sub(r'Probability$', ' visibility', key)
        return re.sub(r'([a-z])([A-Z])', r'\1 \2', key).replace('_', ' ').capitalize()

    def customize(fields):
        for child in options.get_children():
            options.remove(child)
        selector = Gtk.MenuButton(label="Choose a part  ▾")
        hidden = {'seed', 'size', 'idRandomization', 'title', 'fontFamily', 'fontWeight'}
        keys = [key for key in fields if key not in hidden]
        # Character parts first; global positioning controls come last.
        keys.sort(key=lambda key: (not key.endswith('Variant'), key))
        options.pack_start(Gtk.Label(label='What would you like to change?', xalign=0), False, False, 0)
        options.pack_start(selector, False, False, 0)
        controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        options.pack_start(controls, True, True, 0)
        def choose(key):
            selector.set_label(friendly(key) + '  ▾')
            if not key:
                return
            state['choice_token'] = state.get('choice_token', 0) + 1
            token = state['choice_token']
            for child in controls.get_children():
                controls.remove(child)
            field = fields[key]
            if field['type'] == 'enum':
                grid = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE,
                                   min_children_per_line=1, max_children_per_line=3,
                                   homogeneous=True, row_spacing=5, column_spacing=5)
                controls.pack_start(grid, False, False, 0)
                controls.pack_start(Gtk.Label(label='Choose a picture to try it on.', xalign=0, wrap=True), False, False, 0)
                request = {'action': 'variants', 'style': state['style'], 'options': dict(state['options']), 'field': key}
                def variants(items):
                    if state.get('choice_token') != token:
                        return
                    for index, item in enumerate(items):
                        button = Gtk.Button()
                        button.set_tooltip_text('Option ' + str(index + 1))
                        button.add(Gtk.Image.new_from_pixbuf(svg_image(item['svg'], 72)))
                        def pick(_, value=item['value'], chosen=button):
                            for child in grid.get_children():
                                child.get_child().get_style_context().remove_class('suggested-action')
                            chosen.get_style_context().add_class('suggested-action')
                            probability = key.removesuffix('Variant') + 'Probability'
                            if probability in fields:
                                state['options'][probability] = 100
                            option_changed(key, [value] if field.get('list') else value)
                        if state.get('resolved', {}).get(key) == item['value']:
                            button.get_style_context().add_class('suggested-action')
                        button.connect('clicked', pick)
                        grid.add(button)
                    grid.show_all()
                async_job(lambda: render(request), variants)
            elif field['type'] == 'color':
                control = Gtk.ColorButton(title=friendly(key))
                color = state.get('resolved', {}).get(key, ['#cba6f7'])
                if isinstance(color, list): color = color[0] if color else '#cba6f7'
                rgba = Gdk.RGBA(); rgba.parse(color); control.set_rgba(rgba)
                def color_changed(w):
                    rgba = w.get_rgba()
                    value = '%02x%02x%02x' % tuple(round(c * 255) for c in (rgba.red, rgba.green, rgba.blue))
                    option_changed(key, [value] if field.get('list') else value)
                control.connect('color-set', color_changed)
                controls.pack_start(Gtk.Label(label='Click the color to choose another.', xalign=0, wrap=True), False, False, 0)
                controls.pack_start(control, False, False, 0)
            elif field['type'] == 'boolean' or key.endswith('Probability'):
                control = Gtk.ComboBoxText()
                for value, label in [('auto', 'Let the character decide'), ('on', 'Show'), ('off', 'Hide')]:
                    control.append(value, label)
                control.set_active(0)
                def visibility_changed(w):
                    value = w.get_active_id()
                    if value == 'auto':
                        state['options'].pop(key, None); update()
                    else:
                        option_changed(key, value == 'on' if field['type'] == 'boolean' else 100 if value == 'on' else 0)
                control.connect('changed', visibility_changed)
                controls.pack_start(control, False, False, 0)
            elif field['type'] in ('number', 'range'):
                low, high = field.get('min', 0), field.get('max', 100)
                current = state.get('resolved', {}).get(key, 1 if key.endswith('Scale') or key=='scale' else 0)
                if isinstance(current, list): current = current[0]
                control = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, low, high, .05 if key=='scale' else 1)
                control.set_value(max(low, min(high, current)))
                pending = [None]
                def changing(w):
                    if pending[0]: GLib.source_remove(pending[0])
                    def apply_value():
                        pending[0] = None
                        if state.get('choice_token') == token:
                            value = w.get_value()
                            option_changed(key, [value] * 2 if field['type']=='range' else [value] if field.get('list') else value)
                        return False
                    pending[0] = GLib.timeout_add(150, apply_value)
                control.connect('value-changed', changing)
                controls.pack_start(control, False, False, 0)
            else:
                control = Gtk.Entry(placeholder_text='Your text')
                control.connect('activate', lambda w: option_changed(key, [w.get_text()] if field.get('list') else w.get_text()))
                controls.pack_start(control, False, False, 0)
            controls.show_all()
        popover = Gtk.Popover.new(selector)
        popover.set_name('avatar-parts')
        menu = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin=8)
        find = Gtk.SearchEntry(placeholder_text='Find a part…')
        menu.pack_start(find, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_size_request(250, 220)
        choices = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        for key in keys:
            button = Gtk.Button(label=friendly(key), halign=Gtk.Align.FILL)
            button.set_relief(Gtk.ReliefStyle.NONE)
            button.part_name = friendly(key).casefold()
            button.connect('clicked', lambda _, k=key: (choose(k), popover.popdown()))
            choices.add(button)
        choices.set_filter_func(lambda row: find.get_text().casefold() in row.get_child().part_name)
        find.connect('search-changed', lambda _: choices.invalidate_filter())
        scroll.add(choices)
        menu.pack_start(scroll, True, True, 0)
        popover.add(menu)
        menu.show_all()
        selector.set_popover(popover)
        if keys:
            choose(keys[0])
        options.show_all()

    def select(item):
        state['choice_token'] = state.get('choice_token', 0) + 1
        state['style'] = item['name']
        state['options'] = {'seed': seed.get_text()[:128]}
        credit.set_text(item['meta']['license']['text'])
        update(True)
        workspace.set_visible_child_name('customize')

    def catalog_loaded(items):
        for item in items:
            button = Gtk.Button()
            button.style_name = item['name']
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            box.pack_start(Gtk.Image.new_from_pixbuf(svg_image(item['svg'], 64)), False, False, 0)
            label = Gtk.Label(label=item['name'].replace('-', ' ').title(), wrap=True)
            label.set_max_width_chars(12)
            box.pack_start(label, False, False, 0)
            button.add(box)
            button.connect('clicked', lambda _, i=item: select(i))
            gallery.add(button)
        gallery.show_all()
        try:
            saved = json.loads((DATA / 'current.json').read_text())
            assert saved['style'] in {item['name'] for item in items}
            assert isinstance(saved['options'], dict)
            state['style'], state['options'] = saved['style'], saved['options']
            seed.set_text(str(saved['options'].get('seed', 'avatar')))
            credit.set_text(saved.get('credit', ''))
            if saved.get('photo'):
                image = GdkPixbuf.Pixbuf.new_from_file(str(DATA / 'current.png'))
                state['photo'], state['pixbuf'] = True, image
                preview.set_from_pixbuf(image.scale_simple(160, 160, GdkPixbuf.InterpType.BILINEAR))
                status.set_text('Your saved photo')
                options.pack_start(Gtk.Label(label='Choose photo to change the crop, or select another style.', wrap=True), False, False, 0)
                options.show_all()
            else:
                update(True)
        except (OSError, ValueError, KeyError, AssertionError, GLib.Error):
            select(next(i for i in items if i['name'] == 'pixel-art'))

    def randomize(_):
        seed.set_text(secrets.token_hex(4))
        state['options'] = {'seed': seed.get_text()}
        update(True)

    def choose_photo(_, favorites=False):
        chooser = Gtk.FileChooserDialog(title='Choose a profile photo', transient_for=parent,
                                       action=Gtk.FileChooserAction.OPEN)
        chooser.add_buttons('Cancel', Gtk.ResponseType.CANCEL, 'Open', Gtk.ResponseType.OK)
        if favorites:
            folder = DATA / 'favorites'
            folder.mkdir(parents=True, exist_ok=True)
            chooser.set_current_folder(str(folder))
        filter_ = Gtk.FileFilter(); filter_.set_name('Images'); filter_.add_pixbuf_formats(); chooser.add_filter(filter_)
        if chooser.run() != Gtk.ResponseType.OK:
            chooser.destroy(); return
        filename = chooser.get_filename(); chooser.destroy()
        try:
            if Path(filename).stat().st_size > 32 * 1024 * 1024:
                raise ValueError('Choose an image smaller than 32 MiB.')
            source = GdkPixbuf.Pixbuf.new_from_file_at_scale(filename, 2048, 2048, True).apply_embedded_orientation()
        except Exception as e:
            status.set_text(str(e)); return
        dialog = Gtk.Dialog(title='Crop your photo', transient_for=parent, modal=True)
        dialog.add_buttons('Cancel', Gtk.ResponseType.CANCEL, 'Use photo', Gtk.ResponseType.OK)
        content = dialog.get_content_area()
        picture = Gtk.Image(); content.pack_start(picture, True, True, 8)
        sliders = []
        for label, low, high, value in [('Zoom', 1, 4, 1), ('Horizontal', -1, 1, 0), ('Vertical', -1, 1, 0)]:
            content.pack_start(Gtk.Label(label=label), False, False, 0)
            slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, low, high, .01)
            slider.set_value(value); content.pack_start(slider, False, False, 0); sliders.append(slider)
        cropped = [None]
        def crop(*_):
            zoom, x, y = [s.get_value() for s in sliders]
            scale = max(512 / source.get_width(), 512 / source.get_height()) * zoom
            dx = (512 - source.get_width() * scale) * (x + 1) / 2
            dy = (512 - source.get_height() * scale) * (y + 1) / 2
            dest = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 512, 512)
            dest.fill(0x1e1e2eff)
            source.scale(dest, 0, 0, 512, 512, dx, dy, scale, scale, GdkPixbuf.InterpType.BILINEAR)
            cropped[0] = dest
            picture.set_from_pixbuf(dest.scale_simple(256, 256, GdkPixbuf.InterpType.BILINEAR))
        for slider in sliders:
            slider.connect('value-changed', crop)
        crop(); dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            state['token'] += 1
            state['pixbuf'] = cropped[0]
            state['photo'] = True
            preview.set_from_pixbuf(cropped[0].scale_simple(160, 160, GdkPixbuf.InterpType.BILINEAR))
            credit.set_text(source.get_option('tEXt::Description') or 'Your photo · original file preserved')
            status.set_text('Photo ready · click Guardar to save and apply it.')
        dialog.destroy()

    def apply(_=None):
        if state.get('saving') or state['pixbuf'] is None:
            return
        state['saving'] = True
        page.set_sensitive(False)
        if hasattr(parent, 'buttons'): parent.buttons['save'].set_sensitive(False)
        snapshot = {'style': state['style'], 'options': dict(state['options']),
                    'photo': bool(state['photo']), 'credit': credit.get_text()}
        photo = state['pixbuf'].copy() if snapshot['photo'] else None
        def report(message):
            if hasattr(parent, 'status'):
                parent.status.set_text(message)
            else:
                status.set_text(message)
        def finished():
            state['saving'] = False
            page.set_sensitive(True)
            if hasattr(parent, 'buttons'): parent.buttons['save'].set_sensitive(True)
        report('Saving avatar to SDDM… authorization may be requested.')
        def save():
            DATA.mkdir(parents=True, exist_ok=True)
            image = photo or svg_image(render({'style': snapshot['style'], 'options': snapshot['options']})['svg'], 512)
            fd, filename = tempfile.mkstemp(suffix='.png', prefix='apply-', dir=DATA)
            os.close(fd)
            target = '/usr/share/sddm/faces/' + pwd.getpwuid(os.getuid()).pw_name + '.face.icon'
            metadata = DATA / ('save-' + secrets.token_hex(6) + '.json')
            try:
                image.savev(filename, 'png', ['tEXt::Description'], [snapshot['credit']])
                subprocess.run(['pkexec', '/usr/bin/install', '-D', '-m', '644', '--', filename, target],
                               check=True, capture_output=True, timeout=120)
                metadata.write_text(json.dumps(snapshot))
                Path(filename).replace(DATA / 'current.png')
                metadata.replace(DATA / 'current.json')
                return 'Avatar saved and applied to SDDM. Your edits will be restored next time.'
            finally:
                Path(filename).unlink(missing_ok=True)
                metadata.unlink(missing_ok=True)
        async_job(save, report, finished)

    def favorite(_):
        if state['pixbuf'] is None:
            return
        folder = DATA / 'favorites'; folder.mkdir(parents=True, exist_ok=True)
        path = folder / (secrets.token_hex(6) + '.png')
        state['pixbuf'].savev(str(path), 'png', ['tEXt::Description'], [credit.get_text()])
        status.set_text('Favorite saved. Use Choose photo to open it again.')

    buttons = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    for label, fn in [('New character', randomize), ('Choose photo', choose_photo), ('Save favorite', favorite), ('Open favorite', lambda b: choose_photo(b, True))]:
        button = Gtk.Button(label=label); button.connect('clicked', fn); buttons.pack_start(button, False, False, 0)
    # The portrait and actions stay in place while only the controls scroll.
    for child in list(page.get_children()):
        page.remove(child)
    expander.remove(options)
    page.set_orientation(Gtk.Orientation.HORIZONTAL)
    page.set_spacing(14)
    left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    left.set_size_request(170, -1)
    heading.set_text('Your login avatar')
    status.set_max_width_chars(20)
    for widget in (heading, preview, status, buttons):
        left.pack_start(widget, False, False, 0)
    page.pack_start(left, False, False, 0)
    right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    workspace = Gtk.Stack(transition_type=Gtk.StackTransitionType.NONE)
    navigation = Gtk.StackSwitcher(stack=workspace)
    right.pack_start(navigation, False, False, 0)
    right.pack_start(workspace, True, True, 0)
    def section(widget, name, title):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(widget)
        workspace.add_titled(scroll, name, title)
    section(options, 'customize', 'Customize')
    styles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    styles.pack_start(search, False, False, 0)
    gallery.set_max_children_per_line(3)
    styles.pack_start(gallery, False, False, 0)
    section(styles, 'styles', 'All styles')
    credit.set_max_width_chars(35)
    details = Gtk.Expander(label='About this style'); details.add(credit)
    right.pack_start(details, False, False, 0)
    page.pack_start(right, True, True, 0)
    parent.connect('destroy', lambda _: pool.shutdown(wait=False, cancel_futures=True))
    async_job(lambda: render({'action': 'catalog'}), catalog_loaded)
    page.save_avatar = apply
    return page
