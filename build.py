#!/usr/bin/env python3
"""Render the portfolio site and profile README from content.json.

Sources, in precedence order:
  content.json  - hand-maintained, always present
  board.json    - optional, written by sync_board.py from the org Project board.
                  Items merge by project id; board fields win.

Only projects with publish=true are rendered. That flag is the publication gate.
"""
import html
import json
import pathlib
import sys
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).parent
CONTENT = HERE / "content.json"
BOARD = HERE / "board.json"
OUT_HTML = HERE / "index.html"
OUT_README = HERE / "PROFILE_README.md"

VISIBILITY_LABEL = {
    "public": "public repo",
    "private": "private repo",
    "planned": "planned",
}

# Where the built site is served from. Card links are relative; the profile
# README lives on github.com and needs them absolute.
SITE_BASE = "https://raengineered.github.io"


def load():
    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    if BOARD.exists():
        by_id = {p["id"]: p for p in data["projects"]}
        for item in json.loads(BOARD.read_text(encoding="utf-8")):
            by_id.setdefault(item["id"], {}).update(item)
        data["projects"] = list(by_id.values())
    return data


def published(data):
    return [p for p in data["projects"] if p.get("publish")]


def grouped(data):
    """Projects grouped by area, in content.json area order."""
    out = []
    for key, area in data["areas"].items():
        items = [p for p in published(data) if p.get("area") == key]
        if items:
            out.append((key, area, items))
    return out


def render_html(data):
    e = html.escape
    prof = data["profile"]
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    tabs = []
    cards = []
    for i, (key, area, items) in enumerate(grouped(data)):
        active = i == 0
        rows = []
        for p in items:
            vis = VISIBILITY_LABEL.get(p.get("visibility", "private"), "private repo")
            title = e(p["title"])
            if p.get("repo"):
                title = f'<a href="{e(p["repo"])}">{title}</a>'
            stack = "".join(f"<li>{e(s)}</li>" for s in p.get("stack", []))
            hi = "".join(f"<li>{e(h)}</li>" for h in p.get("highlights", []))
            # An "embed" fragment puts the project's actual figures on this page,
            # instead of asking the reader to click through to see them.
            embed_path = p.get("embed")
            embed_html = (HERE / embed_path).read_text(encoding="utf-8") if embed_path else ""
            # A hosted write-up is separate from the repo: a private project can
            # still publish its pages here, so link the two independently.
            writeup_label = "The full write-up &rarr;" if embed_html else "Read the write-up &rarr;"
            writeup = (
                f'<p class="writeup"><a href="{e(p["site"])}">{writeup_label}</a></p>'
                if p.get("site") else ""
            )
            card_class = "card featured" if embed_html else "card"
            embed_block = f'<div class="embed">{embed_html}</div>' if embed_html else ""
            rows.append(f"""
        <article class="{card_class}">
          <h3>{title} <span class="vis vis-{e(p.get('visibility','private'))}">{e(vis)}</span></h3>
          <p>{e(p.get("blurb",""))}</p>
          <ul class="hi">{hi}</ul>
          <ul class="stack">{stack}</ul>
          {embed_block}{writeup}
        </article>""")
        tabs.append(
            f'<button type="button" class="tab{" active" if active else ""}" '
            f'id="tabbtn-{e(key)}" data-tab="{e(key)}" role="tab" '
            f'aria-selected="{"true" if active else "false"}" '
            f'aria-controls="tab-{e(key)}">{e(area["name"])}</button>'
        )
        cards.append(f"""
      <section class="area{" active" if active else ""}" id="tab-{e(key)}" role="tabpanel"
               aria-labelledby="tabbtn-{e(key)}"{"" if active else " hidden"}>
        <header class="area-head">
          <h2>{e(area["name"])}</h2>
          <p>{e(area.get("blurb",""))}</p>
        </header>
        <div class="grid">{"".join(rows)}</div>
      </section>""")

    links = " · ".join(
        f'<a href="{e(l["href"])}">{e(l["label"])}</a>' for l in prof.get("links", [])
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(prof["name"])} — {e(prof["tagline"])}</title>
<meta name="description" content="{e(prof["blurb"])}">
<link rel="icon" href="assets/avatar.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="assets/avatar.png">
<style>
:root {{
  color-scheme: light dark;
  /* Brand palette. Accent is the avatar red #5A1322 darkened; neutrals are
     kept neutral so nothing reads pink. */
  --bg:#fbfaf9; --fg:#171414; --muted:#68635f; --line:#e2dedb;
  --card:#ffffff; --accent:#45101B; --gold:#8a6718; --rule:#45101B;
  --accent-soft:#f4efee; --code-bg:#f6f1f0;
  --mono: ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, monospace;
  /* aliases so the concept-car diagrams (.embed) can use their own var names */
  --ink:var(--fg); --ink-2:var(--muted); --ink-3:var(--muted); --panel:var(--card);
}}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#120F10; --fg:#F4EFEE; --muted:#98918e; --line:#2b2527;
           --card:#1A1517; --accent:#C9A24A; --gold:#C9A24A; --rule:#5A1322;
           --accent-soft:#3C0B16; --code-bg:#1a1016; }}
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; background:var(--bg); color:var(--fg);
  border-top:4px solid var(--rule);
  font:16px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
}}
.wrap {{ max-width:56rem; margin:0 auto; padding:4rem 1.25rem 6rem; }}
h1 {{ font-size:clamp(2rem,5vw,2.75rem); line-height:1.15; margin:0 0 .35rem; letter-spacing:-.02em; }}
.avatar {{ width:72px; height:72px; border-radius:.75rem; display:block; margin:0 0 1rem; }}
h1::after {{ content:""; display:block; width:2.5rem; height:3px; background:var(--gold);
             border-radius:2px; margin:.6rem 0 .1rem; }}
