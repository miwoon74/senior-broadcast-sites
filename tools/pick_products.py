#!/usr/bin/env python3
"""
기사별 제휴 상품 자동 고르기

기사를 AI(Claude)가 읽고
  1) 상품을 붙여도 되는 기사인지 판단 (사고·참사·사망 등 무거운 기사는 건너뜀)
  2) 기사와 어울리는 상품 검색어와 상품 이름
  3) 독자를 자연스럽게 이끄는 한 줄 유도 문구
를 정한 뒤, 나라별 제휴 프로그램 링크를 만들어 기사 파일에 써 넣습니다.

사용법
  python tools/pick_products.py                 # 아직 상품을 고르지 않은 기사 전부
  python tools/pick_products.py content/kr/past/2026-10-21-am-01.md
  python tools/pick_products.py --dry-run       # 파일은 바꾸지 않고 결과만 보기
  python tools/pick_products.py --force         # 이미 고른 기사도 다시

필요한 값 (.env 또는 환경변수)
  ANTHROPIC_API_KEY      없으면 기사 태그로 간단히 고릅니다 (AI 없이)
  COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY   한국(쿠팡 파트너스) 링크용
  미국·일본 Amazon 링크는 sites.json의 affiliate_program.tag 를 씁니다.
"""
import datetime as dt
import hashlib
import hmac
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
MODEL = "claude-haiku-5-5"
FIELDS = ["product_checked", "product_skip", "product_keyword", "product_name", "product_note", "product_url"]

LANG_NAME = {"en": "English (United States)", "ja": "Japanese", "ko": "Korean"}


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


