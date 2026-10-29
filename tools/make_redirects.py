#!/usr/bin/env python3
"""예전 주소(miwoon74.github.io/senior-broadcast-sites/...)로 들어온 사람과 검색엔진을 브랜드별 새 도메인으로 보냅니다.
GitHub Pages 에는 이 안내 페이지만 올라갑니다 (같은 글이 두 주소에 있으면 검색에 불리하므로)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public"
cfg = json.loads((ROOT / "sites.json").read_text(encoding="utf-8"))
dom = {p["id"]: p["base_url"].rstrip("/") for p in cfg["properties"] if p.get("base_url")}


def page(target):
    return (f'<!doctype html><meta charset="utf-8"><title>Moved</title>'
            f'<meta http-equiv="refresh" content="0; url={target}"><link rel="canonical" href="{target}">'
            f'<meta name="robots" content="noindex"><a href="{target}">{target}</a>\n')


OUT.mkdir(exist_ok=True)
links = []
for s in cfg["sites"]:
    new = f"{dom[s['property']]}/{s['id']}/"
    d = OUT / s["property"] / s["id"]
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(page(new), encoding="utf-8")
    links.append(f'<li><a href="{new}">{s["name"]}</a></li>')
for old, (prop, sid) in {"us": ("snb", "us"), "jp": ("snb", "jp"), "kr": ("tm", "kr")}.items():
    (OUT / old).mkdir(exist_ok=True)
    (OUT / old / "index.html").write_text(page(f"{dom[prop]}/{sid}/"), encoding="utf-8")
(OUT / "index.html").write_text('<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><title>Sites</title><ul>'
                                + "".join(links) + "</ul>\n", encoding="utf-8")
(OUT / ".nojekyll").write_text("")
print("redirect pages:", len(links))
