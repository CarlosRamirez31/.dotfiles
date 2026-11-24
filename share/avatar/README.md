# Local avatar assets

Vendored runtime only, no network requests at runtime:

- `@dicebear/core` 10.7.0, https://registry.npmjs.org/@dicebear/core/-/core-10.7.0.tgz
- `@dicebear/styles` 10.6.0, https://registry.npmjs.org/@dicebear/styles/-/styles-10.6.0.tgz

Original package manifests and LICENSE files are preserved. Every style carries
its own creator, source and license metadata. The editor displays this credit
and embeds it in exported PNGs. `libexec/avatar/render.mjs` renders the catalogue
and style options locally through Node; `editor.py` embeds the UI in Appearance.
