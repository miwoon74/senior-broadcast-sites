"""기사 본문의 ```chart {json}``` 블록을 그래프(SVG)로 바꾼다. 2026-10-30

  ```chart
  {"type": "bar" | "line", "title": "제목", "unit": "건", "labels": ["2019", "2020"],
   "series": [{"name": "이름", "values": [3215, 2890]}], "source": "출처", "source_url": "https://..."}
  ```
- 글자는 브라우저가 그리므로 한·일·영 글꼴 문제 없음. 색은 사이트 변수(--chart-1, --chart-2, 다크 모드 따로).
- 막대: 항목 이름이 길면 가로 막대, 아니면 세로 막대. 선: 2px 선 + 점.
- 마우스를 올리면 값(title 툴팁), 아래에 '표로 보기'(숫자 표)가 붙는다. 시리즈가 2개면 범례.
"""
import html
import json
import re

CHART_RE = re.compile(r"^```chart\s*\n(.*?)\n```\s*$", re.S | re.M)
W, H = 480, 300
TABLE_LABEL = {"ko": "표로 보기", "ja": "表で見る", "en": "View as table"}
SOURCE_LABEL = {"ko": "출처", "ja": "出典", "en": "Source"}


def fmt(v):
    if v is None:
        return ""
    if abs(v - round(v)) < 1e-9:
        return f"{int(round(v)):,}"
    return f"{v:,.2f}".rstrip("0").rstrip(".")


def nice_step(v):
    """눈금 간격: 1·2·2.5·5 x 10^k 중 4~5칸이 되는 값"""
    import math
    if v <= 0:
        return 1
    raw = v / 4
    e = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * e:
            return m * e
    return 10 * e


def nice_max(v):
    import math
    st = nice_step(v)
    return st * math.ceil(v / st) if v > 0 else 1


def esc(s):
    return html.escape(str(s), quote=True)


def _ticks(vmax):
    st = nice_step(vmax)
    n = int(round(vmax / st))
    return [st * i for i in range(n + 1)]


def bar_svg(spec, W=W, H=H, force_h=False, cls=""):
    labels, series, unit = spec["labels"], spec["series"], spec.get("unit", "")
    vmax = nice_max(max(v for s in series for v in s["values"] if v is not None))
    horizontal = force_h or max(len(str(l)) for l in labels) > 6 or len(labels) > 8
    out = []
    if horizontal:
        left, right, top, bottom = (120 if W > 400 else 96), 64, 10, 10
        rows = len(labels)
        H = max(H if not force_h else 0, rows * len(series) * 22 + rows * 14 + top + bottom)
        band = (H - top - bottom) / rows
        bh = min(28, band * 0.7 / len(series))
        out.append(f'<svg viewBox="0 0 {W} {H}" class="chart-svg{cls}" role="img">')
        for i, l in enumerate(labels):
            y0 = top + band * i + (band - bh * len(series) - 2 * (len(series) - 1)) / 2
            out.append(f'<text class="c-lab" x="{left - 8}" y="{top + band * i + band / 2 + 4:.1f}" text-anchor="end">{esc(l)}</text>')
            for k, s in enumerate(series):
                v = s["values"][i]
                if v is None:
                    continue
                w = (W - left - right) * v / vmax
                y = y0 + k * (bh + 2)
                out.append(f'<rect class="c-s{k + 1}" x="{left}" y="{y:.1f}" width="{max(w, 1):.1f}" height="{bh:.1f}" rx="4">'
                           f'<title>{esc(l)} {esc(s.get("name", ""))}: {fmt(v)}{esc(unit)}</title></rect>')
                out.append(f'<text class="c-val" x="{left + w + 6:.1f}" y="{y + bh / 2 + 4:.1f}">{fmt(v)}{esc(unit)}</text>')
        out.append(f'<line class="c-axis" x1="{left}" x2="{left}" y1="{top}" y2="{H - bottom}"/>')
    else:
        left, right, top, bottom = 44, 8, 26, 34
        cols = len(labels)
        band = (W - left - right) / cols
        bw = min(46, band * 0.6 / len(series))
        out.append(f'<svg viewBox="0 0 {W} {H}" class="chart-svg{cls}" role="img">')
        for t in _ticks(vmax):
            y = H - bottom - (H - top - bottom) * t / vmax
            out.append(f'<line class="c-grid" x1="{left}" x2="{W - right}" y1="{y:.1f}" y2="{y:.1f}"/>'
                       f'<text class="c-tick" x="{left - 6}" y="{y + 4:.1f}" text-anchor="end">{fmt(t)}</text>')
        for i, l in enumerate(labels):
            x0 = left + band * i + (band - bw * len(series) - 2 * (len(series) - 1)) / 2
            out.append(f'<text class="c-lab" x="{left + band * i + band / 2:.1f}" y="{H - bottom + 20}" text-anchor="middle">{esc(l)}</text>')
            for k, s in enumerate(series):
                v = s["values"][i]
                if v is None:
                    continue
                h = (H - top - bottom) * v / vmax
                x = x0 + k * (bw + 2)
                y = H - bottom - h
                # 위쪽 모서리만 둥글게 (바닥은 기준선에 붙임)
                r = min(4, bw / 2, h)
                path = (f"M{x:.1f},{H - bottom} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} "
                        f"H{x + bw - r:.1f} Q{x + bw:.1f},{y:.1f} {x + bw:.1f},{y + r:.1f} V{H - bottom} Z")
                out.append(f'<path class="c-s{k + 1}" d="{path}"><title>{esc(l)} {esc(s.get("name", ""))}: {fmt(v)}{esc(unit)}</title></path>')
                if cols <= 8 and len(series) == 1:
                    out.append(f'<text class="c-val" x="{x + bw / 2:.1f}" y="{y - 6:.1f}" text-anchor="middle">{fmt(v)}</text>')
        out.append(f'<line class="c-axis" x1="{left}" x2="{W - right}" y1="{H - bottom}" y2="{H - bottom}"/>')
        if unit:
            out.append(f'<text class="c-tick" x="{left - 6}" y="{top - 10}" text-anchor="end">({esc(unit)})</text>')
    out.append("</svg>")
    return "".join(out)