.tagline {{ color:var(--accent); font-weight:600; margin:0 0 .25rem; }}
.loc {{ color:var(--muted); margin:0 0 1.25rem; font-size:.9rem; }}
.lede {{ font-size:1.1rem; max-width:42rem; margin:0 0 1.5rem; }}
.links a {{ color:var(--fg); }}
hr {{ border:0; border-top:1px solid var(--line); margin:3rem 0; }}
.tabs {{ display:flex; flex-wrap:wrap; gap:.5rem; margin:0 0 2rem; }}
.tabs .tab {{
  font:inherit; font-size:.85rem; font-weight:500; color:var(--muted);
  background:transparent; border:1px solid var(--line); border-radius:2rem;
  padding:.4rem 1rem; cursor:pointer;
}}
.tabs .tab:hover {{ color:var(--fg); border-color:var(--accent); }}
.tabs .tab.active {{ color:var(--bg); background:var(--accent); border-color:var(--accent); }}
.area-head h2 {{ font-size:1.35rem; margin:0 0 .2rem; letter-spacing:-.01em; color:var(--accent); }}
.area-head p {{ color:var(--muted); margin:0 0 1.25rem; font-size:.95rem; }}
.area {{ margin-bottom:3rem; }}
.area[hidden] {{ display:none; }}
.grid {{ display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(19rem,1fr)); }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:.75rem; padding:1.25rem; }}
.card h3 {{ margin:0 0 .5rem; font-size:1.05rem; }}
.card h3 a {{ color:var(--fg); }}
.card p {{ margin:0 0 .75rem; color:var(--fg); }}
.vis {{ font-size:.7rem; font-weight:500; text-transform:uppercase; letter-spacing:.04em;
        color:var(--muted); border:1px solid var(--line); border-radius:1rem;
        padding:.1rem .5rem; white-space:nowrap; vertical-align:.15em; }}
.vis-public {{ color:var(--accent); border-color:var(--accent); }}
ul.hi {{ margin:0 0 .9rem; padding-left:1.1rem; font-size:.92rem; color:var(--muted); }}
ul.hi li {{ margin:.2rem 0; }}
ul.stack {{ list-style:none; display:flex; flex-wrap:wrap; gap:.4rem; margin:0; padding:0; }}
ul.stack li {{ font-size:.75rem; color:var(--muted); border:1px solid var(--line);
               border-radius:.35rem; padding:.1rem .45rem; }}
p.writeup {{ margin:.9rem 0 0; font-size:.85rem; }}
p.writeup a {{ color:var(--accent); font-weight:600; }}
footer {{ color:var(--muted); font-size:.85rem; border-top:1px solid var(--line); padding-top:1.5rem; }}
a {{ text-decoration-thickness:1px; text-underline-offset:2px; }}

