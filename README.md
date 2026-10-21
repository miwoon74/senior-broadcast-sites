# 시니어 방송국 홈페이지

미국·일본·한국 3개 사이트를 한 번에 만드는 프로그램입니다. 기사 파일만 넣으면 홈페이지, 목록, 기사 페이지, 검색용 파일(사이트맵·RSS)이 자동으로 만들어지고, GitHub에 올리면 인터넷에 자동 게시됩니다.

| 사이트 | 코너 | 화면 구성 |
|---|---|---|
| 미국 `us` | Senior News, Past News | 신문 1면형: 큰 헤드라인 하나, 넉넉한 여백, 한 줄 흐름 |
| 일본 `jp` | シニアニュース, なつかしニュース | 정보 정리형: 색 띠 제목, 오늘의 방송표, 촘촘한 새 글 목록 |
| 한국 `kr` | 과거 뉴스 | 포털형: 대표 기사 카드, 썸네일 목록, 오른쪽 사이드바 |

세 사이트 모두 휴대폰 화면에 자동으로 맞춰지고, 휴대폰에서는 아래쪽에 큰 메뉴와 글자 크기 버튼이 나옵니다.

---

## 1. 기사 넣는 방법

기사 하나 = 파일 하나입니다. 위치와 이름 규칙만 지키면 됩니다.

```
content/<사이트>/<코너>/<날짜>-<am 또는 pm>.md

content/jp/senior/2026-10-21-am.md   ← 일본 시니어뉴스, 10월 21일 오전
content/kr/past/2026-10-21-pm.md     ← 한국 과거뉴스, 10월 21일 오후
```

파일 내용 형식:

```markdown
---
title: "기사 제목"
summary: "목록과 검색 결과에 보이는 한두 문장 요약"
youtube: dQw4w9WgXcQ
tags: 1980년대, 올림픽, 서울
---

여기부터 본문입니다. 빈 줄로 문단을 나눕니다.

## 소제목은 이렇게

- 목록은 이렇게
```

- 기사마다 어울리는 제휴 상품을 붙이려면 아래 세 줄을 넣습니다. 기사 본문 바로 아래 "이 기사와 함께 보면 좋은 상품" 칸에 나옵니다.
  ```
  product_name: "상품 이름"
  product_url: https://제휴링크
  product_note: "한 줄 설명"
  ```
- `youtube`에는 유튜브 주소 `watch?v=` 뒤의 영상 ID만 넣습니다. 넣으면 영상 썸네일과 재생 버튼이 자동으로 붙습니다.
- 지금 들어 있는 기사는 모두 `sample: true`인 예시입니다. 예시 기사는 검색에 노출되지 않습니다. 실제 기사가 들어오면 예시 파일은 지워 주세요.

## 2. 내 컴퓨터에서 확인하기

```bash
pip install -r requirements.txt
python build.py              # public/ 폴더에 사이트 생성
```

`public/index.html`을 브라우저로 열면 바로 볼 수 있습니다.
`python build.py --preview`를 실행하면 모든 페이지를 한 파일로 모은 `preview.html`이 만들어집니다.

## 3. 인터넷에 올리기 (GitHub Pages, 무료)

1. GitHub에서 새 저장소를 만듭니다. 예: `senior-broadcast-sites`
2. 이 폴더 전체를 그 저장소에 올립니다.
3. 저장소 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 바꿉니다.
4. 몇 분 뒤 `https://<내 아이디>.github.io/senior-broadcast-sites/` 에서 사이트가 열립니다.

이후로는 기사 파일을 올릴 때마다 자동으로 다시 만들어져 게시됩니다.

## 4. 사이트 설정 (`sites.json`)

| 항목 | 할 일 |
|---|---|
| `base_url` | 사이트 주소를 넣습니다. 예: `https://아이디.github.io/senior-broadcast-sites` 이게 있어야 검색 주소·사이트맵·공유 링크가 완성됩니다. |
| `show_placeholders` | 광고·영상 자리 표시(점선 상자). 실제 운영 전에 `false`로 바꿉니다. |
| `name`, `tagline`, `description` | 사이트 이름과 소개 문구 |
| `contact_email` | 소개·개인정보 페이지의 문의 메일 (애드센스 심사에 필요) |
| `seo` | 구글 서치 콘솔, 빙, 네이버 서치어드바이저에서 받은 확인 코드 |
| `ads` | 애드센스 승인 후 받은 `ca-pub-...` 번호와 광고 단위 번호 |
| `affiliate.items` | 제휴 상품. `{"title": "상품명", "url": "제휴 링크", "note": "한 줄 설명"}` |
| `share` | 공유 버튼 종류 (`line`, `naver`, `facebook`, `x`, `copy`) |

## 5. 검색 등록 (SEO)

자동으로 들어가는 것: 페이지별 제목·설명, 검색 주소(canonical), SNS 미리보기(OG), 뉴스 기사 구조 데이터(JSON-LD), 사이트별 `sitemap.xml`, 코너별 `feed.xml`(RSS), `robots.txt`.

직접 해야 하는 등록:
- **미국·일본**: Google Search Console, Bing Webmaster Tools에 사이트 등록 → `사이트/sitemap.xml` 제출 (일본 Yahoo! 검색은 구글 결과를 씁니다)
- **한국**: 네이버 서치어드바이저에 사이트 등록 → 사이트맵과 RSS(`kr/past/feed.xml`) 제출

> 참고: 나라별 사이트를 검색에서 더 강하게 만들려면 나중에 개인 도메인(예: `seniorbroadcast.jp`)을 연결하는 것이 좋습니다. 애드센스 승인에도 유리합니다.

## 6. 광고 표기 규정

각 사이트의 제휴 상품 영역에는 나라별 규정에 맞는 표기가 이미 들어 있습니다.
- 미국: FTC 제휴 링크 공개 문구
- 일본: 스텔스마케팅 규제(2023년 10월 시행)에 따른 【PR】 표기
- 한국: 공정위 추천·보증 심사지침에 따른 경제적 대가 표시

## 7. 방송국 프로그램과 연결 (다음 단계)

방송국 프로그램이 기사를 만들 때마다 1번 형식의 파일을 `content/` 폴더에 저장하고 GitHub에 올리기(push)만 하면 됩니다. 이 연결 스크립트는 방송국 프로그램 구조를 확인한 뒤 만들 예정입니다.

## 폴더 구조

```
build.py            사이트 생성 프로그램
sites.json          사이트 설정
content/            기사와 소개·개인정보 페이지
templates/          화면 구성 (나라별 홈: home_us / home_jp / home_kr)
static/             디자인(style.css)과 동작(site.js)
.github/workflows/  GitHub 자동 게시 설정
```
