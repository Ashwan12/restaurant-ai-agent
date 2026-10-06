from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
static_dir = base_dir / "static"

index_path = static_dir / "index.html"
css_path = static_dir / "style.css"
js_path = static_dir / "app.js"

html = index_path.read_text(encoding="utf-8")
css = css_path.read_text(encoding="utf-8")
js = js_path.read_text(encoding="utf-8")

# Replace stylesheet link
if '<link rel="stylesheet" href="/static/style.css">' in html:
    html = html.replace('<link rel="stylesheet" href="/static/style.css">', f"<style>\n{css}\n</style>")

# Replace script tag
if '<script src="/static/app.js"></script>' in html:
    html = html.replace('<script src="/static/app.js"></script>', f"<script>\n{js}\n</script>")

index_path.write_text(html, encoding="utf-8")
print(f"Successfully bundled inline assets into {index_path}. Total size: {len(html)} bytes.")