# ---------- 기사 파일 읽기/쓰기 ----------
def read_article(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return None, None, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, m.group(1), m.group(2)


def write_fields(path, fm, body, values):
    lines = [l for l in fm.splitlines() if l.split(":", 1)[0].strip() not in FIELDS]
    for k in FIELDS:
        if k in values and values[k] not in (None, ""):
            v = str(values[k]).replace('"', "'")
            lines.append(f'{k}: "{v}"' if k not in ("product_checked", "product_skip") else f"{k}: {v}")
    path.write_text("---\n" + "\n".join(lines) + "\n---\n" + body, encoding="utf-8")


# ---------- AI로 고르기 ----------
PROMPT = """You choose ONE affiliate product to place at the end of a nostalgic news article for older readers.
Write every text field in {lang}.

Rules:
- If the article is about a disaster, accident, death, crime, war, terrorism, illness outbreak, or any tragedy, set "skip": true. Never attach products to tragic news.
- Otherwise pick something a reader of this story would genuinely enjoy: books, photo collections, DVDs/music of that era, retro-style goods, reissued memorabilia, travel guides, hobby items related to the story.
- Never pick medicine, supplements or health products, and never promise health effects.
- "search_keyword": 2-5 words a shopper would type on {shop} to find this kind of product (no brand you are unsure exists).
- "product_name": a short generic product description (not an invented brand name).
- "pitch": one warm, natural sentence (max 60 characters in Korean/Japanese, 110 in English) that links the story's memory to the product. No exaggeration, no "buy now".

Return only JSON: {{"skip": bool, "reason": str, "search_keyword": str, "product_name": str, "pitch": str}}

Article title: {title}
Summary: {summary}
Tags: {tags}
Body:
{body}
"""


def ask_claude(site, meta, body, shop):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    prompt = PROMPT.format(lang=LANG_NAME[site["lang"]], shop=shop, title=meta.get("title", ""),
                           summary=meta.get("summary", ""), tags=meta.get("tags", ""), body=body[:3000])
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps({"model": MODEL, "max_tokens": 400,
                         "messages": [{"role": "user", "content": prompt}]}).encode(),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    text = "".join(c.get("text", "") for c in data.get("content", []))
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else None


HEAVY = {
    "ko": ["참사", "사고", "붕괴", "사망", "숨져", "희생", "테러", "전쟁", "학살", "재난", "화재", "추락", "침몰"],
    "ja": ["事故", "惨事", "崩落", "死亡", "犠牲", "テロ", "戦争", "災害", "火災", "墜落", "沈没", "事件"],
    "en": ["disaster", "crash", "collapse", "killed", "death", "dies", "terror", "war", "massacre", "fire", "sank"],
}


def simple_pick(site, meta):
    """AI 키가 없을 때: 무거운 기사는 건너뛰고, 나머지는 사이트 기본 추천 상품을 붙입니다"""
    text = " ".join([meta.get("title", ""), meta.get("summary", ""), meta.get("tags", "")]).lower()
    if any(w in text for w in HEAVY[site["lang"]]):
        return {"skip": True, "reason": "무거운 기사(단어 확인)"}
    d = site.get("affiliate_program", {}).get("default_product")
    if not d:
        return None
    return {"skip": False, "reason": "기본 추천", "search_keyword": d["keyword"], "product_name": d["name"], "pitch": d["pitch"]}


# ---------- 나라별 제휴 링크 ----------
def amazon_link(prog, keyword):
    if not prog.get("tag"):
        return ""
    q = urllib.parse.quote_plus(keyword)
    return f"https://{prog['domain']}/s?k={q}&tag={urllib.parse.quote(prog['tag'])}"


def coupang_link(keyword):
    ak, sk = os.environ.get("COUPANG_ACCESS_KEY"), os.environ.get("COUPANG_SECRET_KEY")
    if not (ak and sk):
        return ""
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
    signed = dt.datetime.now(dt.timezone.utc).strftime("%y%m%dT%H%M%SZ")
    sig = hmac.new(sk.encode(), (signed + "POST" + path).encode(), hashlib.sha256).hexdigest()
    auth = f"CEA algorithm=HmacSHA256, access-key={ak}, signed-date={signed}, signature={sig}"
    search = "https://www.coupang.com/np/search?q=" + urllib.parse.quote(keyword)
    req = urllib.request.Request("https://api-gateway.coupang.com" + path,
                                 data=json.dumps({"coupangUrls": [search]}).encode(),
                                 headers={"Authorization": auth, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    items = data.get("data") or []
    return items[0].get("shortenUrl", "") if items else ""


def make_link(prog, keyword):
    try:
        if prog.get("type") == "amazon":
            return amazon_link(prog, keyword)
        if prog.get("type") == "coupang":
            return coupang_link(keyword)
    except Exception as e:  # 링크를 못 만들어도 고른 결과는 남깁니다
        print(f"    링크 만들기 실패: {e}")
    return ""


# ---------- 실행 ----------
def main(argv):
    load_env()
    dry, force = "--dry-run" in argv, "--force" in argv
    paths = [Path(a) for a in argv if not a.startswith("--")]
    cfg = json.loads((ROOT / "sites.json").read_text(encoding="utf-8"))
    sites = {s["id"]: s for s in cfg["sites"]}
    if not paths:
        paths = sorted(p for p in CONTENT.glob("*/*/*.md") if p.parent.name != "pages")
    use_ai = bool(os.environ.get("ANTHROPIC_API_KEY"))
    print(f"기사 {len(paths)}개 확인 · {'AI(Claude)로 고르기' if use_ai else 'AI 키 없음 → 무거운 기사는 건너뛰고 기본 추천 상품'}")

    for path in paths:
        path = path.resolve()
        site = sites.get(path.relative_to(CONTENT).parts[0])
        meta, fm, body = read_article(path)
        if not site or meta is None:
            continue
        if meta.get("product_checked") == "true" and not force:
            continue
        prog = site.get("affiliate_program", {})
        shop = prog.get("shop", "an online store")
        pick = ask_claude(site, meta, body, shop) if use_ai else simple_pick(site, meta)
        if not pick:
            print(f"  ? {path.name}: 결과를 못 받음, 건너뜀")
            continue
        if pick.get("skip"):
            print(f"  - {path.name}: 상품 안 붙임 ({pick.get('reason', '')})")
            values = {"product_checked": "true", "product_skip": "true"}
        else:
            url = make_link(prog, pick["search_keyword"])
            print(f"  + {path.name}: {pick['product_name']} / {pick['pitch']}" + ("" if url else "  (링크 대기)"))
            values = {"product_checked": "true", "product_keyword": pick["search_keyword"],
                      "product_name": pick["product_name"], "product_note": pick["pitch"], "product_url": url}
        if not dry:
            write_fields(path, fm, body, values)


if __name__ == "__main__":
    main(sys.argv[1:])