def line_svg(spec, W=W, H=H, cls=""):
    labels, series, unit = spec["labels"], spec["series"], spec.get("unit", "")
    vals = [v for s in series for v in s["values"] if v is not None]
    vmax = nice_max(max(vals))
    left, right, top, bottom = 44, 60, 26, 34
    n = len(labels)
    step = (W - left - right) / max(n - 1, 1)
    out = [f'<svg viewBox="0 0 {W} {H}" class="chart-svg{cls}" role="img">']
    for t in _ticks(vmax):
        y = H - bottom - (H - top - bottom) * t / vmax
        out.append(f'<line class="c-grid" x1="{left}" x2="{W - right}" y1="{y:.1f}" y2="{y:.1f}"/>'
                   f'<text class="c-tick" x="{left - 6}" y="{y + 4:.1f}" text-anchor="end">{fmt(t)}</text>')
    every = max(1, round(n / 8))
    for i, l in enumerate(labels):
        if i % every == 0 or i == n - 1:
            out.append(f'<text class="c-lab" x="{left + step * i:.1f}" y="{H - bottom + 20}" text-anchor="middle">{esc(l)}</text>')
    for k, s in enumerate(series):
        pts = [(left + step * i, H - bottom - (H - top - bottom) * v / vmax, v, labels[i])
               for i, v in enumerate(s["values"]) if v is not None]
        d = " ".join(("M" if j == 0 else "L") + f"{x:.1f},{y:.1f}" for j, (x, y, _, _) in enumerate(pts))
        out.append(f'<path class="c-line c-l{k + 1}" d="{d}"/>')
        for x, y, v, l in pts:
            out.append(f'<circle class="c-dot c-s{k + 1}" cx="{x:.1f}" cy="{y:.1f}" r="4">'
                       f'<title>{esc(l)} {esc(s.get("name", ""))}: {fmt(v)}{esc(unit)}</title></circle>')
        if pts:   # 마지막 값만 직접 표시
            x, y, v, _ = pts[-1]
            out.append(f'<text class="c-val" x="{x + 8:.1f}" y="{y + 4:.1f}">{fmt(v)}{esc(unit)}</text>')
    out.append(f'<line class="c-axis" x1="{left}" x2="{W - right}" y1="{H - bottom}" y2="{H - bottom}"/>')
    if unit:
        out.append(f'<text class="c-tick" x="{left - 6}" y="{top - 10}" text-anchor="end">({esc(unit)})</text>')
    out.append("</svg>")
    return "".join(out)


def chart_html(spec, lang="ko"):
    series = spec["series"]
    # 넓은 화면용 + 휴대폰용(글자가 작아지지 않게 좁은 그림, 막대는 가로로) 두 장
    if spec.get("type") == "line":
        svg = line_svg(spec, cls=" c-wide") + line_svg(spec, W=360, H=260, cls=" c-narrow")
    else:
        svg = bar_svg(spec, cls=" c-wide") + bar_svg(spec, W=360, force_h=True, cls=" c-narrow")
    title = esc(spec.get("title", ""))
    legend = ""
    if len(series) > 1:
        legend = '<div class="chart-legend">' + "".join(
            f'<span><i class="sw c-s{k + 1}"></i>{esc(s.get("name", ""))}</span>' for k, s in enumerate(series)) + "</div>"
    head = "<tr><th></th>" + "".join(f"<th>{esc(s.get('name', '') or spec.get('unit', ''))}</th>" for s in series) + "</tr>"
    rows = "".join("<tr><th>" + esc(l) + "</th>" + "".join(
        f"<td>{fmt(s['values'][i])}{esc(spec.get('unit', ''))}</td>" for s in series) + "</tr>"
        for i, l in enumerate(spec["labels"]))
    src = spec.get("source", "")
    if src:
        url = spec.get("source_url", "")
        src_html = f'<a href="{esc(url)}" rel="nofollow noopener">{esc(src)}</a>' if url.startswith("http") else esc(src)
        src = f'<p class="chart-src">{SOURCE_LABEL.get(lang, "Source")}: {src_html}</p>'
    return (f'<figure class="chart"><figcaption class="chart-title">{title}</figcaption>{legend}{svg}{src}'
            f'<details class="chart-table"><summary>{TABLE_LABEL.get(lang, "View as table")}</summary>'
            f'<table><thead>{head}</thead><tbody>{rows}</tbody></table></details></figure>')


def render_charts(body, lang="ko"):
    """본문의 chart 블록을 HTML 로 바꾼다. 형식이 틀린 블록은 조용히 지운다(빈 그래프보다 낫다)."""
    def rep(m):
        try:
            spec = json.loads(m.group(1))
            assert spec["labels"] and spec["series"]
            for s in spec["series"]:
                assert len(s["values"]) == len(spec["labels"])
                s["values"] = [None if v is None else float(v) for v in s["values"]]
            return "\n\n" + chart_html(spec, lang) + "\n\n"
        except Exception as e:  # noqa: BLE001
            print(f"  [그래프 건너뜀] {type(e).__name__}: {e}")
            return ""
    return CHART_RE.sub(rep, body)
