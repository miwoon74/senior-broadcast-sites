#!/usr/bin/env python3
"""
시니어 방송국 홈페이지 생성기

  python build.py            -> public/ 폴더에 실제 사이트를 만듭니다 (GitHub Pages가 이 폴더를 올립니다)
  python build.py --preview  -> preview.html 한 파일로 모든 페이지 미리보기를 만듭니다
  python build.py --property=tm  -> 한 브랜드만 (도메인별 배포용). snb = 시니어 뉴스, tm = 오늘의 과거 뉴스

기사 파일 위치:  content/<브랜드>/<나라>/<코너>/<날짜>-<am|pm>[-번호].md
  예) content/snb/jp/senior/2026-10-20-am.md
      content/tm/kr/past/2026-10-21-am-01.md
"""
import hashlib
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

import markdown
from jinja2.utils import htmlsafe_json_dumps
from markdown.extensions.toc import slugify_unicode
from html import unescape

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
from charts import render_charts  # noqa: E402  기사 속 ```chart``` 블록 → 그래프
from jinja2 import Environment, FileSystemLoader, select_autoescape


# 2026-11-04: style.css·site.js 를 고쳐 올려도 방문자 브라우저가 옛 파일을 계속 쓰던 문제(캐시) →
# 파일 내용이 바뀌면 주소 끝 ?v= 값이 바뀌어 새 파일을 받게 함
_ASSET_V = {}


def asset_version(name):
    if not name.endswith((".css", ".js")):
        return ""
    if name not in _ASSET_V:
        import hashlib
        f = Path(__file__).resolve().parent / "static" / name
        _ASSET_V[name] = "?v=" + hashlib.sha1(f.read_bytes()).hexdigest()[:8] if f.is_file() else ""
    return _ASSET_V[name]

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUT = ROOT / "public"
PER_PAGE = 20

# 2026-11-28 사용자 "사이트에 날짜별로 검색할 수 있는 기능을 넣었으면 해. 일렬로 배치하면 보기 힘드니까":
# 코너 목록·날짜별 쪽 위에 달 달력(방송 있는 날만 눌림, 편수 표시) + 날짜 입력칸, 날짜별 쪽(/<코너>/day/YYYY-MM-DD.html)은 카드 바둑판.
# 날짜별 쪽은 목록과 내용이 겹치므로 검색 제외(noindex, 사이트맵 제외)·링크는 따라감.
CAL_LABELS = {
    "ko": {"title": "날짜로 찾기", "week": "일월화수목금토", "mon": 0, "ym": "{y}년 {m}월", "prev": "이전 달", "next": "다음 달",
           "jump": "날짜", "go": "보기", "prev_day": "‹ 전날", "next_day": "다음 날 ›", "count": "{n}편", "none": "이 날짜에는 방송이 없어 가까운 날로 갑니다"},
    "ja": {"title": "日付で探す", "week": "日月火水木金土", "mon": 0, "ym": "{y}年{m}月", "prev": "前の月", "next": "次の月",
           "jump": "日付", "go": "表示", "prev_day": "‹ 前の日", "next_day": "次の日 ›", "count": "{n}本", "none": "この日の放送はないため近い日を表示します"},
    "en": {"title": "Find by date", "week": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], "mon": 0, "ym": "{M} {y}",
           "prev": "Previous month", "next": "Next month", "jump": "Date", "go": "Go", "prev_day": "‹ Previous day",
           "next_day": "Next day ›", "count": "{n} stories", "none": "No edition on that day - showing the nearest one"},
    "zh-CN": {"title": "按日期查找", "week": "日一二三四五六", "mon": 0, "ym": "{y}年{m}月", "prev": "上个月", "next": "下个月",
              "jump": "日期", "go": "查看", "prev_day": "‹ 前一天", "next_day": "后一天 ›", "count": "{n}篇", "none": "这一天没有内容，显示最近的一天"},
    "zh-TW": {"title": "依日期查詢", "week": "日一二三四五六", "mon": 0, "ym": "{y}年{m}月", "prev": "上個月", "next": "下個月",
              "jump": "日期", "go": "查看", "prev_day": "‹ 前一天", "next_day": "後一天 ›", "count": "{n}篇", "none": "這一天沒有內容，顯示最近的一天"},
    "es": {"title": "Buscar por fecha", "week": ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"], "mon": 1, "ym": "{M} {y}",
           "prev": "Mes anterior", "next": "Mes siguiente", "jump": "Fecha", "go": "Ver", "prev_day": "‹ Día anterior",
           "next_day": "Día siguiente ›", "count": "{n}", "none": "No hay publicación ese día; se muestra la más cercana"},
    "fr": {"title": "Chercher par date", "week": ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"], "mon": 1, "ym": "{M} {y}",
           "prev": "Mois précédent", "next": "Mois suivant", "jump": "Date", "go": "Voir", "prev_day": "‹ Jour précédent",
           "next_day": "Jour suivant ›", "count": "{n}", "none": "Rien ce jour-là : voici le jour le plus proche"},
    "de": {"title": "Nach Datum suchen", "week": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"], "mon": 1, "ym": "{M} {y}",
           "prev": "Voriger Monat", "next": "Nächster Monat", "jump": "Datum", "go": "Anzeigen", "prev_day": "‹ Vortag",
           "next_day": "Nächster Tag ›", "count": "{n}", "none": "An diesem Tag gibt es nichts - nächster Tag wird gezeigt"},
    "ru": {"title": "Поиск по дате", "week": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"], "mon": 1, "ym": "{M} {y}",
           "prev": "Предыдущий месяц", "next": "Следующий месяц", "jump": "Дата", "go": "Показать", "prev_day": "‹ Предыдущий день",
           "next_day": "Следующий день ›", "count": "{n}", "none": "В этот день публикаций нет — показан ближайший"},
}
CAL_MONTHS = {"en": "January February March April May June July August September October November December".split(),
              "es": "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(),
              "fr": "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split(),
              "de": "Januar Februar März April Mai Juni Juli August September Oktober November Dezember".split(),
              "ru": "Январь Февраль Март Апрель Май Июнь Июль Август Сентябрь Октябрь Ноябрь Декабрь".split()}


def cal_labels(lang):
    c = dict(CAL_LABELS.get(lang) or CAL_LABELS.get(lang[:2]) or CAL_LABELS["en"])
    c["week"] = list(c["week"])
    return c


def make_calendar(day_counts, lang, href):
    """day_counts {date: 편수} → 달 목록(최근 달부터). 칸 = None(빈칸) 또는 {d, iso, n, href}. 방송 없는 날은 href 없음."""
    import calendar as _cal
    CL = cal_labels(lang)
    months = sorted({(d.year, d.month) for d in day_counts}, reverse=True)
    out = []
    for y, mo in months:
        weeks = _cal.Calendar(firstweekday=0 if CL["mon"] else 6).monthdatescalendar(y, mo)
        rows = []
        for wk in weeks:
            rows.append([None if d.month != mo else
                         {"d": d.day, "iso": d.isoformat(), "n": day_counts.get(d, 0), "href": href(d) if day_counts.get(d) else ""}
                         for d in wk])
        names = CAL_MONTHS.get(lang[:2])
        out.append({"key": f"{y}-{mo:02d}", "title": CL["ym"].format(y=y, m=mo, M=names[mo - 1] if names else mo), "weeks": rows})
    return out


