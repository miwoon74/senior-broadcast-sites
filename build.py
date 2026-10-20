#!/usr/bin/env python3
"""
시니어 방송국 홈페이지 생성기

  python build.py            -> public/ 폴더에 실제 사이트를 만듭니다 (GitHub Pages가 이 폴더를 올립니다)
  python build.py --preview  -> preview.html 한 파일로 모든 페이지 미리보기를 만듭니다

기사 파일 위치:  content/<사이트>/<코너>/<날짜>-<am|pm>.md
  예) content/jp/senior/2026-10-20-am.md
"""
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUT = ROOT / "public"
PER_PAGE = 20
SLOT_TIME = {"am": "07:00:00", "pm": "17:00:00"}
FILE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(am|pm)\.md$")
YEAR_RE = re.compile(r"(1[89]\d\d|20\d\d)")

WEEKDAYS = {
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "ja": list("月火水木金土日"),
    "ko": list("월화수목금토일"),
}
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]


# ---------- 날짜 표시 ----------
def fmt_date(d, lang):
    w = WEEKDAYS[lang][d.weekday()]
    if lang == "en":
        return f"{w}, {MONTHS_EN[d.month - 1]} {d.day}, {d.year}"
    if lang == "ja":
        return f"{d.year}年{d.month}月{d.day}日({w})"
    return f"{d.year}년 {d.month}월 {d.day}일 ({w})"


def fmt_short(d, lang):
    if lang == "en":
        return f"{MONTHS_EN[d.month - 1][:3]} {d.day}"
    if lang == "ja":
        return f"{d.month}/{d.day}"
    return f"{d.month}.{d.day}"


# ---------- 기사 읽기 ----------
def parse_front_matter(text):
    meta, body = {}, text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            _, fm, body = parts
            for line in fm.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, body.strip()


def load_articles(site):
    articles = []
    for sec in site["sections"]:
        folder = CONTENT / site["id"] / sec["id"]
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.md")):
            m = FILE_RE.match(path.name)
            if not m:
                print(f"  [건너뜀] 파일 이름 형식이 다릅니다: {path.relative_to(ROOT)}")
                continue
            y, mo, d, slot = m.groups()
            meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
            day = date(int(y), int(mo), int(d))
            slug = f"{y}-{mo}-{d}-{slot}"
            yt = meta.get("youtube", "").strip()
            # 사진: 기사에 image가 있으면 그것을, 없으면 유튜브 썸네일을 씁니다
            image = meta.get("image", "").strip()
            if image and not image.startswith("http"):
                image = f"{site['id']}/images/{image}"
            ym = YEAR_RE.search(meta.get("title", ""))
            articles.append({
                "site": site["id"],
                "section": sec["id"],
                "section_label": sec["label"],
                "date": day,
                "slot": slot,
                "slug": slug,
                "title": meta.get("title", slug),
                "summary": meta.get("summary", ""),
                "youtube": yt,
                "thumb": image or (f"https://i.ytimg.com/vi/{yt}/hqdefault.jpg" if yt else ""),
                "photo": bool(image),
                "image_credit": meta.get("image_credit", ""),
                "year": ym.group(1) if ym else "",
                "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
                "sample": meta.get("sample", "").lower() == "true",
                "body_html": markdown.markdown(body, extensions=["extra"]),
                "path": f"{site['id']}/{sec['id']}/{slug}.html",
                "iso": f"{day.isoformat()}T{SLOT_TIME[slot]}{site['timezone']}",
                "date_long": fmt_date(day, site["lang"]),
                "date_short": fmt_short(day, site["lang"]),
            })
    # 최신 기사가 앞에 오도록 (날짜, 오후>오전)
    articles.sort(key=lambda a: (a["date"], a["slot"] == "pm"), reverse=True)
    return articles


def load_page(site_id, name):
    path = CONTENT / site_id / "pages" / f"{name}.md"
    if not path.exists():
        return None
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    return {"title": meta.get("title", name), "body_html": markdown.markdown(body, extensions=["extra"])}


