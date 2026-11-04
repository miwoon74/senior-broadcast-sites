# -*- coding: utf-8 -*-
"""새 글·고친 글을 검색 엔진에 바로 알리기 (IndexNow, Claude 2026-11-04).

사용자: "우리 사이트를 널리 퍼지게 하는 데 도움이 되는 게 있다면 다 넣으면 좋겠어".
IndexNow 한 번 보내면 Bing(미국 야후·덕덕고도 Bing 결과 사용), 네이버, Yandex, Seznam 등이 함께 받습니다.
GitHub Actions(.github/workflows/indexnow.yml)가 main 에 기사가 올라올 때마다 실행합니다.

  python tools/indexnow.py <바뀐 파일 목록 파일> [--dry-run]

규칙
  * content/<브랜드>/<나라>/<코너>/<이름>.md  ->  https://<브랜드 도메인>/<나라>/<코너>/<이름>.html
  * 예시(sample: true)·검수 대기(review:) 글은 보내지 않음 (검색 제외 글)
  * Cloudflare 가 새 글을 게시할 때까지 최대 15분 기다렸다가, 실제로 열리는 주소만 보냄
  * 첫 화면·목록·사이트맵 주소도 같이 보냄
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "senior-broadcast-sites-indexnow/1.0"


def front(md):
    m = re.match(r"^---\n(.*?)\n---", md, re.S)
    return m.group(1) if m else ""


def urls_for(paths, cfg):
    dom = {p["id"]: p["base_url"].rstrip("/") for p in cfg["properties"]}
    out = {}
    for p in paths:
        m = re.match(r"^content/([a-z]+)/([a-z]{2})/([a-z]+)/([^/]+)\.md$", p.strip())
        if not m or m.group(1) not in dom or m.group(3) == "pages":
            continue
        f = ROOT / p.strip()
        if not f.is_file():
            continue  # 지운 글
        fm = front(f.read_text(encoding="utf-8"))
        if re.search(r"^sample:\s*true", fm, re.M) or re.search(r"^review:\s*\S", fm, re.M):
            continue
        b, cc, sec, name = m.groups()
        base = dom[b]
        out.setdefault(base, set()).update({
            f"{base}/{cc}/{sec}/{name}.html", f"{base}/{cc}/", f"{base}/{cc}/{sec}/", f"{base}/{cc}/sitemap.xml"})
    return out


def live(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    dry = "--dry-run" in sys.argv
    cfg = json.loads((ROOT / "sites.json").read_text(encoding="utf-8"))
    key = cfg.get("indexnow_key")
    if not key:
        print("NO_KEY"); return 0
    paths = Path(a[0]).read_text(encoding="utf-8").splitlines() if a else []
    todo = urls_for(paths, cfg)
    if not todo:
        print("NOTHING_TO_SEND"); return 0
    rc = 0
    for base, urls in todo.items():
        urls = sorted(urls)
        arts = [u for u in urls if u.endswith(".html")]
        if not dry:
            for _ in range(30):  # 새 글이 실제로 열릴 때까지 (최대 15분)
                if all(live(u) for u in arts):
                    break
                time.sleep(30)
            urls = [u for u in urls if live(u)]
        body = {"host": base.split("//", 1)[1], "key": key, "keyLocation": f"{base}/{key}.txt", "urlList": urls}
        print("SEND", base, len(urls), "urls")
        for u in urls:
            print("  ", u)
        if dry or not urls:
            continue
        req = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print("RESULT", base, r.status)
        except urllib.error.HTTPError as e:
            print("RESULT", base, e.code, e.read()[:200])
            rc = 1 if e.code not in (200, 202) else rc
    return rc


if __name__ == "__main__":
    sys.exit(main())