SLOT_TIME = {"am": "07:00:00", "pm": "17:00:00"}
FILE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(am|pm)(?:-(\d{1,2}))?\.md$")
YEAR_RE = re.compile(r"(1[89]\d\d|20\d\d)")
ERA_RE = re.compile(r"(昭和|平成|令和)(\d{1,2})年")   # 일본 연호 → 서기
ERA_BASE = {"昭和": 1925, "平成": 1988, "令和": 2018}

WEEKDAYS = {
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "ja": list("月火水木金土日"),
    "ko": list("월화수목금토일"),
    # 2026-11-17 레시피(gw) 9개 언어: 중국어 간체·번체, 스페인어, 프랑스어, 독일어, 러시아어
    "zh-CN": list("一二三四五六日"),
    "zh-TW": list("一二三四五六日"),
    "es": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"],
    "fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
    "de": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
    "ru": ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"],
}
MONTHS = {
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
    "ru": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"],
}
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]


# ---------- 날짜 표시 ----------
DASH_RE = re.compile(r"[ \t]*[—―]+[ \t]*")


def cjk_dashes(text, lang):
    """한국어·일본어 글의 줄표(—)를 그 언어에 맞는 문장부호로 바꾼다 (2026-11-02).
    한·일 글에서 줄표를 자주 쓰면 번역투·AI 글처럼 보임. 제목 줄은 가운뎃점, 본문은 쌍점.
    ``` 블록(그래프 데이터) 안은 손대지 않는다. 영어 글은 그대로."""
    if not text or lang[:2] not in ("ko", "ja"):
        return text
    ja = lang[:2] == "ja"
    out, fenced = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and ("—" in line or "―" in line):
            head = line.lstrip().startswith("#")
            def rep(m, head=head):
                if head:
                    return "・" if ja else " · "
                before = line[:m.start()].rstrip()
                # 앞이 문장 끝(…요/…다, …です/…ください)이면 마침표, 아니면 쌍점
                if re.search(r"(요|다|니다|세요)$", before):
                    return ". "
                if re.search(r"(です|ます|ください|ません|でした|ました|ましょう)$", before):
                    return "。"
                if re.search(r":\s|：", before):   # 쌍점이 이미 있으면 쉼표 (쌍점 두 번 방지)
                    return "、" if ja else ", "
                return "：" if ja else ": "
            line = DASH_RE.sub(rep, line)
        out.append(line)
    return "\n".join(out)


def fmt_date(d, lang):
    w = WEEKDAYS.get(lang, WEEKDAYS["en"])[d.weekday()]
    if lang in ("zh-CN", "zh-TW"):
        return f"{d.year}年{d.month}月{d.day}日（星期{w}）"
    if lang in MONTHS:
        m = MONTHS[lang][d.month - 1]
        if lang == "es":
            return f"{w}, {d.day} de {m} de {d.year}"
        if lang == "fr":
            return f"{w} {d.day} {m} {d.year}"
        if lang == "de":
            return f"{w}, {d.day}. {m} {d.year}"
        return f"{w}, {d.day} {m} {d.year} г."
    if lang == "en":
        return f"{w}, {MONTHS_EN[d.month - 1]} {d.day}, {d.year}"
    if lang == "ja":
        return f"{d.year}年{d.month}月{d.day}日({w})"
    return f"{d.year}년 {d.month}월 {d.day}일 ({w})"


def fmt_short(d, lang):
    if lang in ("zh-CN", "zh-TW"):
        return f"{d.month}月{d.day}日"
    if lang in ("es", "fr", "ru"):
        return f"{d.day}/{d.month}"
    if lang == "de":
        return f"{d.day}.{d.month}."
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


def recipe_data(raw):
    if not raw.startswith("{"):
        return None
    r = json.loads(raw)
    r["instructions"] = [{"@type": "HowToStep", "text": t} for t in r.get("steps", [])]
    return r


# ── 2026-11-19 GEO·AEO (AI 검색·답변 엔진이 글을 바로 인용하기 좋게) ──────────────────────────
# 한눈에 보기 상자·질문형 정리·구조화 데이터에 쓰는 글자 (9개 언어). 지어낸 질문은 넣지 않고,
# 기사에 이미 있는 사실(날짜·분량·출처)과 원고의 질문형 소제목만 씀.
GEO_LABELS = {
    "ko": {"glance": "한눈에 보기", "faq": "질문으로 정리", "ago": "{n}년 전", "serves": "{n}인분", "ing": "재료 {n}가지",
           "steps": "{n}단계", "sources": "출처 {n}곳", "q_happened": "{date}에는 무슨 일이 있었나요?"},
    "ja": {"glance": "ひと目でわかる", "faq": "質問で整理", "ago": "{n}年前", "serves": "{n}人分", "ing": "材料{n}つ",
           "steps": "{n}ステップ", "sources": "出典{n}件", "q_happened": "{date}には何がありましたか？"},
    "en": {"glance": "At a glance", "faq": "Questions answered", "ago": "{n} years ago", "serves": "Serves {n}", "ing": "{n} ingredients",
           "steps": "{n} steps", "sources": "{n} sources", "sources1": "1 source", "q_happened": "What happened on {date}?"},
    "zh-CN": {"glance": "要点速览", "faq": "问答整理", "ago": "{n}年前", "serves": "{n}人份", "ing": "{n}种食材",
              "steps": "{n}个步骤", "sources": "{n}个来源", "q_happened": "{date}发生了什么？"},
    "zh-TW": {"glance": "重點速覽", "faq": "問答整理", "ago": "{n}年前", "serves": "{n}人份", "ing": "{n}種食材",
              "steps": "{n}個步驟", "sources": "{n}個來源", "q_happened": "{date}發生了什麼？"},
    "es": {"glance": "De un vistazo", "faq": "Preguntas y respuestas", "ago": "hace {n} años", "serves": "Para {n} personas",
           "ing": "{n} ingredientes", "steps": "{n} pasos", "sources": "{n} fuentes", "sources1": "1 fuente", "q_happened": "¿Qué pasó el {date}?"},
    "fr": {"glance": "En bref", "faq": "Questions et réponses", "ago": "il y a {n} ans", "serves": "Pour {n} personnes",
           "ing": "{n} ingrédients", "steps": "{n} étapes", "sources": "{n} sources", "sources1": "1 source", "q_happened": "Que s'est-il passé le {date} ?"},
    "de": {"glance": "Auf einen Blick", "faq": "Fragen und Antworten", "ago": "vor {n} Jahren", "serves": "Für {n} Personen",
           "ing": "{n} Zutaten", "steps": "{n} Schritte", "sources": "{n} Quellen", "sources1": "1 Quelle", "q_happened": "Was geschah am {date}?"},
    "ru": {"glance": "Коротко", "faq": "Вопросы и ответы", "ago": "{n} лет назад", "serves": "Порций: {n}", "ing": "Ингредиентов: {n}",
           "steps": "Шагов: {n}", "sources": "Источников: {n}", "q_happened": "Что произошло {date}?"},
}
EN_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
HREF_RE = re.compile(r'<a href="(https?://[^"]+)"')
H2_SEC_RE = re.compile(r"<h2[^>]*>(.*?)</h2>(.*?)(?=<h2|\Z)", re.S)
P_RE = re.compile(r"<p>(.*?)</p>", re.S)


