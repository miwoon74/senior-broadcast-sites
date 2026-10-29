#!/usr/bin/env python3
"""
할머니 건강레시피 원고 → 사이트 기사 파일로 옮기는 도구

  python tools/import_grandma.py <REVIEW 폴더> [--preview] [--days=2026-10-30,2026-10-31] [--outbox=<YouTubePublisher\\outbox>]

  <REVIEW 폴더>: 할머니 PC의 GrandmaWisdom\\OUTPUT\\REVIEW (회차 폴더 YYYY-MM-DD_<종류>_<항목>이 들어 있음)
  --preview   : 공개 승인 전 원고도 '검수 대기' 표시와 함께 넣습니다 (미리보기 전용, 검색·RSS 제외).
                이 옵션이 없으면 그 회차의 유튜브 업로드가 승인된(UPLOAD_APPROVED.json) 언어만 넣습니다.
  --outbox    : YouTubePublisher\\outbox 폴더. 업로드 승인 여부와 올라간 영상 ID(youtube)를 여기서 읽습니다.

회차 폴더의 blog_ko.md / blog_ja.md / blog_en.md 가 각각 한국·일본·미국 사이트 기사 하나가 됩니다.
  → content/gw/<kr|jp|us>/recipe/YYYY-MM-DD-am.md
규칙
  - 원고의 자리 표시({VIDEO_EMBED}, {AFFILIATE_INGREDIENTS})는 지웁니다. 영상은 youtube: 필드로 사이트가 넣습니다.
  - 채널 소개(intro) 회차는 넣지 않습니다.
  - 해시태그(유튜브 설명란 마지막 줄)는 기사 tags 로 씁니다.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANG_SITE = {"ko": "kr", "ja": "jp", "en": "us"}
LANG_CH = {"ko": "gw_kr", "ja": "gw_jp", "en": "gw_en"}
REVIEW_TEXT = {"ko": "검수 대기 원고 · 공개 전 미리보기", "ja": "検収待ちの原稿・公開前プレビュー",
               "en": "Draft awaiting review · not published"}
GENERIC_TAGS = {"할머니의지혜", "시니어", "건강상식", "おばあちゃんの知恵", "シニア", "grandmaswisdom", "seniorliving"}
FOLDER_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_([a-z]+)_(.+)$")
PLACEHOLDER = re.compile(r"^\s*\{(VIDEO_EMBED|AFFILIATE_INGREDIENTS|BLOG_URL)\}\s*$")


def q(s):
    return '"' + str(s).replace('"', "'").replace("\n", " ").strip() + '"'


def first_paragraph(body):
    for block in body.split("\n\n"):
        b = block.strip()
        if b and not b.startswith(("#", "!", "*", ">", "-", "|", "{")):
            return re.sub(r"\s+", " ", b)[:160]
    return ""


def tags_of(desc):
    if not desc.exists():
        return []
    tags = re.findall(r"#([^\s#]+)", desc.read_text(encoding="utf-8"))
    return [t for t in tags if t.lower() not in ("shorts",) and t.lower() not in GENERIC_TAGS][:6]


def outbox_info(outbox, lang, day):
    """(승인됐는지, 영상 ID) — 승인·업로드 기록은 YouTubePublisher 가 회차 폴더에 남긴다"""
    if not outbox:
        return False, ""
    item = Path(outbox) / LANG_CH[lang] / f"{day}_DAY"
    approved = (item / "UPLOAD_APPROVED.json").exists()
    vid = ""
    for name in ("UPLOADED.json", "upload_result.json"):
        f = item / name
        if f.exists():
            try:
                j = json.loads(f.read_text(encoding="utf-8"))
                vid = j.get("video_id") or j.get("id") or ""
            except Exception:
                pass
    return approved, vid


ING_HEAD = re.compile(r"^#{2,3}\s*(재료|材料|Ingredients)", re.I)
STEP_HEAD = re.compile(r"^#{2,3}\s*(만드는\s*법|作り方|How to Make)", re.I)
SERVES_RE = re.compile(r"(\d+)\s*(인분|人分)|Serves\s*(\d+)", re.I)


def recipe_of(body):
    """블로그의 재료표·만드는 법을 구글 레시피 검색용 정보로 뽑는다 (Recipe 구조화 데이터)"""
    lines = body.splitlines()
    ings, steps, serves, mode = [], [], "", None
    for l in lines:
        t = l.strip()
        if t.startswith("#"):
            mode = "ing" if ING_HEAD.match(t) else ("step" if STEP_HEAD.match(t) else None)
            if mode == "ing":
                m = SERVES_RE.search(t)
                if m:
                    serves = m.group(1) or m.group(3)
            continue
        if mode == "ing" and t.startswith("|") and not re.match(r"^\|[-\s|:]+\|$", t):
            cells = [c.strip() for c in t.strip("|").split("|")]
            if cells and cells[0] not in ("재료", "材料", "Ingredient"):
                ings.append(" ".join(c for c in cells[:3] if c and c not in ("—", "-")))
        elif mode == "step":
            m = re.match(r"^\d+[.)]\s*(.+)$", t)
            if m:
                steps.append(m.group(1).strip())
    if not ings or not steps:
        return None
    return {"yield": serves, "ingredients": ings, "steps": steps}


def convert(md, day, tags, preview, vid, lang):
    lines = md.strip().splitlines()
    title = ""
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        lines = lines[1:]
    body = "\n".join(l for l in lines if not PLACEHOLDER.match(l))
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    fm = ["---", f"title: {q(title or day)}", f"summary: {q(first_paragraph(body))}", f"youtube: {vid}"]
    if tags:
        fm.append(f"tags: {', '.join(tags)}")
    rc = recipe_of(body)
    if rc:
        fm.append("recipe: " + json.dumps(rc, ensure_ascii=False))
    if preview:
        fm.append(f"review: {q(REVIEW_TEXT[lang])}")
    fm.append("---")
    return "\n".join(fm) + "\n\n" + body + "\n"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) if "=" in a else (a[2:], "1") for a in sys.argv[1:] if a.startswith("--"))
    if not args:
        print(__doc__)
        return 1
    review = Path(args[0])
    days = set(opts["days"].split(",")) if opts.get("days") else None
    preview = "preview" in opts
    out = []
    for folder in sorted(p for p in review.iterdir() if p.is_dir()):
        m = FOLDER_RE.match(folder.name)
        if not m:
            continue
        day, kind, _ = m.groups()
        if kind == "intro" or (days and day not in days):
            continue
        for lang, site in LANG_SITE.items():
            blog = folder / f"blog_{lang}.md"
            if not blog.exists():
                continue
            approved, vid = outbox_info(opts.get("outbox"), lang, day)
            if not approved and not preview:
                continue
            text = convert(blog.read_text(encoding="utf-8"), day,
                           tags_of(folder / f"youtube_description_{lang}.txt"), preview and not approved, vid, lang)
            dest = ROOT / "content" / "gw" / site / "recipe" / f"{day}-am.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
            out.append(f"{site} {day} {'(검수 대기)' if preview and not approved else ''}")
    print("\n".join(out) or "넣은 기사 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
