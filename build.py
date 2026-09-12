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

    cards = []
    for key, area, items in grouped(data):
        rows = []
        for p in items:
            vis = VISIBILITY_LABEL.get(p.get("visibility", "private"), "private repo")
            title = e(p["title"])
            if p.get("repo"):
                title = f'<a href="{e(p["repo"])}">{title}</a>'
            stack = "".join(f"<li>{e(s)}</li>" for s in p.get("stack", []))
            hi = "".join(f"<li>{e(h)}</li>" for h in p.get("highlights", []))
            # A hosted write-up is separate from the repo: a private project can
            # still publish its pages here, so link the two independently.
            writeup = (
                f'<p class="writeup"><a href="{e(p["site"])}">Read the write-up &rarr;</a></p>'
                if p.get("site") else ""
            )
            rows.append(f"""
        <article class="card">
          <h3>{title} <span class="vis vis-{e(p.get('visibility','private'))}">{e(vis)}</span></h3>
          <p>{e(p.get("blurb",""))}</p>
          <ul class="hi">{hi}</ul>
          <ul class="stack">{stack}</ul>{writeup}
        </article>""")
        cards.append(f"""
      <section class="area">
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
}}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#120F10; --fg:#F4EFEE; --muted:#98918e; --line:#2b2527;
           --card:#1A1517; --accent:#C9A24A; --gold:#C9A24A; --rule:#5A1322; }}
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
.area-head h2 {{ font-size:1.35rem; margin:0 0 .2rem; letter-spacing:-.01em; color:var(--accent); }}
.area-head p {{ color:var(--muted); margin:0 0 1.25rem; font-size:.95rem; }}
.area {{ margin-bottom:3rem; }}
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
  <main>{"".join(cards)}</main>
  <footer>
    <p>Generated {built} from <code>content.json</code>. Private repositories are described but not linked; where a project has a write-up, it is hosted here.</p>
  </footer>
</div>
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