def geo_labels(lang):
    return GEO_LABELS.get(lang) or GEO_LABELS.get(lang[:2], GEO_LABELS["en"])


def plain_date(d, lang):
    """요일 없는 날짜 (질문 문장 안에 넣는 용)"""
    if lang[:2] in ("ko",):
        return f"{d.year}년 {d.month}월 {d.day}일"
    if lang[:2] in ("ja", "zh"):
        return f"{d.year}年{d.month}月{d.day}日"
    if lang == "en":
        return f"{EN_MONTHS[d.month - 1]} {d.day}, {d.year}"
    m = MONTHS.get(lang, [""] * 12)[d.month - 1]
    return {"es": f"{d.day} de {m} de {d.year}", "fr": f"{d.day} {m} {d.year}", "de": f"{d.day}. {m} {d.year}"}.get(lang, d.isoformat())


def strip_tags(h):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", h))).strip()


def geo_info(site, a):
    lang, G = site["lang"], geo_labels(site["lang"])
    html = a["body_html"]
    sources = list(dict.fromkeys(u for u in HREF_RE.findall(html)))[:30]
    facts, faq, hist = [], [], None
    if site.get("property") == "tm" and a["year"].isdigit():
        try:
            hist = date(int(a["year"]), a["date"].month, a["date"].day)
        except ValueError:
            hist = None
        if hist and 1800 < hist.year <= a["date"].year:
            facts += [plain_date(hist, lang), G["ago"].format(n=a["date"].year - hist.year)]
    r = a.get("recipe")
    if r:
        if r.get("yield"):
            facts.append(G["serves"].format(n=r["yield"]))
        if r.get("ingredients"):
            facts.append(G["ing"].format(n=len(r["ingredients"])))
        if r.get("steps"):
            facts.append(G["steps"].format(n=len(r["steps"])))
    if sources:
        facts.append((G.get("sources1") if len(sources) == 1 else None) or G["sources"].format(n=len(sources)))
    # 상자 제목: 과거뉴스는 그날 무슨 일이 있었는지 묻는 질문, 나머지는 '한눈에 보기'
    box_q = G["q_happened"].format(date=plain_date(hist, lang)) if hist and a["summary"] and not a["lead_dup"] else ""
    if box_q:
        faq.append({"q": box_q, "a": a["summary"], "visible": False})
    # 원고에 이미 있는 질문형 소제목(? ？로 끝남) → 그 단락 첫 문단이 답
    for h, sec in H2_SEC_RE.findall(html):
        q = strip_tags(h)
        if not q.endswith(("?", "？")):
            continue
        ps = [strip_tags(x) for x in P_RE.findall(sec)]
        ans = " ".join(x for x in ps[:2] if x)[:600]
        if ans:
            faq.append({"q": q, "a": ans, "visible": True})
    return {"sources": sources, "facts": facts, "box_q": box_q, "faq": faq[:8],
            "hist_iso": hist.isoformat() if hist else ""}


def load_articles(site):
    articles = []
    for sec in site["sections"]:
        folder = CONTENT / site["src"] / sec["id"]
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.md")):
            m = FILE_RE.match(path.name)
            if not m:
                print(f"  [건너뜀] 파일 이름 형식이 다릅니다: {path.relative_to(ROOT)}")
                continue
            y, mo, d, slot, num = m.groups()
            order = int(num) if num else 0
            meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
            day = date(int(y), int(mo), int(d))
            # hold_until: 그 날짜가 되기 전엔 사이트에 넣지 않음 (방송 전에 미리 올려 둔 글)
            hold = meta.get("hold_until", "").strip()
            if hold and date.today().isoformat() < hold:
                continue
            # wait_video: 유튜브 예약 공개 전 영상의 글(게시 프로그램이 공개 시각이 지나면 이 줄을 빼고 다시 올림) —
            # 비공개 영상이 사이트에 '비공개 동영상·로그인'으로 뜨지 않게 (2026-11-18)
            if meta.get("wait_video", "").strip():
                continue
            slug = f"{y}-{mo}-{d}-{slot}" + (f"-{order:02d}" if num else "")
            yt = meta.get("youtube", "").strip()
            # 사진: 기사에 image가 있으면 그것을, 없으면 유튜브 썸네일을 씁니다
            image = meta.get("image", "").strip()
            if image and not image.startswith("http"):
                image = f"{site['base']}/images/{image}"
            ym = YEAR_RE.search(meta.get("title", ""))
            era = ERA_RE.search(meta.get("title", "")) if not ym else None
            articles.append({
                "site": site["id"],
                "section": sec["id"],
                "section_label": sec["label"],
                "date": day,
                "slot": slot,
                "order": order,
                "slug": slug,
                "title": cjk_dashes(meta.get("title", slug), site["lang"]),
                "summary": tidy_summary(cjk_dashes(meta.get("summary", ""), site["lang"])),
                "youtube": yt,
                "thumb": image or (f"https://i.ytimg.com/vi/{yt}/hqdefault.jpg" if yt else ""),
                "photo": bool(image),
                "image_credit": meta.get("image_credit", ""),
                # 연도: 기사 파일의 year가 있으면 그것, 없으면 제목에서 찾음
                "year": meta.get("year", "").strip() or (ym.group(1) if ym else (str(ERA_BASE[era.group(1)] + int(era.group(2))) if era else "")),
                # 검수 대기 원고(미리보기 전용): 표시 문구를 보여 주고 검색에서 제외
                "review": meta.get("review", "").strip(),
                # 기사별 제휴 상품 (방송국이 기사와 어울리는 상품을 붙일 때)
                "product": {"name": meta.get("product_name", ""), "url": meta.get("product_url", ""),
                            "note": meta.get("product_note", "")} if meta.get("product_name") else None,
                "product_skip": meta.get("product_skip", "") == "true",
                "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
                # 레시피(할머니): 구글 레시피 검색용 구조화 데이터 (재료·만드는 법·몇 인분)
                "recipe": recipe_data(meta.get("recipe", "")),
                "sample": meta.get("sample", "").lower() == "true",
                "body_html": markdown.markdown(render_charts(cjk_dashes(body, site["lang"]), site["lang"]), extensions=["extra", "toc"],
                                               extension_configs={"toc": {"slugify": slugify_unicode}}),
                # 요약이 본문 첫 문단과 같으면 기사 위 요약 줄은 생략(같은 글 두 번 방지)
                "lead_dup": bool(meta.get("summary")) and cjk_dashes(meta.get("summary", ""), site["lang"])[:40] in cjk_dashes(body, site["lang"]),
                "path": f"{site['base']}/{sec['id']}/{slug}.html",
                "iso": f"{day.isoformat()}T{SLOT_TIME[slot]}{site['timezone']}",
                "date_long": fmt_date(day, site["lang"]),
                "date_short": fmt_short(day, site["lang"]),
            })
    for a in articles:
        a["geo"] = geo_info(site, a)
    # 최신 기사가 앞에 오도록 (날짜, 오후>오전)
    # 같은 방송 안에서는 편성 순서(01, 02 …)대로
    articles.sort(key=lambda a: (a["date"], a["slot"] == "pm", -a["order"]), reverse=True)
    return articles