/* ---- featured project embed (ported from concept-car/style.css) ---- */
.card.featured {{ grid-column:1 / -1; }}
.embed .lede {{ font-size:1rem; color:var(--fg); max-width:56ch; margin:.25rem 0 1.25rem; }}
.anim {{ border:1px solid var(--line); border-radius:.75rem; background:var(--card); overflow:hidden; margin:1.5rem 0; }}
.anim-head {{ display:flex; justify-content:space-between; align-items:baseline; gap:.75rem; flex-wrap:wrap;
              padding:.65rem 1rem; border-bottom:1px solid var(--line); background:var(--code-bg);
              font-family:var(--mono); font-size:.75rem; color:var(--muted); }}
.anim-head b {{ color:var(--accent); font-weight:600; }}
.anim svg {{ display:block; width:100%; height:auto; }}
.anim figcaption {{ padding:.6rem 1rem .85rem; font-size:.8rem; color:var(--muted); border-top:1px solid var(--line); }}
.sf-node rect {{ fill:var(--card); stroke:var(--line); stroke-width:1.5; }}
.sf-node text {{ font-family:var(--mono); font-size:11px; fill:var(--muted); }}
.sf-edge {{ stroke:var(--line); stroke-width:1.5; fill:none; }}
.sf-lbl {{ font-family:var(--mono); font-size:9px; fill:var(--muted); }}
.lit {{ opacity:0; fill:var(--accent-soft); stroke:var(--accent); stroke-width:2; }}
@keyframes lit-move {{0%,59%{{opacity:1}} 60%,100%{{opacity:0}}}}
@keyframes lit-p3   {{0%,59.9%{{opacity:0}} 60%,69%{{opacity:1}} 70%,100%{{opacity:0}}}}
@keyframes lit-turn {{0%,69.9%{{opacity:0}} 70%,94%{{opacity:1}} 95%,100%{{opacity:0}}}}
@keyframes lit-p2   {{0%,94.9%{{opacity:0}} 95%,100%{{opacity:1}}}}
.a-move {{ animation:lit-move 3s steps(1,end) infinite; }}
.a-p3   {{ animation:lit-p3 3s steps(1,end) infinite; }}
.a-turn {{ animation:lit-turn 3s steps(1,end) infinite; }}
.a-p2   {{ animation:lit-p2 3s steps(1,end) infinite; }}
.code-blk {{ opacity:0; }}
.code-blk text {{ font-family:var(--mono); font-size:11.5px; fill:var(--muted); }}
.code-blk .kw {{ fill:var(--accent); }}
.code-blk .hd {{ fill:var(--fg); font-weight:600; }}
.rover {{ offset-path:path("M 690,286 L 856,286 L 856,120 L 690,120 Z"); offset-rotate:0deg;
          animation:travel 12s linear infinite; }}
@keyframes travel {{
  0%{{offset-distance:0%}} 15%{{offset-distance:25%}} 25%{{offset-distance:25%}}
  40%{{offset-distance:50%}} 50%{{offset-distance:50%}}
  65%{{offset-distance:75%}} 75%{{offset-distance:75%}}
  90%{{offset-distance:100%}} 100%{{offset-distance:100%}}}}
.rover-body {{ transform-box:fill-box; transform-origin:center; animation:heading 12s linear infinite; fill:var(--accent); }}
@keyframes heading {{
  0%,17.5%{{transform:rotate(0deg)}} 23.75%,42.5%{{transform:rotate(-90deg)}}
  48.75%,67.5%{{transform:rotate(-180deg)}} 73.75%,92.5%{{transform:rotate(-270deg)}}
  98.75%,100%{{transform:rotate(-360deg)}}}}
.trail {{ stroke:var(--accent); stroke-width:2.5; fill:none; stroke-linecap:round;
          stroke-dasharray:664; animation:draw 12s linear infinite; }}
@keyframes draw {{
  0%{{stroke-dashoffset:664}} 15%{{stroke-dashoffset:498}} 25%{{stroke-dashoffset:498}}
  40%{{stroke-dashoffset:332}} 50%{{stroke-dashoffset:332}}
  65%{{stroke-dashoffset:166}} 75%{{stroke-dashoffset:166}}
  90%{{stroke-dashoffset:0}} 100%{{stroke-dashoffset:0}}}}
