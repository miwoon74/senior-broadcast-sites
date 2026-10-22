#!/usr/bin/env python3
"""
방송국(타임머신) 원고 → 사이트 기사 파일로 옮기는 수동 픽업 도구

  python tools/import_timemachine.py <날짜 폴더> [--preview] [--slot=am|pm|all] [--out=<content 폴더>]

  <날짜 폴더>: 방송국 PC의 data/timemachine/YYYY-MM-DD 폴더(또는 그 복사본)
  --preview : 공개 승인 전 원고를 '검수 대기' 표시와 함께 넣습니다 (미리보기 전용, 검색 제외)
              이 옵션이 없으면 publication_ready / publication_approval 이 true 인 원고만 넣습니다.
  --slot    : 라이브 전 = all (나라별 12편), 라이브 후 = am(01~06) 또는 pm(07~12) 따로 픽업

규칙 (인계 문서 TIME_MACHINE_CLAUDE_MANUAL_IMPORT_20260901.md)
  - 목록 JSON의 기사 파일이 하나라도 없으면 아무것도 넣지 않고 멈춥니다.
  - 같은 id(source_id)가 이미 있으면 다시 넣지 않습니다.
  - 사진은 실제 파일이 있고 publish_ready=true 인 것만 씁니다. 없으면 대체하지 않습니다.
  - 실제 사진과 AI 삽화(kind=AI_RECONSTRUCTION)는 캡션에서 구분합니다.
  - 방송용 파일·제작 중간 파일은 가져오지 않습니다.
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COUNTRY_SITE = {"KR": "kr", "JP": "jp", "US": "us"}
SLOT = {"morning": "am", "afternoon": "pm"}

# 방송국이 '사진 없음/보류'로 남긴 줄 (사이트에는 넣지 않음)
HOLD_LINE = re.compile(r"^\*(시각자료 확인 필요|画像未確認|Visual pending review).*\*$")
IMG_LINE = re.compile(r"^!\[.*\]\((blog_visuals/[^)]+)\)\s*$")
SOURCE_HEAD = re.compile(r"^#{2,4}\s*(시각자료 출처|Image source|画像の出典|画像出典)")

TEXT = {
    "ko": {"refs": "참고 자료", "real": "실제 사진", "ai": "AI 재현 삽화(실제 사진 아님)",
           "review": "검수 대기 원고 · 공개 전 미리보기"},
    "ja": {"refs": "参考資料", "real": "実際の写真", "ai": "AIによる再現イラスト（実際の写真ではありません）",
           "review": "検収待ちの原稿・公開前プレビュー"},
    "en": {"refs": "Sources", "real": "Archival photo", "ai": "AI reconstruction (not a real photograph)",
           "review": "Draft awaiting review · not published"},
}
WARN = {
    "BLOG_DISTINCT_DEPTH_REVIEW": "내용 깊이·방송 원고와의 차별성 확인",
    "RESEARCH_GAP_PAID_BUDGET_EXHAUSTED": "추가 자료조사 예산 소진 — 사실 확인 필요",
}


def q(s):
    return '"' + str(s).replace('"', "'").replace("\n", " ").strip() + '"'


def first_paragraph(body):
    for block in body.split("\n\n"):
        b = block.strip()
        if b and not b.startswith(("#", "!", "*", ">", "-")):
            return re.sub(r"\s+", " ", b)[:160]
    return ""


def pick_photo(visuals, folder):
    """사용 가능한 첫 사진: 파일이 있고 publish_ready=true"""
    for p in visuals.get("photos", []):
        if not p.get("publish_ready"):
            continue
        local = p.get("local_file", "")
        name = local.replace("\\", "/").split("/")[-1]
        f = folder / "blog_visuals" / name
        if name and f.exists():
            return p, f
    return None, None


def convert(art, folder, lang, preview):
    md = (folder / art["illustrated_blog_file"]).read_text(encoding="utf-8")
    visuals = json.loads((folder / art["visual_manifest"]).read_text(encoding="utf-8"))
    photo, photo_file = pick_photo(visuals, folder)
    T = TEXT[lang]

    lines, skip_source = [], False
    for line in md.strip().splitlines():
        s = line.strip()
        if HOLD_LINE.match(s):
            continue
        if IMG_LINE.match(s):          # 사진은 기사 위쪽(front matter)으로 옮김
            continue
        if s.startswith("*") and photo and s.strip("*").startswith(photo.get("caption", "")[:30]):
            continue                    # 본문 속 사진 캡션 줄
        if not photo and s.startswith("*") and ("공개 보류" in s or "公開保留" in s or "on hold" in s):
            continue
        if SOURCE_HEAD.match(s):
            skip_source = not photo     # 사진을 안 쓰면 출처 문단도 뺌
        if skip_source:
            continue
        if re.match(r"^#\s", line):     # 제목은 페이지 h1이 따로 있으므로 한 단계 내림
            line = "#" + line
        lines.append(line)
    body = "\n".join(lines).strip()
    body = re.sub(r"\n-{3,}\s*$", "", body).strip()

    refs = art.get("source_urls") or []
    if refs:
        body += f"\n\n### {T['refs']}\n\n" + "\n".join(f"- <{u}>" for u in refs)

    fm = {
        "title": art["title"],
        "summary": first_paragraph(body),
        "year": art.get("historical_year", ""),
        "youtube": "",
        "source_id": art["id"],
    }
    image_name = None
    if photo:
        ext = photo_file.suffix.lower()
        image_name = f"{art['broadcast_date']}-{SLOT[art['slot']]}-{art['number']:02d}{ext}"
        kind = T["ai"] if photo.get("kind") == "AI_RECONSTRUCTION" else T["real"]
        fm["image"] = image_name
        fm["image_credit"] = f"{kind}: {photo.get('caption', '').strip()} — {photo.get('credit_line', '')}"
    if preview and not (art.get("publication_ready") and art.get("publication_approval", art.get("publication_ready"))):
        warns = [WARN.get(w, w) for w in art.get("quality_warnings", [])]
        fm["review"] = TEXT["ko"]["review"] + (" — " + " / ".join(warns) if warns else "")
    text = "---\n" + "\n".join(f"{k}: {q(v) if k != 'youtube' else v}" for k, v in fm.items()) + "\n---\n\n" + body + "\n"
    return text, photo_file, image_name


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) if "=" in a else (a[2:], True) for a in sys.argv[1:] if a.startswith("--"))
    if not args:
        print(__doc__)
        sys.exit(1)
    day = Path(args[0])
    preview = bool(opts.get("preview"))
    slot = opts.get("slot", "all")
    content = Path(opts.get("out", ROOT / "content"))

    manifests = list(day.glob("CLAUDE_SITE_MANUAL_IMPORT_*.json"))
    if not manifests:
        sys.exit(f"[중단] 목록 JSON이 없습니다: {day}")
    man = json.loads(manifests[0].read_text(encoding="utf-8"))
    arts = man["articles"]
    if slot in ("am", "pm"):
        arts = [a for a in arts if SLOT[a["slot"]] == slot]

    # 1) 준비 확인 — 하나라도 없으면 아무것도 하지 않음
    missing = []
    for a in arts:
        folder = day / a["country"] / "auto_ai_output"
        for k in ("illustrated_blog_file", "visual_manifest"):
            if not (folder / a[k]).exists():
                missing.append(f"{a['id']}: {a[k]}")
    if missing:
        sys.exit("[중단] 준비 안 된 파일이 있습니다:\n  " + "\n  ".join(missing))

    # 2) 공개 승인 확인
    if not preview:
        blocked = [a["id"] for a in arts if not a.get("publication_ready") or not man.get("publication_approval")]
        if blocked:
            sys.exit(f"[중단] 공개 승인 전 원고 {len(blocked)}편 — 미리보기는 --preview 로 실행하세요.")

    existing = set()
    for f in content.glob("tm/*/past/*.md"):
        m = re.search(r'^source_id:\s*"?([^"\n]+)', f.read_text(encoding="utf-8"), re.M)
        if m:
            existing.add(m.group(1).strip())

    added = skipped = photos = 0
    for a in arts:
        if a["id"] in existing:
            skipped += 1
            continue
        site = COUNTRY_SITE[a["country"]]
        lang = {"kr": "ko", "jp": "ja", "us": "en"}[site]
        folder = day / a["country"] / "auto_ai_output"
        text, photo_file, image_name = convert(a, folder, lang, preview)
        n = a["number"] if a["number"] <= 6 else a["number"] - 6
        dest = content / "tm" / site / "past" / f"{a['broadcast_date']}-{SLOT[a['slot']]}-{n:02d}.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        if photo_file:
            img_dir = content / "tm" / site / "images"
            img_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(photo_file, img_dir / image_name)
            photos += 1
        added += 1
    print(f"완료: {added}편 추가, {skipped}편은 이미 있어 건너뜀, 사진 {photos}장"
          + (" (미리보기 모드 — 검수 대기 표시)" if preview else ""))


if __name__ == "__main__":
    main()