def load_page(site, name):
    path = CONTENT / site["src"] / "pages" / f"{name}.md"
    if not path.exists():
        return None
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    return {"title": meta.get("title", name), "body_html": markdown.markdown(body, extensions=["extra"])}


# ---------- 생성기 ----------
# 2026-11-01 시청자 유도 설계 P0: 기사 아래 "이 회차의 다른 이야기"와 "함께 보면 좋은 다른 방송"
FLOW_LABELS = {
    "ko": {"edition": "이 회차의 다른 이야기", "pos": "{total}개 중 {n}번째 이야기", "next": "다음 이야기",
           "cross": "함께 보면 좋은 다른 방송", "match": "같은 주제", "latest": "최신"},
    "ja": {"edition": "この回のほかのニュース", "pos": "{total}本中{n}本目", "next": "次のニュース",
           "cross": "あわせて見たい姉妹サイト", "match": "関連", "latest": "最新"},
    "en": {"edition": "More from this edition", "pos": "Story {n} of {total}", "next": "Next story",
           "cross": "From our sister sites", "match": "Related", "latest": "Latest"},
    "zh-CN": {"edition": "本期其他内容", "pos": "第{n}篇，共{total}篇", "next": "下一篇",
              "cross": "我们的其他网站", "match": "相关", "latest": "最新"},
    "zh-TW": {"edition": "本期其他內容", "pos": "第{n}篇，共{total}篇", "next": "下一篇",
              "cross": "我們的其他網站", "match": "相關", "latest": "最新"},
    "es": {"edition": "Más de esta edición", "pos": "{n} de {total}", "next": "Siguiente",
           "cross": "Nuestros otros sitios", "match": "Relacionado", "latest": "Lo último"},
    "fr": {"edition": "Dans cette édition", "pos": "{n} sur {total}", "next": "Suivant",
           "cross": "Nos autres sites", "match": "Sur le même thème", "latest": "Le plus récent"},
    "de": {"edition": "Mehr aus dieser Ausgabe", "pos": "{n} von {total}", "next": "Weiter",
           "cross": "Unsere anderen Seiten", "match": "Verwandt", "latest": "Neueste"},
    "ru": {"edition": "Ещё в этом выпуске", "pos": "{n} из {total}", "next": "Далее",
           "cross": "Наши другие сайты", "match": "По теме", "latest": "Новое"},
}


# 2026-11-13 사용자 결정: 사이트 영상은 맛보기만 → 유튜브로 보냄(조회·구독·추천이 유튜브에 쌓이게).
#   시니어·과거뉴스(긴 영상): 45초에서 멈추고 "전체 영상은 유튜브에서" / 할머니(쇼츠): 끝까지 보고 다른 레시피 3개.
# 2026-11-18 사용자 "광고 들어오기 전까지 빈 광고 자리에 관련 사진 아무거나": 광고 번호가 없는 자리 →
# 같은 사이트의 사진 있는 글 하나(사진+제목, 누르면 그 글). 광고 번호를 넣으면 자동으로 광고로 바뀜.
PROMO_LABELS = {"ko": "이런 이야기도 있어요", "ja": "こちらもどうぞ", "en": "You might also like",
                "zh-CN": "推荐阅读", "zh-TW": "推薦閱讀", "es": "También te puede interesar",
                "fr": "À découvrir aussi", "de": "Auch interessant", "ru": "Вам может быть интересно"}
PREVIEW_SECONDS = 45
VIDEO_LABELS = {
    "ko": {"cont": "미리 보기는 여기까지입니다", "full": "전체 영상은 유튜브에서 보기", "again": "처음부터 다시 보기",
           "more": "다른 레시피도 보세요", "channel": "채널에서 레시피 더 보기"},
    "ja": {"cont": "続きはYouTubeで", "full": "続きをYouTubeで見る", "again": "もう一度見る",
           "more": "ほかのレシピもどうぞ", "channel": "チャンネルでレシピをもっと見る"},
    "en": {"cont": "That's the preview", "full": "Watch the full video on YouTube", "again": "Watch again",
           "more": "More recipes to try", "channel": "More recipes on our channel"},
    "zh-CN": {"cont": "预览到此结束", "full": "在YouTube观看完整视频", "again": "重新观看",
              "more": "再看看其他食谱", "channel": "在频道观看更多食谱（英语）"},
    "zh-TW": {"cont": "預覽到此結束", "full": "在YouTube觀看完整影片", "again": "重新觀看",
              "more": "再看看其他食譜", "channel": "在頻道觀看更多食譜（英語）"},
    "es": {"cont": "Fin del avance", "full": "Ver el video completo en YouTube", "again": "Ver de nuevo",
           "more": "Más recetas para probar", "channel": "Más recetas en nuestro canal (en inglés)"},
    "fr": {"cont": "Fin de l'aperçu", "full": "Voir la vidéo complète sur YouTube", "again": "Revoir",
           "more": "D'autres recettes à essayer", "channel": "Plus de recettes sur notre chaîne (en anglais)"},
    "de": {"cont": "Ende der Vorschau", "full": "Ganzes Video auf YouTube ansehen", "again": "Nochmal ansehen",
           "more": "Weitere Rezepte", "channel": "Mehr Rezepte auf unserem Kanal (auf Englisch)"},
    "ru": {"cont": "Конец превью", "full": "Смотреть видео целиком на YouTube", "again": "Посмотреть снова",
           "more": "Другие рецепты", "channel": "Больше рецептов на нашем канале (на английском)"},
}


# ------------------------------------------------------------------ 제목·요약 줄바꿈 (2026-11-18)
# 사용자 "영상 옆 글자가 다음 줄에 한 글자만 내려가고 단어 중간에서 끊긴다, 자동으로 맞춰지게, 모바일도":
# ① 제목의 '｜' 뒤(부제)는 새 줄로 (tt 필터) ② 일본어·중국어는 단어(구절) 사이에서만 줄을 바꿈 —
#    일본어 BudouX(Google, Apache-2.0), 중국어 jieba(MIT)로 구절을 나눠 <wbr> + keep-all
# ③ CSS text-wrap: balance(제목)·pretty(요약)로 마지막 줄에 한두 글자만 남지 않게.
_SEG = {}
_PUNCT = re.compile(r"^[\s、。，．,.!?！？：:；;）)」』】〉》”’・…ー～〜|｜]+$")


def _segments(text, lang):
    if lang.startswith("ja"):
        if "ja" not in _SEG:
            try:
                import budoux
                _SEG["ja"] = budoux.load_default_japanese_parser().parse
            except Exception:
                _SEG["ja"] = None
        f = _SEG["ja"]
        return f(text) if f else None
    if lang.startswith("zh"):
        if "zh" not in _SEG:
            try:
                import logging
                import jieba
                jieba.setLogLevel(logging.WARNING)
                _SEG["zh"] = lambda t: list(jieba.cut(t))
            except Exception:
                _SEG["zh"] = None
        f = _SEG["zh"]
        return f(text) if f else None
    return None


def _kind(ch):
    o = ord(ch)
    if 0x3040 <= o <= 0x309F:
        return "h"
    if 0x30A0 <= o <= 0x30FF or ch == "ー":
        return "k"
    if 0x4E00 <= o <= 0x9FFF or ch in "々〆":
        return "c"
    return "o"