.pipe-seg {{ fill:var(--card); stroke:var(--line); stroke-width:1.5; }}
.pipe-lit {{ fill:var(--accent-soft); stroke:var(--accent); stroke-width:2; opacity:0; animation:plit 9s linear infinite; }}
@keyframes plit {{ 0%,2%{{opacity:0}} 4%,29%{{opacity:1}} 31%,100%{{opacity:0}} }}
.pipe-txt {{ font-family:var(--mono); font-size:11px; fill:var(--muted); }}
.pipe-sub {{ font-family:var(--mono); font-size:9px; fill:var(--muted); }}
.pipe-tok {{ fill:var(--accent); offset-path:path("M 100,150 L 380,150 L 660,150"); animation:ptravel 9s linear infinite; }}
@keyframes ptravel {{ 0%{{offset-distance:0%}} 100%{{offset-distance:100%}} }}
.v-arm {{ stroke:var(--line); stroke-width:2; fill:none; }}
@media (prefers-reduced-motion: reduce) {{
  .a-move,.a-p3,.a-turn,.a-p2,.code-blk,.rover,.rover-body,.trail,.pipe-lit,.pipe-tok {{ animation:none !important; }}
  .a-move,.code-blk:first-of-type {{ opacity:1; }}
  .trail {{ stroke-dashoffset:0; }}
}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <img class="avatar" src="assets/avatar.png" alt="" width="72" height="72">
    <h1>{e(prof["name"])}</h1>
    <p class="tagline">{e(prof["tagline"])}</p>
    <p class="loc">{e(prof["location"])}</p>
    <p class="lede">{e(prof["blurb"])}</p>
    <p class="links">{links}</p>
  </header>
  <hr>
  <nav class="tabs" role="tablist">{"".join(tabs)}</nav>
  <main>{"".join(cards)}</main>
  <footer>
    <p>Generated {built} from <code>content.json</code>. Private repositories are described but not linked; where a project has a write-up, it is hosted here.</p>
  </footer>
</div>
<script>
document.querySelectorAll(".tabs .tab").forEach(function(btn) {{
  btn.addEventListener("click", function() {{
    document.querySelectorAll(".tabs .tab").forEach(function(b) {{
      b.classList.remove("active");
      b.setAttribute("aria-selected", "false");
    }});
    document.querySelectorAll("main .area").forEach(function(s) {{
      s.classList.remove("active");
      s.hidden = true;
    }});
    btn.classList.add("active");
    btn.setAttribute("aria-selected", "true");
    var panel = document.getElementById("tab-" + btn.dataset.tab);
    panel.hidden = false;
    panel.classList.add("active");
  }});
}});
</script>
</body>
</html>
"""


def render_readme(data):
    prof = data["profile"]
    L = [
        f"## {prof['name']} — {prof['tagline']}",
        "",
        f"{prof['blurb']}",
        "",
        f"📍 {prof['location']}",
        "",
    ]
    for _key, area, items in grouped(data):
        L.append(f"### {area['name']}")
        L.append("")
        for p in items:
            name = f"**[{p['title']}]({p['repo']})**" if p.get("repo") else f"**{p['title']}**"
            tag = "" if p.get("repo") else f" _({p.get('visibility', 'private')})_"
            # Relative site paths only resolve on the Pages domain, so the README
            # needs them absolute.
            writeup = f" — [write-up]({SITE_BASE}/{p['site']})" if p.get("site") else ""
            L.append(f"- {name}{tag} — {p['blurb']}{writeup}")
        L.append("")
    L += [
        "---",
        "",
        f"<sub>Generated from <a href=\"https://github.com/{prof['handle']}/{prof['handle'].lower()}.github.io\">"
        f"{prof['handle'].lower()}.github.io</a> · "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}</sub>",
        "",
    ]
    return "\n".join(L)


def main():
    data = load()
    OUT_HTML.write_text(render_html(data), encoding="utf-8")
    OUT_README.write_text(render_readme(data), encoding="utf-8")
    n = len(published(data))
    total = len(data["projects"])
    print(f"built {OUT_HTML.name} and {OUT_README.name} — {n}/{total} projects published")
    return 0


if __name__ == "__main__":
    sys.exit(main())
