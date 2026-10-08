#!/usr/bin/env python3
"""Bump the cache-busting version on every local module / stylesheet reference (`?v=N`).

GitHub Pages lets browsers cache .js / .css for about 10 minutes, so after a push a visitor could get new HTML with an
old module (or one new module importing an old one). Every reference to our own files carries the same `?v=N`; run
this before a push that changes any of them. It rewrites index.html, cybertruck_mock.html and the .js modules, and
keeps all references on ONE number (different specifiers for the same file would load it twice).
"""
import pathlib, re

HERE = pathlib.Path(__file__).resolve().parent
FILES = ["index.html", "cybertruck_mock.html", "main.js", "common.js", "gclass.js", "cybertruck.js"]
REF = re.compile(r"""(\./)?((?:main|common|gclass|cybertruck|tents)\.js|style\.css)\?v=(\d+)""")

texts = {f: (HERE / f).read_text() for f in FILES}
current = max(int(m.group(3)) for t in texts.values() for m in REF.finditer(t))
new = current + 1
for f, t in texts.items():
    out = REF.sub(lambda m: f"{m.group(1) or ''}{m.group(2)}?v={new}", t)
    if out != t:
        (HERE / f).write_text(out)
print(f"version {current} -> {new}")