def _ja_split(seg):
    parts, cur = [], ""
    for ch in seg:
        if cur and _kind(ch) in ("c", "k") and _kind(ch) != _kind(cur[-1]) and len(cur) >= 2:
            parts.append(cur)
            cur = ""
        cur += ch
    return parts + ([cur] if cur else [])


def _phrase_html(text, lang):
    """일본어·중국어 → 구절마다 <wbr>, keep-all 상자로 감쌈. 다른 언어는 그대로(이스케이프만)."""
    segs = _segments(text, lang) if text else None
    if not segs:
        return str(escape(text or ""))
    if lang.startswith("ja"):             # 긴 구절(9자 이상)은 글자 종류가 바뀌는 곳(히라가나→한자·가타카나 등)에서 한 번 더 나눔
        segs = [y for x in segs for y in (_ja_split(x) if len(x) > 8 else [x])]
    out = []
    for seg in segs:                      # 문장부호·공백은 앞 구절에 붙임(줄 첫머리에 '，' 가 오지 않게)
        if out and _PUNCT.match(seg):
            out[-1] += seg
        elif (out and lang.startswith("ja") and len(out[-1]) <= 2 and all(_kind(c) == "h" for c in out[-1])
              and _kind(seg[0]) == "h"):      # 'おば|あちゃん' 같은 짧은 히라가나 조각은 붙임
            out[-1] += seg
        else:
            out.append(seg)
    return '<span class="px">' + "<wbr>".join(str(escape(x)) for x in out) + "</span>"


_SUB_SPLIT = re.compile(r"\s*[｜|]\s*")


_END = re.compile(r'[.!?。！？」』）)\]…"”’*]$')
_SENT = re.compile(r'[。！？]|[.!?](?=[\s"”’」』）)]|$)')


def tidy_summary(s):
    """2026-11-18: 게시 프로그램이 요약을 160자에서 그냥 잘라 'crunchy r' 처럼 단어 중간에서 끝나던 것 →
    문장이 끝난 곳까지(남는 길이가 절반 이상이면), 아니면 마지막 낱말 경계에서 자르고 '…'."""
    s = (s or "").strip()
    if not s or _END.search(s):
        return s
    ends = [m.end() for m in _SENT.finditer(s)]
    if ends and ends[-1] >= len(s) * 0.5:
        return s[:ends[-1]].rstrip()
    cut = s.rfind(" ")
    if cut >= len(s) * 0.6:
        s = s[:cut]
    return s.rstrip(" ,、，;；:：-—") + "…"


def title_html(text, lang, split=True):
    parts = _SUB_SPLIT.split(text or "", maxsplit=1) if split else [text or ""]
    main = _phrase_html(parts[0], lang)
    if len(parts) == 2 and parts[1].strip():
        return main + '<span class="t-sub">' + _phrase_html(parts[1], lang) + "</span>"
    return main