# ---------- 생성기 ----------
class Builder:
    def __init__(self, config, preview=False):
        self.config = config
        self.preview = preview
        self.base_url = config.get("base_url", "").rstrip("/")
        self.env = Environment(loader=FileSystemLoader(str(TEMPLATES)),
                               autoescape=select_autoescape(["html", "xml"]),
                               trim_blocks=True, lstrip_blocks=True)
        self.fragments = []   # 미리보기용
        self.sitemaps = {}    # site_id -> [(url, lastmod)]

    @staticmethod
    def page_id(path):
        return "p-" + re.sub(r"[^a-z0-9]+", "-", path.lower().replace(".html", "")).strip("-")

    def abs_url(self, path):
        if not self.base_url:
            return ""
        if path.endswith("index.html"):
            path = path[: -len("index.html")]
        return f"{self.base_url}/{path}"

    def render(self, template, out_path, **ctx):
        depth = out_path.count("/")
        prefix = "../" * depth

        def url(p):
            return "#" + self.page_id(p) if self.preview else prefix + p

        ctx.update(
            url=url,
            root=prefix,
            preview=self.preview,
            fragment=self.preview,
            path=out_path,
            canonical=self.abs_url(out_path),
            show_placeholders=self.config.get("show_placeholders", True),
            asset=lambda p: prefix + "assets/" + p,
        )
        html = self.env.get_template(template).render(**ctx)
        if self.preview:
            self.fragments.append((self.page_id(out_path), html))
        else:
            dest = OUT / out_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(html, encoding="utf-8")
        site = ctx.get("site")
        if site and not ctx.get("noindex"):
            self.sitemaps.setdefault(site["id"], []).append((self.abs_url(out_path), ctx.get("lastmod", "")))

    def build_site(self, site):
        arts = load_articles(site)
        L = site["labels"]
        print(f"- {site['name']} ({site['id']}): 기사 {len(arts)}개")
        by_section = {s["id"]: [a for a in arts if a["section"] == s["id"]] for s in site["sections"]}

        # 코너별 가장 최근 날짜의 오전/오후 방송
        today_by_section = {}
        for sid, items in by_section.items():
            if items:
                last = items[0]["date"]
                today_by_section[sid] = sorted([a for a in items if a["date"] == last], key=lambda a: a["slot"])
        latest_day = arts[0]["date"] if arts else date.today()
        common = dict(site=site, L=L, sections=site["sections"], all_articles=arts,
                      by_section=by_section, today_by_section=today_by_section,
                      latest_day=fmt_date(latest_day, site["lang"]))

        # 홈
        self.render(f"home_{site['layout']}.html", f"{site['id']}/index.html",
                    page_title=site["name"], description=site["description"], nav="home",
                    lastmod=latest_day.isoformat(), **common)

        # 코너 목록 (페이지 나누기)
        for sec in site["sections"]:
            items = by_section[sec["id"]]
            pages = [items[i:i + PER_PAGE] for i in range(0, len(items), PER_PAGE)] or [[]]
            for n, chunk in enumerate(pages, start=1):
                name = "index.html" if n == 1 else f"page-{n}.html"
                groups = []
                for a in chunk:
                    if groups and groups[-1]["date"] == a["date"]:
                        groups[-1]["items"].append(a)
                    else:
                        groups.append({"date": a["date"], "label": a["date_long"], "items": [a]})
                for g in groups:
                    g["items"].sort(key=lambda a: a["slot"])
                pager = {
                    "n": n, "total": len(pages),
                    "newer": None if n == 1 else (f"{site['id']}/{sec['id']}/" + ("index.html" if n == 2 else f"page-{n - 1}.html")),
                    "older": f"{site['id']}/{sec['id']}/page-{n + 1}.html" if n < len(pages) else None,
                }
                title = sec["label"] if n == 1 else f"{sec['label']} ({L['page']} {n})"
                self.render("list.html", f"{site['id']}/{sec['id']}/{name}",
                            page_title=title, description=sec["desc"], nav=sec["id"], section=sec,
                            groups=groups, pager=pager, **common)

            # 기사 (이전/다음은 같은 코너 안에서 시간 순서)
            for i, a in enumerate(items):
                newer = items[i - 1] if i > 0 else None
                older = items[i + 1] if i + 1 < len(items) else None
                recent = [x for x in items if x is not a][:5]
                self.render("article.html", a["path"],
                            page_title=a["title"], description=a["summary"] or site["description"],
                            nav=sec["id"], section=sec, a=a, newer=newer, older=older, recent=recent,
                            og_type="article", noindex=a["sample"],
                            og_image=a["thumb"] if a["thumb"].startswith("http") else self.abs_url(a["thumb"]),
                            lastmod=a["date"].isoformat(), **common)

            # RSS (네이버·구글 뉴스 수집용)
            if not self.preview:
                self.write_rss(site, sec, items)

        # 소개 / 개인정보처리방침 (애드센스 승인에 필요)
        for name in ("about", "privacy"):
            page = load_page(site["id"], name)
            if page:
                self.render("page.html", f"{site['id']}/{name}.html",
                            page_title=page["title"], description=site["description"], nav=name,
                            page=page, **common)

    def write_rss(self, site, sec, items):
        link = self.abs_url(f"{site['id']}/{sec['id']}/index.html")
        rows = []
        for a in items[:30]:
            if a["sample"]:
                continue
            rows.append(
                "<item>"
                f"<title>{escape(a['title'])}</title>"
                f"<link>{escape(self.abs_url(a['path']))}</link>"
                f"<guid>{escape(self.abs_url(a['path']) or a['path'])}</guid>"
                f"<pubDate>{a['date'].strftime('%a, %d %b %Y')} {SLOT_TIME[a['slot']]} {site['timezone'].replace(':', '')}</pubDate>"
                f"<description>{escape(a['summary'])}</description>"
                "</item>"
            )
        xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
               f"<title>{escape(site['name'] + ' - ' + sec['label'])}</title>"
               f"<link>{escape(link)}</link><description>{escape(sec['desc'])}</description>"
               f"<language>{site['lang']}</language>" + "".join(rows) + "</channel></rss>\n")
        dest = OUT / site["id"] / sec["id"] / "feed.xml"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(xml, encoding="utf-8")

    def write_seo_files(self):
        lines = ["User-agent: *", "Allow: /"]
        for sid, urls in self.sitemaps.items():
            body = "".join(
                f"<url><loc>{escape(u)}</loc>" + (f"<lastmod>{m}</lastmod>" if m else "") + "</url>"
                for u, m in urls if u
            )
            (OUT / sid / "sitemap.xml").write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>\n',
                encoding="utf-8")
            if self.base_url:
                lines.append(f"Sitemap: {self.base_url}/{sid}/sitemap.xml")
        (OUT / "robots.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def run(self):
        if not self.preview:
            if OUT.exists():
                shutil.rmtree(OUT)
            (OUT / "assets").mkdir(parents=True)
            for f in STATIC.iterdir():
                shutil.copy(f, OUT / "assets" / f.name)
            (OUT / ".nojekyll").write_text("")
            for site in self.config["sites"]:
                imgs = CONTENT / site["id"] / "images"
                if imgs.exists():
                    shutil.copytree(imgs, OUT / site["id"] / "images")

        sites = self.config["sites"]
        self.render("root.html", "index.html", sites=sites, page_title="Senior Broadcast",
                    description="Senior Broadcast: United States, Japan, Korea")
        for site in sites:
            self.build_site(site)

        if self.preview:
            html = self.env.get_template("preview.html").render(
                fragments=self.fragments, sites=sites,
                css=(STATIC / "style.css").read_text(encoding="utf-8"),
                js=(STATIC / "site.js").read_text(encoding="utf-8"))
            (ROOT / "preview.html").write_text(html, encoding="utf-8")
            print(f"미리보기 완성: preview.html (페이지 {len(self.fragments)}개)")
        else:
            self.render("404.html", "404.html", sites=sites, page_title="404", description="", noindex=True)
            self.write_seo_files()
            print(f"사이트 완성: {OUT}")
            if not self.base_url:
                print("  참고: sites.json의 base_url을 채우면 사이트맵·검색 주소(canonical)가 완성됩니다.")


if __name__ == "__main__":
    cfg = json.loads((ROOT / "sites.json").read_text(encoding="utf-8"))
    Builder(cfg, preview="--preview" in sys.argv).run()