class Builder:
    def __init__(self, config, preview=False, prop=None):
        self.config = config
        self.preview = preview
        self.prop = prop  # 한 브랜드만 만들 때 (도메인별 배포용): "snb" 또는 "tm"
        props = {p["id"]: p for p in config.get("properties", [])}
        if prop and props.get(prop, {}).get("base_url"):
            self.base_url = props[prop]["base_url"].rstrip("/")
        else:
            self.base_url = config.get("base_url", "").rstrip("/")
        self.env = Environment(loader=FileSystemLoader(str(TEMPLATES)),
                               autoescape=select_autoescape(["html", "xml"]),
                               trim_blocks=True, lstrip_blocks=True)
        from jinja2 import pass_context
        from markupsafe import Markup

        @pass_context
        def tt(ctx, text):          # 보이는 제목: 부제 새 줄 + 구절 줄바꿈
            return Markup(title_html(text, (ctx.get("site") or {}).get("lang", "")))

        @pass_context
        def pt(ctx, text):          # 보이는 요약: 구절 줄바꿈만
            return Markup(_phrase_html(text, (ctx.get("site") or {}).get("lang", "")))
        def ld(obj):                # 구조화 데이터: 빈 값(None·빈 목록) 빼고 안전하게 JSON 으로
            def clean(o):
                if isinstance(o, dict):
                    return {k: clean(v) for k, v in o.items() if v not in (None, "", [], {})}
                if isinstance(o, list):
                    return [clean(v) for v in o if v not in (None, "", [], {})]
                return o
            return htmlsafe_json_dumps(clean(obj), ensure_ascii=False)
        self.env.filters["ld"] = ld
        self.env.filters["tt"] = tt
        self.env.filters["pt"] = pt
        self.fragments = []   # 미리보기용
        self.sitemaps = {}    # site_id -> [(url, lastmod)]
        self.llms = {}        # site base -> llms.txt 재료 (2026-11-19 GEO)

    @staticmethod
    def page_id(path):
        return "p-" + re.sub(r"[^a-z0-9]+", "-", path.lower().replace(".html", "")).strip("-")

    def item_list(self, arts):
        return [{"@type": "ListItem", "position": i + 1, "url": self.abs_url(x["path"]), "name": x["title"]}
                for i, x in enumerate(arts)] if self.base_url else []

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
            promo_seed=int(hashlib.sha1(out_path.encode()).hexdigest()[:6], 16),
            show_placeholders=self.config.get("show_placeholders", True),
            asset=lambda p: prefix + "assets/" + p + asset_version(p),
            asset_v=asset_version,
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
            self.sitemaps.setdefault(site["base"], []).append((self.abs_url(out_path), ctx.get("lastmod", "")))

    @staticmethod
    def apply_year_range(site):
        """'오늘의 과거 뉴스'처럼 범위가 매년 움직이는 사이트: {from}, {to}를 올해 기준으로 채웁니다.
        예) years_back [56, 20] → 2026년이면 1970–2006, 2027년이면 1971–2007"""
        if "years_back" not in site:
            return site
        now = date.today().year
        rng = {"{from}": str(now - site["years_back"][0]), "{to}": str(now - site["years_back"][1])}

        def fill(v):
            if isinstance(v, str):
                for k, x in rng.items():
                    v = v.replace(k, x)
                return v
            if isinstance(v, dict):
                return {k: fill(x) for k, x in v.items()}
            if isinstance(v, list):
                return [fill(x) for x in v]
            return v
        site = fill(site)
        site["year_range"] = (now - site["years_back"][0], now - site["years_back"][1])
        return site

    def make_cross_index(self):
        """같은 언어의 다른 브랜드 기사 목록(공개된 것만). 각 브랜드 도메인의 절대 주소로 잇습니다."""
        props = {p["id"]: p for p in self.config.get("properties", [])}
        out = {}
        for s in self.config["sites"]:
            own = props.get(s["property"], {}).get("base_url", "").rstrip("/")
            if not own:
                continue
            s = self.apply_year_range(dict(s))
            s["src"] = f"{s['property']}/{s['id']}"
            s["base"] = s["id"]
            for a in load_articles(s):
                if a["sample"] or a["review"]:
                    continue
                out.setdefault(s["lang"], []).append({
                    "property": s["property"], "brand": s["name"], "title": a["title"], "tags": set(a["tags"]),
                    "date": a["date"], "slot": a["slot"], "url": f"{own}/{a['path']}",
                    "thumb": a["thumb"] if (not a["thumb"] or a["thumb"].startswith("http")) else f"{own}/{a['thumb']}"})
        return out

    def cross_for(self, site, a, limit=2):
        """주제 꼬리표가 겹치는 옆 브랜드 글 → 없으면 그 브랜드의 최신 글 (브랜드마다 1개, 빈칸 없음)."""
        picks = []
        mine = set(a["tags"])
        by_brand = {}
        for c in self.cross.get(site["lang"], []):
            if c["property"] == site["property"]:
                continue
            by_brand.setdefault(c["property"], []).append(c)
        for prop, items in by_brand.items():
            scored = sorted(items, key=lambda c: (len(mine & c["tags"]), c["date"], c["slot"] == "pm"), reverse=True)
            best = scored[0]
            picks.append(dict(best, matched=bool(mine & best["tags"])))
        picks.sort(key=lambda c: (c["matched"], c["date"]), reverse=True)
        return picks[:limit]

    def make_network(self):
        """같은 언어의 다른 브랜드 사이트로 오가는 버튼 (시니어뉴스 ↔ 과거뉴스 ↔ 할머니).
        브랜드마다 도메인이 따로 있으면 그 도메인 주소, 아직 없으면 지금 함께 올라가는 주소를 씁니다."""
        props = {p["id"]: p for p in self.config.get("properties", [])}
        shared = self.config.get("base_url", "").rstrip("/")
        out = {}
        for s in self.config["sites"]:
            s = self.apply_year_range(dict(s))
            own = props.get(s["property"], {}).get("base_url", "").rstrip("/")
            if own:
                link = f"{own}/{s['id']}/"
            elif self.prop and shared:
                link = f"{shared}/{s['property']}/{s['id']}/"
            else:
                link = None   # 한 번에 만드는 경우: 상대 주소
            out.setdefault(s["lang"], []).append({"property": s["property"], "id": s["id"], "name": s["name"],
                                                  "tagline": s.get("tagline", ""), "icon": s.get("favicon", ""),
                                                  "abs": link, "rel": f"{s['property']}/{s['id']}/index.html"})
        return out

    def build_site(self, site):
        arts = load_articles(site)
        # 같은 글의 다른 언어판 (할머니처럼 세 나라가 같은 레시피를 번역해 올리는 브랜드): hreflang
        if site.get("translations"):
            for a in arts:
                a["alternates"] = [{"lang": o["lang"], "url": self.abs_url(f"{o['base']}/{a['section']}/{a['slug']}.html")}
                                   for o in self.sites_by_prop.get(site["property"], [])
                                   if (CONTENT / o["src"] / a["section"] / (a["slug"] + ".md")).exists()]
                # 2026-11-17: 검색엔진 기본판(x-default) = 영어판
                en = next((x for x in a["alternates"] if x["lang"] == "en"), None)
                if en and len(a["alternates"]) > 1:
                    a["alternates"].append({"lang": "x-default", "url": en["url"]})
        # 2026-11-17 레시피 9개 언어: 화면 위 언어 바꾸기 줄 (같은 브랜드의 모든 언어판, 기사면 그 기사의 번역판으로)
        lang_sites = [{"lang": o["lang"], "label": o.get("lang_name") or o["name"], "base": o["base"], "src": o["src"],
                       "current": o["id"] == site["id"]}
                      for o in self.sites_by_prop.get(site["property"], [])] if site.get("translations") else []
        L = site["labels"]
        print(f"- {site['name']} ({site['base']}): 기사 {len(arts)}개")
        by_section = {s["id"]: [a for a in arts if a["section"] == s["id"]] for s in site["sections"]}

        # 코너별 가장 최근 날짜의 오전/오후 방송
        # 코너별 가장 최근 날짜의 방송: 오전/오후 편성(editions)과, 홈에 보여줄 묶음(today_by_section)
        today_by_section, editions_by_section = {}, {}
        for sid, items in by_section.items():
            if items:
                last = items[0]["date"]
                day = sorted([a for a in items if a["date"] == last], key=lambda a: (a["slot"], a["order"]))
                eds = {"am": [a for a in day if a["slot"] == "am"], "pm": [a for a in day if a["slot"] == "pm"]}
                editions_by_section[sid] = eds
                # 하루 기사가 많으면 가장 최근 방송(오후가 있으면 오후)만
                today_by_section[sid] = day if len(day) <= 6 else (eds["pm"] or eds["am"])
        # 첫 화면의 '오늘' 날짜·지난 글은 첫 코너 기준 (레시피 사이트의 '집에서 만들기' 메뉴 글이 섞이지 않게)
        prim = by_section.get(site["sections"][0]["id"], []) if site["sections"] else arts
        latest_day = prim[0]["date"] if prim else date.today()
        latest_date = prim[0]["date"] if prim else None
        earlier = [a for a in prim if a["date"] != latest_date]
        # 2026-11-18 사용자 "오늘의 과거뉴스는 오전밖에 없는데 '오전' 표시, 지난 방송이 8개만이라 17일 뉴스가 2개만 보임":
        # 지난 방송을 날짜별 묶음(그날 이야기 전부, 방송 순서대로)으로 — 최근 4일
        earlier_days = []
        for a in earlier:
            if not earlier_days or earlier_days[-1]["date"] != a["date"]:
                if len(earlier_days) == 4:
                    break
                earlier_days.append({"date": a["date"], "label": fmt_date(a["date"], site["lang"]), "stories": []})
            earlier_days[-1]["stories"].append(a)
        for g in earlier_days:
            g["stories"].sort(key=lambda a: (a["slot"], a["order"]))
        seen, site_videos = set(), []
        for x in arts:   # 영상 끝에 보여 줄 같은 사이트의 다른 영상(최신순, 예시·검수 대기 제외)
            if x.get("youtube") and not x["sample"] and not x["review"] and x["youtube"] not in seen:
                seen.add(x["youtube"])
                site_videos.append({"id": x["youtube"], "title": x["title"]})
        common = dict(site=site, L=L, sections=[x for i, x in enumerate(site["sections"]) if i == 0 or by_section.get(x["id"])], all_articles=arts, lang_sites=lang_sites,
                      site_videos=site_videos[:8], preview_seconds=PREVIEW_SECONDS,
                      promo_pool=[x for x in arts if x["thumb"] and not x["sample"] and not x["review"]][:24],
                      PROMO=PROMO_LABELS.get(site["lang"]) or PROMO_LABELS.get(site["lang"][:2], PROMO_LABELS["en"]),
                      VL=VIDEO_LABELS.get(site["lang"]) or VIDEO_LABELS.get(site["lang"][:2], VIDEO_LABELS["en"]),
                      network=[dict(n, tracked_url=(n["abs"].rstrip("/") + "/" + "?utm_source=" + site["property"] + "&utm_medium=internal_referral&utm_campaign=cross_brand_202611&utm_content=site_banner") if n["abs"] else None) for n in self.network.get(site["lang"], []) if n["property"] != site["property"]],
                      by_section=by_section, today_by_section=today_by_section,
                      editions_by_section=editions_by_section, earlier_articles=earlier, earlier_days=earlier_days,
                      latest_day=fmt_date(latest_day, site["lang"]), now_year=latest_day.year,
                      hero_photos=[dict(ph, src=ph["src"] if ph["src"].startswith("http") else f"{site['base']}/images/{ph['src']}")
                                   for ph in site.get("hero", {}).get("photos", [])])

        # 2026-11-04: 사진 없는 기사의 SNS 미리보기 그림 주소가 사이트 첫 주소("…com/")로 깨져 나가던 것 →
        # 사진 없을 때는 사이트 대표 사진(헤더 사진), 그것도 없으면 사이트 아이콘. 첫 화면에도 같은 그림.
        hp = common["hero_photos"]
        if hp:
            share_img = hp[0]["src"] if hp[0]["src"].startswith("http") else self.abs_url(hp[0]["src"])
        elif site.get("favicon"):
            share_img = self.abs_url("assets/" + site["favicon"])
        else:
            share_img = ""

        # 2026-11-19 GEO: 모든 쪽에 '누가 만드는 사이트인지'(Organization·WebSite) — AI 답변이 출처를 밝힐 때 씀
        home_abs = self.abs_url(f"{site['base']}/index.html")
        same = [u for u in (site.get("youtube_channel"), site.get("facebook_page"), site.get("instagram"),
                            f"https://x.com/{site['x_account']}" if site.get("x_account") else "", site.get("band")) if u]
        common["org"] = {"id": home_abs + "#org", "home": home_abs, "name": site["name"],
                         "type": "Organization" if site["property"] == "gw" else "NewsMediaOrganization",
                         "logo": self.abs_url("assets/" + site["favicon"]) if site.get("favicon") else "",
                         "same_as": same, "about": self.abs_url(f"{site['base']}/about.html")}
        common["GL"] = geo_labels(site["lang"])
        public = [x for x in arts if not x["sample"] and not x["review"]]
        self.llms[site["base"]] = {"site": site, "home": home_abs, "arts": public[:50],
                                   "sections": [x for x in common["sections"]]}

        # 2026-11-28 첫 화면 '지난 방송'에도 날짜로 찾기 달력(첫 코너 기준)
        if site["sections"]:
            s0 = site["sections"][0]
            hd = {}
            for a in prim:
                if not a["sample"] and not a["review"]:
                    hd[a["date"]] = hd.get(a["date"], 0) + 1
            home_cal = make_calendar(hd, site["lang"], lambda d, s=s0: f"{site['base']}/{s['id']}/day/{d.isoformat()}.html")
            common.update(cal=home_cal, CL=cal_labels(site["lang"]), cal_show=home_cal[0]["key"] if home_cal else "",
                          cal_prefix=f"{site['base']}/{s0['id']}/day/__D__.html", cal_days=sorted(d.isoformat() for d in hd))

        # 홈
        self.render(f"home_{site['layout']}.html", f"{site['base']}/index.html",
                    page_title=site["name"], description=site["description"], nav="home",
                    itemlist=self.item_list(public[:10]),
                    og_image=share_img, lastmod=latest_day.isoformat(), **common)
        for k in ("cal", "CL", "cal_show", "cal_prefix", "cal_days"):   # 코너 목록·날짜별 쪽은 코너마다 따로 넘김
            common.pop(k, None)

        # 코너 목록 (페이지 나누기)
        for si, sec in enumerate(site["sections"]):
            items = by_section[sec["id"]]
            if si and not items:   # 둘째 코너부터는 글이 생겨야 목록을 만듦 (빈 페이지가 검색에 안 잡히게)
                continue
            pages = [items[i:i + PER_PAGE] for i in range(0, len(items), PER_PAGE)] or [[]]
            # 2026-11-28 날짜로 찾기: 이 코너의 날짜별 묶음·달력 (예시·검수 대기 글은 날짜별 쪽에서 뺌)
            day_map = {}
            for a in items:
                if not a["sample"] and not a["review"]:
                    day_map.setdefault(a["date"], []).append(a)
            day_href = lambda d, s=sec: f"{site['base']}/{s['id']}/day/{d.isoformat()}.html"
            cal = make_calendar({d: len(v) for d, v in day_map.items()}, site["lang"], day_href)
            CL = cal_labels(site["lang"])
            cal_ctx = dict(cal=cal, CL=CL, cal_prefix=f"{site['base']}/{sec['id']}/day/__D__.html",
                           cal_days=sorted(d.isoformat() for d in day_map))
            for n, chunk in enumerate(pages, start=1):
                name = "index.html" if n == 1 else f"page-{n}.html"
                groups = []
                for a in chunk:
                    if groups and groups[-1]["date"] == a["date"]:
                        groups[-1]["items"].append(a)
                    else:
                        groups.append({"date": a["date"], "label": a["date_long"], "items": [a]})
                for g in groups:
                    g["items"].sort(key=lambda a: (a["slot"], a["order"]))
                pager = {
                    "n": n, "total": len(pages),
                    "newer": None if n == 1 else (f"{site['base']}/{sec['id']}/" + ("index.html" if n == 2 else f"page-{n - 1}.html")),
                    "older": f"{site['base']}/{sec['id']}/page-{n + 1}.html" if n < len(pages) else None,
                }
                title = sec["label"] if n == 1 else f"{sec['label']} ({L['page']} {n})"
                self.render("list.html", f"{site['base']}/{sec['id']}/{name}",
                            page_title=title, description=sec["desc"], nav=sec["id"], section=sec,
                            itemlist=self.item_list([x for x in chunk if not x["sample"] and not x["review"]]),
                            groups=groups, pager=pager, cal_show=cal[0]["key"] if cal else "", **cal_ctx, **common)

            # 날짜별 쪽 (그날 방송 카드 바둑판 + 전날/다음 날 + 달력) — 검색 제외(목록과 겹침)
            days_sorted = sorted(day_map)
            for di, d in enumerate(days_sorted):
                day_items = sorted(day_map[d], key=lambda a: (a["slot"], a["order"]))
                self.render("day.html", day_href(d),
                            page_title=f"{fmt_date(d, site['lang'])} · {sec['label']}", description=sec["desc"],
                            nav=sec["id"], section=sec, day_label=fmt_date(d, site["lang"]), day_items=day_items,
                            prev_day=day_href(days_sorted[di - 1]) if di > 0 else None,
                            next_day=day_href(days_sorted[di + 1]) if di + 1 < len(days_sorted) else None,
                            cal_show=f"{d.year}-{d.month:02d}", cal_current=d.isoformat(), noindex=True,
                            lastmod=d.isoformat(), **cal_ctx, **common)

            # 기사 (이전/다음은 같은 코너 안에서 시간 순서)
            for i, a in enumerate(items):
                newer = items[i - 1] if i > 0 else None
                older = items[i + 1] if i + 1 < len(items) else None
                recent = [x for x in items if x is not a][:5]
                edition = sorted([x for x in items if x["date"] == a["date"] and x["slot"] == a["slot"]],
                                 key=lambda x: x["order"])
                if len(edition) < 2:
                    edition = []
                self.render("article.html", a["path"],
                            page_title=a["title"], description=a["summary"] or site["description"],
                            nav=sec["id"], section=sec, a=a, newer=newer, older=older, recent=recent,
                            edition=edition, cross=self.cross_for(site, a), FL=FLOW_LABELS.get(site["lang"]) or FLOW_LABELS.get(site["lang"][:2], FLOW_LABELS["en"]),
                            og_type="article", noindex=a["sample"] or bool(a["review"]),
                            og_image=(a["thumb"] if a["thumb"].startswith("http") else self.abs_url(a["thumb"])) if a["thumb"] else share_img,
                            lastmod=a["date"].isoformat(), **common)

            # RSS (네이버·구글 뉴스 수집용)
            if not self.preview:
                self.write_rss(site, sec, items)

        # 소개 / 개인정보처리방침 (애드센스 승인에 필요)
        for name in ("about", "privacy") + tuple(pg["id"] for pg in site.get("extra_pages", [])):
            page = load_page(site, name)
            if page and site.get("year_range"):
                page["body_html"] = page["body_html"].replace("{from}", str(site["year_range"][0])).replace("{to}", str(site["year_range"][1]))
            if page:
                self.render("page.html", f"{site['base']}/{name}.html",
                            page_title=page["title"], description=site["description"], nav=name,
                            page=page, **common)

    def write_rss(self, site, sec, items):
        link = self.abs_url(f"{site['base']}/{sec['id']}/index.html")
        rows = []
        for a in items[:30]:
            if a["sample"] or a["review"]:
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
        dest = OUT / site["base"] / sec["id"] / "feed.xml"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(xml, encoding="utf-8")

    # 2026-11-19 GEO: AI 검색·답변 엔진 크롤러를 이름으로 허용 (* 만으로도 허용이지만, 일부 엔진은 자기 이름 줄을 먼저 봄)
    AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User",
               "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot", "Applebot-Extended", "Bingbot",
               "DuckAssistBot", "Amazonbot", "meta-externalagent", "MistralAI-User", "Yeti", "CCBot"]

    def write_llms(self):
        """llms.txt (llmstxt.org): AI가 사이트를 한 번에 이해하도록 사이트 소개·코너·최신 글 목록을 글자 파일로.
        도메인 맨 위 /llms.txt = 그 브랜드 모든 언어판, /<나라>/llms.txt = 그 언어판 최신 50개."""
        def block(info, n):
            site = info["site"]
            out = [f"## {site['name']} ({site['lang']})", "", f"{site['description']}", "",
                   f"- [{site['name']}]({info['home']})"]
            for sec in info["sections"]:
                out.append(f"- [{sec['label']}]({self.abs_url(site['base'] + '/' + sec['id'] + '/index.html')}): {sec.get('desc', '')}")
            out.append(f"- [About]({self.abs_url(site['base'] + '/about.html')})")
            out += ["", "### Latest", ""]
            for a in info["arts"][:n]:
                out.append(f"- [{a['title']}]({self.abs_url(a['path'])}): {a['summary']}")
            return out + [""]
        by_prop = {}
        for base, info in self.llms.items():
            by_prop.setdefault(info["site"]["property"], []).append((base, info))
        names = {p["id"]: p["name"] for p in self.config.get("properties", [])}
        notes = {
            "snb": "> Daily news for older adults on health, money and safety. Every article lists its sources "
                   "(official statistics and agencies) at the end. Photos marked as illustrative are not of the people in the story.",
            "tm": "> What happened on this day 20-56 years ago, in Korea, Japan and the United States, six stories a day. "
                  "Each article lists its sources (newspaper archives, public records). Archive photos carry their source "
                  "and license; photos not taken at the event and AI-made illustrations are labelled as such.",
            "gw": "> One traditional grandma recipe a day, in 9 languages: full ingredients, steps, the old books it comes "
                  "from and what research says, with sources. Recipes describe traditional food customs and are not medical advice.",
        }
        for prop, items in by_prop.items():
            note = notes.get(prop, "")
            head = [f"# {names.get(prop, prop)}", "", note, ""]
            for base, info in items:
                (OUT / base / "llms.txt").write_text("\n".join([f"# {info['site']['name']}", "", note, ""] + block(info, 50)),
                                                    encoding="utf-8")
            if self.prop:   # 도메인별 배포: 도메인 맨 위
                body = head + sum((block(info, 15) for _, info in items), [])
                (OUT / "llms.txt").write_text("\n".join(body), encoding="utf-8")

    def write_seo_files(self):
        lines = ["User-agent: *", "Allow: /", ""] + [f"User-agent: {b}" for b in self.AI_BOTS] + ["Allow: /", ""]
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
        # 2026-11-04 IndexNow(Bing·네이버·Yandex 등에 새 글을 바로 알리는 표준): 사이트 주인 확인용 열쇠 파일
        key = self.config.get("indexnow_key")
        if key:
            (OUT / f"{key}.txt").write_text(key, encoding="utf-8")

    def run(self):
        if not self.preview:
            if OUT.exists():
                shutil.rmtree(OUT)
            (OUT / "assets").mkdir(parents=True)
            for f in STATIC.iterdir():
                shutil.copy(f, OUT / "assets" / f.name)
            (OUT / ".nojekyll").write_text("")

        sites = []
        for s in self.config["sites"]:
            if self.prop and s["property"] != self.prop:
                continue
            s = self.apply_year_range(s)
            s["src"] = f"{s['property']}/{s['id']}"                   # 기사 폴더: content/<브랜드>/<나라>
            s["base"] = s["id"] if self.prop else s["src"]            # 사이트 주소 경로
            sites.append(s)
        self.sites_by_prop = {}
        for s in sites:
            self.sites_by_prop.setdefault(s["property"], []).append(s)
        self.network = self.make_network()
        self.cross = self.make_cross_index()
        props = [dict(p, sites=[s for s in sites if s["property"] == p["id"]])
                 for p in self.config.get("properties", []) if not self.prop or p["id"] == self.prop]
        if not self.preview:
            for site in sites:
                imgs = CONTENT / site["src"] / "images"
                if imgs.exists():
                    shutil.copytree(imgs, OUT / site["base"] / "images")
        self.render("root.html", "index.html", sites=sites, properties=props, page_title="Senior News Bureau",
                    description="Senior News Bureau: United States, Japan, Korea")
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
            self.render("404.html", "404.html", sites=sites, properties=props, page_title="404", description="", noindex=True)
            self.write_seo_files()
            if self.base_url:
                self.write_llms()
            # 애드센스 ads.txt: 도메인 맨 위에 있어야 함 → 브랜드 하나만 만들 때(도메인별 배포) 그 브랜드의 게시자 번호로
            pub = next((p.get("adsense_publisher") for p in self.config.get("properties", []) if p["id"] == self.prop), "") if self.prop else ""
            if pub:
                (OUT / "ads.txt").write_text(f"google.com, {pub}, DIRECT, f08c47fec0942fa0\n", encoding="utf-8")
            if not self.prop:  # 예전 주소(/us/ /jp/ /kr/)로 들어온 사람을 새 주소로 안내
                for old, new in {"us": "snb/us", "jp": "snb/jp", "kr": "tm/kr"}.items():
                    d = OUT / old
                    d.mkdir(exist_ok=True)
                    (d / "index.html").write_text(
                        f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=../{new}/">'
                        f'<link rel="canonical" href="../{new}/"><a href="../{new}/">{new}</a>', encoding="utf-8")
            print(f"사이트 완성: {OUT}")
            if not self.base_url:
                print("  참고: sites.json의 base_url을 채우면 사이트맵·검색 주소(canonical)가 완성됩니다.")


if __name__ == "__main__":
    cfg = json.loads((ROOT / "sites.json").read_text(encoding="utf-8"))
    prop = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--property=")), None)
    Builder(cfg, preview="--preview" in sys.argv, prop=prop).run()
