# 시니어 방송국 홈페이지 — 작업 기록

사용자와 함께 정한 내용을 모아 둔 문서입니다. 작업 전에 이 문서를 먼저 읽고, 새로 정한 것이 있으면 여기에 덧붙입니다.

## 일하는 방식
- 사용자는 초보 프로그래머입니다. 답은 **한국어**로, 쉽게 설명합니다.
- 사이트 수정, GitHub 올리기, 연결 스크립트 작성은 **Claude가 직접** 합니다. 사용자에게 파일을 고치라고 넘기지 않습니다.
- 사용자가 직접 해야 하는 일은 계정·설정처럼 Claude가 할 수 없는 것만 안내합니다 (예: GitHub Pages 켜기, 애드센스 가입, 도메인 구매).

## 전체 구조
- 저장소: `miwoon74/senior-broadcast-sites` (Public). `main`에 올리면 GitHub Actions가 사이트를 만들어 GitHub Pages에 게시.
- **도메인 (2026-10-29 구매, Cloudflare): 브랜드마다 따로** — `seniornewsbureau.com`(snb) · `todayspastnews.com`(tm) · `grandmawellnessrecipes.com`(gw). 주소 = 도메인/나라/ (예: grandmawellnessrecipes.com/kr/).
- 게시: Cloudflare Pages 프로젝트 3개(같은 이름)가 이 저장소 `main`을 보고 `python build.py --property=<브랜드>`로 각각 만듦. GitHub Pages(miwoon74.github.io/senior-broadcast-sites/)는 새 도메인으로 보내는 안내 페이지만(`tools/make_redirects.py`) — 같은 글이 두 주소에 있으면 검색에 불리.
- Cloudflare 키: 사용자 PC Windows 자격 증명 `SeniorNewsAutomation/CLOUDFLARE_API_TOKEN` (영역 DNS 편집 + Pages 편집). 설정 스크립트 `C:\Users\user\ControlTower\tools\cf_setup.py`, 상태 `cf_status.py`.
- 사이트끼리 이동: 모든 사이트 위 띠·아래 카드에 같은 언어의 다른 브랜드 링크("함께 운영하는 사이트").
- 생성기: `build.py` (Python + Jinja2 + Markdown). 설정은 `sites.json`, 기사는 `content/<사이트>/<코너>/`.

## 사이트별 결정 (2026-10-21 두 브랜드로 분리)
브랜드가 둘 → 도메인도 둘로 나눌 예정 (사용자 확인).

| 브랜드 | 사이트 | 이름 / 로고 | 코너 |
|---|---|---|---|
| ① SNB `snb` | 미국 `snb/us` | Senior News Bureau, SNB 로고 | 시니어 뉴스만, 신문 1면형, 헤더 노부부 사진(CC BY 2.0) |
| ① SNB | 일본 `snb/jp` | シニア放送局 (시니어 방송국 유지), SNB 로고 + 일본어 이름 | シニアニュース만, 정보 정리형, 헤더 1985년 노부부 사진(CC BY 4.0) |
| ② 타임머신 `tm` | 한국 `tm/kr` | 오늘의 과거 뉴스 | 과거 뉴스 |
| ② 타임머신 | 미국 `tm/us` | Today's Past News | Past News |
| ② 타임머신 | 일본 `tm/jp` | 今日のなつかしニュース | なつかしニュース |
| ③ 할머니 `gw` | 한국·일본·미국 `gw/kr` `gw/jp` `gw/us` | 할머니 건강레시피 / おばあちゃんの健康レシピ / Grandma Wellness Recipes | 레시피 (하루 1편) |

- 타임머신 3개 사이트는 같은 화면 구성(`home_tm.html`): 타임머신 헤더 → 오전 편성 → 오후 편성 → 지난 방송 필름 → 목록. 흑백TV 로고(화면 ◀◀, 특정 연도 없음), 나라별 글자판 로고 `static/tm-logo-<ko|en|ja>-<light|dark>.png`.
- 기사 폴더: `content/<브랜드>/<나라>/<코너>/`. 예전 주소 `/us/ /jp/ /kr/`는 새 주소로 자동 이동.
- `python build.py --property=snb` 또는 `--property=tm`으로 브랜드 하나만 만들 수 있음(도메인별 배포용). 도메인을 사면 각 브랜드를 따로 배포(Cloudflare Pages 2개 또는 저장소 분리 중 그때 결정).
- 일본 연호(昭和45年 등)는 서기로 자동 변환해 연도 표시.
- 예시 기사는 모두 범위(1970–2006) 안의 사건으로 교체. 범위 밖 사진(1969 여의도, 아폴로, 비틀스, 신칸센)은 제거.

## SNB 시니어 뉴스 영상 (2026-10-21)
- 미국·일본 시니어 뉴스 방송 영상은 매일 유튜브에 올라감. 2026-09-01 방송분부터 유튜브에도 쌓을 예정.
- 사이트 연결: 기사 파일의 `youtube: 영상ID` → 기사에 영상(눌러서 재생), 목록 썸네일·SNS 미리보기 이미지로 영상 썸네일 사용, 구글 영상 검색용 VideoObject 정보 자동 추가.
- `sites.json`의 `youtube_channel`에 채널 주소를 넣으면 사이트 아래쪽에 유튜브 채널 링크 표시 (채널 주소 받으면 Claude가 입력).
- 연결 스크립트에서 정할 것: 기사와 영상 ID를 짝짓는 방법(방송국 프로그램이 업로드 후 영상 ID를 기록하는지, 채널에서 날짜·오전/오후로 찾아오는지), 유튜브 설명란에 사이트 기사 주소 넣기(유튜브 → 사이트 → 상품 흐름).

## 오늘의 과거 뉴스 (타임머신) 규칙
- **2026-11-05 사용자 결정: 하루 6편·회차 1개** (나라마다). 아래 "하루 12개, 오전 6·오후 6"은 옛 규칙.
- **원고 기준(2026-11-05 사용자 승인)**: 그때를 추억하게 만드는 뉴스. ① 첫머리 "N年前の今日、YYYY年M月D日。"+사건 한 문장 ② 그 시절: 왜 특별했나·왜 열광했나(핵심 하나, 기록은 그 이유를 받침) ③ 이날: 무슨 일이 있었나, 궁금증이 커지게 ④ 지금: "今も" 지금까지 남은 것, 사실로 끝맺음. 아라비아 숫자, "その日" 금지, 지어낸 장면·시키는 말("胸に刻んで") 금지, 백과사전식 나열 금지. 극적인 부분은 자료 속 실제 이야기로(예: 왕정치-아라카와 첫 만남).
- **원고 작성자 = Claude 예약 작업**(사전 제작, 맥스 요금제 안). 무료 GPT-OSS는 기준을 못 따라 원고용으로 쓰지 않음. 원고는 영상 만들기 전에 사용자에게 먼저 보여 줌.
- **2026-11-05 자동화 설계**: 엔진이 자료 준비 후 `CLAUDE_TM_WRITE.json`에 올리고 대기 → Claude 예약 작업(03:37·15:37, PC `config\CLAUDE_TM_WRITER.md`)이 원고(**약 2분**, JP 560~640자)+사이트 글(`NN_blog.json`, JP 1,600~2,200자)을 씀 → 엔진이 음성·사진·영상·블로그. 방송 전날까지 없으면 엔진 AI. 예약 작업은 주간 한도 때문에 아직 꺼 둠(다음 대화에서 시험 확인 후 켬). 자세한 것·남은 일은 PC `ControlTower\AI_ROLES.md` 2026-11-05 16:00 항목.
- 선정: 연대를 억지로 채우지 않고 사건 크기 기준. 후보 출처(위키·위키데이터·'오늘은 무슨 날' 달력 5곳)가 빠지면 고르지 않음.
- **오늘로부터 56년 전 ~ 20년 전**의 같은 날짜 뉴스. 2026년 = 1970–2006, 2027년 = 1971–2007. 연도는 `sites.json`의 `years_back: [56, 20]`로 매번 자동 계산 (`{from}`, `{to}`).
- 하루 12개: **오전 6개, 오후 6개**. 파일 이름 `YYYY-MM-DD-am-01.md` … `am-06`, `pm-01` … `pm-06`.
- 기사 사진은 방송국에서 **검수를 거친 상업 사용 가능 사진**으로 들어옴 → 그대로 사용.
- 헤더 배경 = 지금 방송(오후가 있으면 오후)에서 사진이 있는 첫 기사. 타임머신 숫자는 그 방송 첫 기사의 연도까지 거꾸로 돈다.
- 지금 들어 있는 12개는 화면 확인용 예시(`sample: true`, 검색 제외). 실제 그날 뉴스가 아님.

## ③ 할머니 건강레시피 `gw` (2026-10-29 추가)
- 사이트 3개: `gw/kr` 할머니 건강레시피 · `gw/jp` おばあちゃんの健康レシピ · `gw/us` Grandma Wellness Recipes (유튜브 채널 이름과 같음). 로고·파비콘 = 유튜브 채널 프로필 그림(`static/gw-icon-<ko|ja|en>.png`).
- 화면(`home_gw.html`, `layout-gw`): 오늘의 레시피 카드(영상 + 제목 + 요약 + 레시피 보기) → 지난 레시피 목록, 옆에 추천 재료·광고. 색은 부엌의 녹색·주황.
- 코너 `recipe`, 하루 1편: `content/gw/<나라>/recipe/YYYY-MM-DD-am.md`.
- 사용자 결정(2026-10-29): 영상(쇼츠)은 이야기·전해 내려온 효능을 말하고 만드는 법은 캡션으로만 → **자세한 레시피는 사이트에서**. 유튜브 설명란·고정 댓글에 사이트 글 주소를 넣어 방문을 유도(쇼츠 화면에는 외부 링크 버튼을 넣을 수 없음).
- 2026-10-30 확인: **쇼츠는 설명란·댓글 링크가 눌리지 않음**(유튜브 고객센터). 눌리는 길 = 채널 프로필 링크·관련 영상. → 8개 채널 프로필에 각 브랜드 사이트 링크를 걸어 둠(할머니 "자세한 레시피", 과거·시니어 "기사 전문"). 영상 마지막 대사 = "자세한 레시피는 채널 프로필 링크에서".
- 영상은 레시피를 간단히(몇 인분 + 주재료), **사이트 글은 상세히**(모든 분량·단계·준비법·옛 책·연구·출처) — 사용자 결정 2026-10-30.
- 자동 게시: PC `YouTubePublisher\publisher\site_publish.py` — 업로드 승인(UPLOAD_APPROVED.json)된 회차의 blog_*.md 를 GitHub API 로 `content/gw/<나라>/recipe/<날짜>-am.md` 에 올림(prepare·upload 때 실행, 올라간 뒤 영상 ID 도 붙임). 키: Windows 자격 증명 `SeniorNewsAutomation/GITHUB_SITE_TOKEN`(이 저장소만, Contents 읽기·쓰기, 사용자가 `ControlTower\SAVE_GITHUB_KEY.cmd`로 저장). 유튜브 설명란에는 그 글 주소, 글이 아직 없으면 올리기 직전 사이트 첫 화면 주소로 자동 교체.
- 가져오기 도구: `tools/import_grandma.py <GrandmaWisdom\OUTPUT\REVIEW> [--preview] [--days=…] [--outbox=<YouTubePublisher\outbox>]` — 회차 폴더의 `blog_ko/ja/en.md`를 기사로 변환. 업로드 승인(UPLOAD_APPROVED.json)된 언어만 넣고, `--preview`면 검수 대기 표시(검색·RSS 제외). 미리보기는 저장소에 올리지 않음.

## 광고·제휴 자리
- 홈: 오전 편성 끝 / 오후 편성 끝마다 광고(`slot_top`, `slot_bottom`) + 추천 상품.
- 기사 페이지: 본문 바로 아래 **기사별 상품**(`product_name`, `product_url`, `product_note` — 연결 스크립트가 넣음) → 광고 → 공유 → 사이트 공통 추천 상품 → 사이드 광고.
- 나라별 광고 표기 문구 포함 (미국 FTC, 일본 【PR】, 한국 공정위).
- 운영 시작 전 `sites.json`의 `show_placeholders`를 `false`로 바꿔 점선 자리 표시를 끈다.

### 기사별 상품 추천 (결정, 2026-10-21)
- 사용자 결정: 기사를 확인하고 어울리는 상품을 골라 자연스럽게 유도. 어려우면 기본 상품을 넣어도 됨.
- 도구: `tools/pick_products.py` — Claude(Haiku)가 기사를 읽고 ① 상품을 붙일지(사고·참사·사망 등은 건너뜀) ② 검색어·상품 이름 ③ 한 줄 유도 문구를 정해 기사 파일에 `product_*` 필드로 기록. 방송국 연결 스크립트가 기사를 넣은 뒤 이 도구를 실행.
- AI 키가 없으면: 무거운 단어가 있는 기사는 건너뛰고, 나머지는 사이트별 기본 추천 상품(`affiliate_program.default_product`).
- 나라별 제휴 프로그램: 미국 Amazon.com, 일본 Amazon.co.jp, 한국 쿠팡 파트너스. 각 프로그램의 필수 고지 문구는 `affiliate_program.disclosure`.
- 링크가 없으면 상품 칸은 "제휴 링크 연결 대기"로 표시(자리 표시 켜진 동안만). 사용자가 제휴 프로그램에 가입하면 Amazon tag, 쿠팡 키를 받아 Claude가 설정.
- 예시 기사 3개(1980 컬러TV, 1982 프로야구, 1993 엑스포)에 고른 결과를 넣어 둠.

## 사진 규칙
- 실제 사진만, AI 그림은 피함. 퍼블릭 도메인이나 상업 사용 가능한 라이선스만 사용, 출처 표시.
- 과거뉴스 영상 사진 찾기(2026-11-05 하나로 정리): PC `HistoricalNews_1970\hn1970\shot_pool.py` 만 사용(사건 나라 기준 모든 출처 동시 검색 → 격자 확인 → 장면 배치, 빈 장면만 삽화). 일본 지역 기록관(adeac.jp)은 한국에서 막혀 Cloudflare 중계 `tm-image-relay`로 받음. 자세한 규칙은 PC `ControlTower\AI_ROLES.md` 2026-11-05 항목.
- 예외(2026-11-04 사용자 결정): **과거뉴스만** 쓸 수 있는 사진이 부족한 이야기에 AI 삽화(그 시절 신문 삽화풍, "AI 재현 일러스트" 표시) 허용. 공인은 공적 장면만, 사고·사건 피해자 얼굴 없음, 로고는 배경에 작게, 특정 사진 따라 그리기 금지(사진을 AI에 넣지 않음). 사이트 글에 들어갈 때도 같은 표시 유지.
- 지금 쓰는 사진 출처: 위키미디어 공용 (미 공군 1988 서울올림픽, 1971 광화문, CC BY 노부부 사진 2장).

## 9월분 기사 넣기 판단 (2026-10-22)
- 과거 날짜로 넣어도 구글은 실제 게시일 기준 → "운영 기간"이 늘어나는 효과는 없음. 메리트는 기사 양·내용.
- 오늘의 과거 뉴스: 적극 추천. 날짜별 기사는 매년 같은 날 다시 검색됨(날짜 사전이 핵심 자산). 나중에 나머지 날짜도 채우면 좋음.
- SNB 시니어 뉴스: 추천하되 선별. 유튜브 영상(9월부터 쌓임)과 짝이 되는 페이지, 기사 양에 도움. 시기가 지난 소식(기한·이번 주 변경 등)은 연결 스크립트에서 AI가 골라내 제외하거나 "○월 ○일 기준 정보" 안내를 붙임.

## 일정 (2026-10-21 정리, 라이브 날짜는 미정)
사용자 계획: 2026-09-01 방송분부터 기사를 쌓다가, 라이브 직전에 도메인·제휴 등을 준비. 제휴 링크(쿠팡·Amazon)는 라이브 직전에 넣음.
Claude 제안: 도메인만은 기사 쌓기 시작 시점으로 앞당기기 (검색 이력·애드센스 심사에 유리, 주소 이전 손실 방지). 사용자 결정 대기.
2026-10-21 갱신: 사용자가 지난 기사(9월 1일~) 한 달치를 2~3일 안에 넣을 수 있다고 함 → 도메인은 몰아넣기 전에 바로 구매 권장(.com 하나, /us /jp /kr). 애드센스는 몰아넣은 뒤 2~3주 매일 업데이트가 이어진 다음 신청. 기사 전달 방법(폴더 연결 또는 zip 업로드)은 사용자 답변 대기.

1. 지금 ~ 방송국 프로그램 완성: 사이트 틀 완료. 대기.
2. 방송국 연결 (경로 받으면 바로): 연결 스크립트 작성 → 2026-09-01부터 쌓인 방송분 한꺼번에 가져오기 → 이후 매일 자동. 예시 기사 삭제. 상품은 "고르기만"(링크 없이) 미리 실행.
3. 기사 쌓기 기간: (제안) 도메인 구매·연결 → 구글 서치콘솔·네이버 서치어드바이저 등록, 사이트맵 제출 → 점선 자리 표시 끄기. 기사 품질 점검.
   - 애드센스: 도메인 연결 후 기사가 약 한 달(하루 12개 기준) 쌓이면 바로 신청 (기한 조건이 없고, 거절 시 재신청 시간이 필요하므로 라이브 전으로 앞당김). 신청 전 연락처 메일을 실제 주소로 교체(사용자에게 받기), 기사 품질 점검.
4. 라이브 2~4주 전: 쿠팡 파트너스 가입, Amazon.co.jp 어소시에이트 신청(사이트 심사 있음).
5. 라이브 직전: Amazon.com 어소시에이트 가입(가입 후 180일 안에 판매 3건 조건이 있어 마지막에). 받은 tag·키로 Claude가 링크 연결, 광고 번호 입력.
6. 라이브 후: 클릭·수익 확인하며 상품 추천 개선, 한국어 시니어뉴스 추가 여부 결정.

## 방송국(타임머신) 인계 (2026-10-22)
- 최종 인계 문서: `C:\Users\user\HistoricalNews_1970\reports\TIME_MACHINE_CLAUDE_MANUAL_IMPORT_20260901.md` (사용자 PC, 이 문서만 보면 됨)
- 기본 폴더: `C:\Users\user\HistoricalNews_1970\data\timemachine`
- 9월 1일분: 한국·일본·미국 블로그 각 12편, 사진 관련 JSON·Markdown 국가별 12편 생성 완료. **공개 게시 승인 전(검수 대기)** → 승인 전에는 사이트에 공개하지 않음.
- 운영 규칙: 라이브 전 국가별 12편씩 수동 픽업 / 라이브 후 오전 6·오후 6 각각 수동 픽업 / 사진은 실제 파일이 있고 사용 승인된 경우만 / 업로드는 파일 준비 확인 후 수동 진행.
- 2026-10-22: PC 연결됨 → Claude가 PC 폴더에서 직접 파일을 가져옴.

### 수동 픽업 도구 (2026-10-22)
- `tools/import_timemachine.py <날짜 폴더> [--preview] [--slot=am|pm|all]` — 목록 JSON(`CLAUDE_SITE_MANUAL_IMPORT_*.json`) 기준으로 `NN_website_illustrated.md` + `NN_visuals.json`을 `content/tm/<kr|jp|us>/past/YYYY-MM-DD-am|pm-NN.md`로 변환.
- 안전장치: 파일 하나라도 없으면 중단 / 공개 승인(`publication_ready`·`publication_approval`) 전이면 `--preview` 없이는 중단 / 같은 `source_id` 중복 등록 안 함 / 사진은 파일이 있고 `publish_ready=true`인 것만(대체 없음), 실제 사진·AI 삽화 캡션 구분 / "공개 보류" 표시 줄 제거 / 출처 URL을 "참고 자료"로 붙임.
- `--preview`로 넣은 원고는 `review:` 표시 → 기사 위 "검수 대기" 문구, 검색 제외(noindex), RSS 제외.
- 기사 파일 `year:` 필드 추가(제목에 연도가 없어도 타임머신 숫자·연도 표시).
- **미리보기는 저장소에 올리지 않음** (main에 올리면 바로 공개됨). 비공개 Claude 페이지로만 보여 줌.
- 2026-09-01분 미리보기 완료(36편). 사진 사용 가능 1장(미국 오전 1). 한국 06 사진(1973 지하철 공사 시찰)은 publish_ready=false라 제외. 검수 경고 붙은 원고 다수 → 사용자 검수·승인 대기.

## 남은 일
1. **방송국 프로그램 연결** — 사용자 프로그램이 아직 미완성(2026-10-21). 완성되면 사용자가 폴더 경로를 알려줌 → Claude가 기사·사진·기사별 상품을 위 형식으로 `content/`에 넣고 GitHub에 올리는 스크립트를 작성.
   - 그때 확인할 것: 기사 저장 형식, 사진 위치와 라이선스 정보 위치, 미국·일본 과거 뉴스도 하루 12개인지.
2. ~~도메인 구매 및 연결~~ — 완료(2026-10-30): 세 도메인 모두 Cloudflare Pages로 공개, www 포함, 예전 github.io 주소는 새 도메인으로 이동 확인.
   - 구글 서치콘솔 완료(2026-11-03): 세 도메인 '도메인 속성'으로 소유 확인(Cloudflare TXT, `ControlTower\tools\cf_verify_txt.py` — TXT 지우면 확인 풀림), 사이트맵 8개 제출(snb us·jp / tm kr·us·jp / gw kr·jp·us, 모두 '성공').
   - 네이버 서치어드바이저(2026-11-03): Claude 브라우저에서는 열 수 없음(안전 제한) → 사용자가 사이트 3개 등록, 'HTML 태그' 값을 받아 `sites.json` properties[].naver_site_verification 에 넣음(첫 화면 root.html 메타 태그, 세 도메인 실제 반영 확인) → 사용자가 소유확인·사이트맵 제출(나라별 전체 주소 https://<도메인>/<kr|jp|us>/sitemap.xml) — 2026-11-03 사용자 완료.
   - IndexNow(2026-11-04): 열쇠 `sites.json indexnow_key` → 빌드 때 각 도메인 맨 위에 `<열쇠>.txt`. `.github/workflows/indexnow.yml` 이 content/ 에 글이 올라오면 `tools/indexnow.py` 로 새 글·첫 화면·목록·사이트맵 주소를 Bing·네이버·Yandex 등에 바로 알림(예시·검수 대기 글 제외, Cloudflare 게시 확인 뒤 보냄).
   - Bing 웹마스터 도구(2026-11-04 완료): 사용자가 로그인·구글 허락 → 서치콘솔에서 세 도메인 가져옴, 사이트맵 8개 Claude가 제출. IndexNow 첫 전송(할머니 30주소) 202 받음.
   - 일본 야후 = 구글 검색 엔진 사용 → 서치콘솔로 충분. 라쿠텐은 검색이 아니라 일본 제휴(楽天アフィリエイト) 후보.
   - SNS 미리보기 그림: 사진 없는 글은 사이트 헤더 사진 → 없으면 사이트 아이콘(전에는 깨진 주소였음).
3. 제휴 프로그램 가입(사용자 명의: Amazon 어소시에이트 미국·일본, 쿠팡 파트너스) → 받은 tag·키를 Claude가 설정
4. 애드센스 신청 → `ads` 번호 입력, 구글 서치콘솔·네이버 서치어드바이저 등록.
5. 한국어 시니어뉴스 추가 여부 결정.

## 사이트 글 자동 게시 — 세 브랜드 (2026-10-30)
- 사용자 결정: 시니어·과거뉴스도 블로그 원고가 있다 → 과거뉴스는 처음 방식(website 원고+사진)을 살리고, 시니어는 **공식 통계·그래프로 자세하고 충실하게**.
- 게시 도구(PC): `YouTubePublisher\publisher\site_publish.py` v2 — 업로드 승인(UPLOAD_APPROVED.json)된 회차만, 바뀐 파일을 모아 **커밋 1개**로 main 에 올림(Git Data API). 영상이 올라가면 영상 ID를 넣어 다시 올림. `--dry-run --all` 은 시험(올리지 않음).
  - 할머니: `content/gw/<kr|jp|us>/recipe/<날짜>-am.md`
  - 과거뉴스: `content/tm/<kr|jp|us>/past/<날짜>-<am|pm>-NN.md` + `images/`. 원고 = HistoricalNews `hn1970/tm_blog.py`(daily_pipeline 의 blog 단계, AI 없음): 보정 원고 4단 + 방송과 같은 자동 검수 통과 사진(사건 당시 사진 아니면 캡션에 표시) + 자체 그래픽(지도·숫자) + 추억 기사만 '그때 vs 지금' 물가표(출처 포함) + 그날 다른 신문 제목 + 참고 자료. **보정 안 된 엔진 초안은 올리지 않음.** 제목은 Claude 보정 때 `blog_title`.
  - 시니어: `content/snb/<jp|us>/senior/<날짜>-<am|pm>-NN.md`. 원고 = `LOCAL_BRIEF\<JP|WEST>\<YYYYMMDD>\<SLOT>\BLOG_FINAL\ARTICLE_NN.md` — 엔진 `snb_blog_final.py`(2026-10-30 확정): 방송 원고(Gemini + 구글 검색으로 쓴 사실·숫자·출처)를 Gemini가 넓혀 씀(따로 검색 안 함, 원고에 없는 숫자 금지, 그래프 숫자도 원고와 대조) → Groq gpt-oss가 검수 헌법 기준으로 검사(원고와 일치한 숫자는 손대지 못함). 기준 `LOCAL_BRIEF\BLOG_FINAL_GUIDE.md`. 사진 = 블로그 꾸러미의 Pexels 사진(“イメージ写真” 표시).
- 그래프: 기사 본문에 ```chart {json}``` 블록 → `tools/charts.py` 가 SVG로(넓은 화면 세로 막대 / 휴대폰은 가로 막대, 다크 모드 색 따로, '표로 보기' 포함). 색 --chart-1/--chart-2 (검증 통과).

## 시청자 유도 흐름 (2026-11-01 사용자 결정 "추천대로")
- 설계 문서: Claude 문서 「시청자 유도 흐름 설계 (세 방송국)」(9절 GPT 보완 반영, 10절 실행 순서).
- 결정: 엑스는 **일본어 계정 1개로 먼저**(일본이 인구 대비 엑스 이용률 최고) → 성과 보고 영어 추가. 엑스 한 달 시험 **한다**(월 약 80달러 상한, 방문 1명당 0.5달러 넘으면 2주 만에 중단). 첫 시험 = 일본 과거뉴스 완결형 맛보기 + 일본 시니어뉴스 숫자 1개 맛보기. 받아보기(LINE부터, 주 2~3회)는 2~3주 뒤.
- 페이스북 페이지(2026-11-04 사용자 생성): Senior News Bureau https://www.facebook.com/seniornewsbureau (방송 및 미디어 회사, 웹사이트 seniornewsbureau.com/us/). `sites.json` snb/us `facebook_page` → 아래쪽 Facebook 링크. 인스타그램 비즈니스 계정 연결·자동 게시(Meta 앱)는 다음 단계. 프로필·커버 그림 PC `Downloads\SNB_facebook`.
- 인스타그램(2026-11-04): **@seniornewsbureau** (snbheadquater@gmail.com, 비즈니스 계정, 페이스북 페이지에 연결). `sites.json` snb/us `instagram` → 아래쪽 Instagram 링크.
- Meta 자동 게시 연결(2026-11-04 완료): Meta 앱 「SNB Social Publisher」(id 1605837300708384, 권한 pages_manage_posts·pages_read_engagement·pages_show_list·business_management·instagram_basic·instagram_content_publish). 페이지 토큰은 PC Windows 자격 증명 `SeniorNewsAutomation/META_PAGE_TOKEN_SNB_US`, 페이지·인스타 ID는 `ControlTower\config\meta_pages.json`. 연결 도구 `ControlTower\tools\meta_connect.py`(값은 사용자가 창에 직접 붙여 넣음). 다음: 게시 스크립트(사용자 승인 후 게시, 첫 글은 미리보기).
- 나머지 SNS(2026-11-04 사용자 결정): 사이트 1개 = 페이스북 페이지 1개 + 인스타 1개(인스타 자동 게시는 페이지 연결 필수). 남은 7세트(snb/jp, tm kr·jp·us, gw kr·jp·us)는 **사용자가 시간 날 때** 만듦 → 말하면 Claude가 그때 프로필·커버 그림을 만들고 안내, `meta_connect.py <사이트> "<페이지 이름>"`으로 연결. 새 계정은 하루 1~2개 게시로 시작.
- 일본 시니어 SNS(2026-11-04): 페이스북 페이지 **シニア放送局** (페이지 id 1461963686999930, 주소 facebook.com/profile.php?id=61595950992970, 카테고리 방송 및 미디어 회사, 「詳しくはこちら」 버튼 → seniornewsbureau.com/jp/, 그림 PC `Downloads\SNB_facebook_jp`) ↔ 인스타 **@seniornewsbureau_jp** (가입 메일 snbheadquater+jp@gmail.com) 연결 확인. 미국 연결 그대로. 자동 게시 열쇠 저장 완료(`SeniorNewsAutomation/META_PAGE_TOKEN_SNB_JP`, meta_pages.json snb_jp, 인스타 id 17841471861229119). sites.json snb/jp 에 facebook_page·instagram 링크. 주의: Claude 앱 브라우저에 로그인된 인스타 계정을 페이스북이 가져가므로, 새 인스타 연결 전 그 브라우저 인스타를 새 계정으로 로그인해 둘 것(로그인 창은 사용자가 직접 눌러야 열림).
- 일본 과거뉴스 SNS(2026-11-04): 페이스북 페이지 **今日のなつかしニュース** (주소 facebook.com/profile.php?id=61595917694630, 카테고리 TV 방송사, 「더 알아보기」 버튼 → todayspastnews.com/jp/, 그림 PC `Downloads\TM_facebook_jp`). ↔ 인스타 **@todayspastnews_jp** (가입 메일 snbheadquater+tmjp@gmail.com, 비즈니스 계정·TV 방송사, 연결 확인). sites.json tm/jp `facebook_page`·`instagram`. 자동 게시 열쇠 저장 완료(`SeniorNewsAutomation/META_PAGE_TOKEN_TM_JP`, meta_pages.json tm_jp, 페이지 id 1337606066114035, 인스타 id 17841431330945466). 2026-11-05 Meta 앱 권한을 '모든 현재 및 향후 페이지·비즈니스·인스타'로 바꿈 → 앞으로 만드는 페이지는 탐색기 설정 수정 없이 열쇠만 받으면 됨. 인스타 프로필 사진·소개 글은 Claude가 웹에서 넣음(링크 칸은 휴대폰 앱에서만 → 사용자가 넣음).
- 미국 과거뉴스 SNS(2026-11-05): 페이스북 페이지 **Today's Past News** (주소 facebook.com/profile.php?id=61596370224932, 카테고리 TV 방송사, 「더 알아보기」 버튼 → todayspastnews.com/us/, 그림 PC `Downloads\TM_facebook_us`). ↔ 인스타 **@todayspastnews_us** (가입 메일 snbheadquater+tmus@gmail.com, 비즈니스 계정·TV 방송사, 연결 확인). sites.json tm/us `facebook_page`·`instagram`. 자동 게시 열쇠 저장 완료(`SeniorNewsAutomation/META_PAGE_TOKEN_TM_US`, meta_pages.json tm_us, 페이지 id 1363492880188494, 인스타 id 17841472471951302). 인스타 프로필 링크 칸은 휴대폰 앱에서 사용자가 넣음.
- 한국 과거뉴스 SNS(2026-11-11): 페이스북 페이지 **오늘의 과거 뉴스** (facebook.com/profile.php?id=61596578845363, TV 방송사, 「더 알아보기」→ todayspastnews.com/kr/, 그림 노예2 ControlTower\SNS_SETUP·jeff Downloads\SNS_SETUP) ↔ 인스타 **@todayspastnews_kr** (snbheadquater+tmkr@gmail.com, 비즈니스·TV 방송사, 연결 확인). sites.json tm/kr facebook_page·instagram. 작업은 jeff 크롬 + Claude in Chrome 확장으로 함(노예2 앱 브라우저는 페이스북 로그인 없음). 자동 게시 열쇠 저장 완료(META_PAGE_TOKEN_TM_KR, 페이지 id 1342234105649743).
- 한국 할머니 SNS(2026-11-11): 페이스북 페이지 **할머니 건강레시피** (facebook.com/profile.php?id=61596066857745, 「더 알아보기」→ grandmawellnessrecipes.com/kr/, 그림 SNS_SETUP GW_KR_*) ↔ 인스타 **@grandmarecipes_kr** (snbheadquater+gwkr@gmail.com, 비즈니스·음식 및 음료, 연결 확인). sites.json gw/kr facebook_page·instagram. 자동 게시 열쇠 저장 완료(META_PAGE_TOKEN_GW_KR, 페이지 id 1422304997636706).
- 일본 할머니 SNS(2026-11-11): 페이스북 페이지 **おばあちゃんの健康レシピ** (facebook.com/profile.php?id=61596247989237, 주방/요리, 「더 알아보기」→ grandmawellnessrecipes.com/jp/, 그림 SNS_SETUP GW_JP_*) ↔ 인스타 **@grandmawellness_jp** (snbheadquater+gwjp@gmail.com, 비즈니스·음식 및 음료, 연결 확인). sites.json gw/jp. 자동 게시 열쇠 저장 완료(META_PAGE_TOKEN_GW_JP, 페이지 id 1374215745783330).
- 미국 할머니 SNS(2026-11-11): 페이스북 페이지 **Grandma Wellness Recipes** (facebook.com/profile.php?id=61596086476950, 주방/요리, 「더 알아보기」→ grandmawellnessrecipes.com/us/, 그림 SNS_SETUP GW_US_*) ↔ 인스타 **@grandmawellness_us** (가입 때 오타 garand… → 11-11 Claude가 고침, 가입 메일은 snbheadquater+guus@gmail.com(오타 그대로), 비즈니스·음식 및 음료, 연결 확인). sites.json gw/us. 자동 게시 열쇠 저장 완료(META_PAGE_TOKEN_GW_US, 페이지 id 1492852860570104).
- 2026-11-11 열쇠 옮기기: 페이스북은 jeff 크롬에만 로그인됨 → jeff `ControlTower\META_KEYS_EXPORT.cmd`(tools\meta_keys_move.py export: 시크릿·토큰 붙여 넣고 짧은 암호로 잠근 파일) → Claude가 노예2로 옮김 → 노예2 `META_KEYS_IMPORT.cmd`(암호 입력, 자격 증명 저장 후 파일 삭제). 8개 사이트 열쇠 모두 노예2에 있음(만료 없음 확인). 앱 권한이 모든 페이지라 탐색기에서 페이지 선택 창이 안 뜨는 게 정상. 앱 설정의 시크릿 칸은 복사가 막혀 있음.
- 2026-11-11 점검(Graph API): 인스타 8개 모두 페이지에 연결·프로필 사진·링크(각 사이트 주소) 확인 완료. 휴대폰 앱 계정 추가는 목록에 안 뜨면 "다른 프로필 사용"으로 직접 입력.
- 한국: **밴드** 2개 만듦(2026-11-11, snb 계정, 노예2 앱 브라우저에 로그인): **오늘의 과거 뉴스** https://band.us/band/105074467 · **할머니 건강레시피** https://band.us/band/105074530 — 둘 다 공개 밴드, 커버 `tools/band_assets/band_*_kr.jpg`(정사각형), 소개 글+대표 사이트(todayspastnews.com/kr/ · grandmawellnessrecipes.com/kr/). 밴드 Open API `/v2.2/band/post/create`로 자동 게시 가능(다음 단계: 밴드 개발자 앱 등록·열쇠). **네이버 블로그는 보류**(자동 글쓰기 API 종료, 사이트 글 복사는 중복 글로 불리 — 하더라도 짧은 소개+링크만).
- 엑스 계정(2026-11-03 사용자 생성): **@snb_newsbase** (일본어, 과거뉴스·시니어뉴스 공용). `sites.json` 사이트별 `x_account` — snb/jp·tm/jp 에 넣음 → 아래쪽 X 링크, `twitter:site` 메타, 공유 버튼 `via=`. 영어 계정 생기면 us 사이트에 넣음.
- 원칙: 쇼츠·릴스는 그 자체로 끝나는 내용, 사이트 유도는 링크가 실제로 눌리는 곳(긴 영상 설명란·고정 댓글, 페이스북·엑스 본문, 메일·LINE)에서만. 방송국 제작 코드는 건드리지 않고 완성물만 읽어 게시. 모든 외부 게시는 사용자 승인 후.
- P0 적용(2026-11-01): 기사 페이지에 **"이 회차의 다른 이야기"**(같은 날·같은 오전/오후 기사 목록, n/전체, 다음 이야기 버튼 — 기사 2개 이상일 때)와 **"함께 보면 좋은 다른 방송"**(같은 언어의 다른 브랜드, 태그 겹치는 글 → 없으면 그 브랜드 최신 글, 브랜드당 1개, 샘플·검수대기 제외, 각 도메인 절대주소). build.py `FLOW_LABELS`, `make_cross_index`, `cross_for`.
- 확인된 문제: 과거뉴스·시니어 사이트에 실제 글이 아직 안 올라옴(과거뉴스는 10/21 예시 글만, 시니어는 3개). 할머니만 자동 게시 중 → site_publish 연결 점검 필요(P0).

## 사이트 영상 = 맛보기 → 유튜브로 (2026-11-13 사용자 결정)
- 목적: 사이트에서 다 보지 않고 유튜브로 가게 해 조회·구독·추천을 유튜브 채널에 쌓기.
- 시니어·과거뉴스(긴 영상): 섬네일 누르면 사이트 안에서 **45초**만 재생(build.py `PREVIEW_SECONDS`, 앞으로 건너뛰어도 45초에서 멈춤) → 끝 화면 "전체 영상은 유튜브에서 보기"(45초부터 이어서) / "처음부터 다시 보기".
- 할머니(쇼츠): 끝까지 재생 → 끝 화면 "다른 레시피도 보세요" = 같은 사이트의 다른 영상 3개(최신순, 누르면 유튜브 쇼츠) + "채널에서 레시피 더 보기".
- 만든 곳: `templates/macros.html` video(끝 화면은 `<template class="video-end">`, 나라별 문구 build.py `VIDEO_LABELS`), `static/site.js` playVideo(유튜브 IFrame API, 못 받으면 예전처럼 end 초만 붙인 iframe), `style.css` 끝 '영상 맛보기 끝 화면'.
- `sites.json` youtube_channel 8개 채널 주소 넣음(@snbnews_en·_jp, @timemachinenews_kr·_jp·_en, @grandmarecipes_kr·_jp·_en) → 사이트 아래 YouTube 링크도 켜짐.
- 주의: 과거뉴스 영상은 유튜브 '퍼가기 허용'이 꺼져 있었음(2026-11-13 확인) → 꺼져 있으면 사이트 안에서 재생 안 됨.

## 디자인 검사 도구 (2026-11-02)
- 2026-11-04 아래 메뉴 아이콘 → Lucide(ISC, 상업 사용 가능). 방송 그래프 예시: ECharts(Apache-2.0)로 실제 11/4 그래프 3개를 다시 그려 비교(순위를 막대 높이로 그리면 6위가 5위보다 커 보이는 문제, 출처 줄에 그래프와 관계없는 자료가 붙는 문제, 결론 문장 두 번 나오는 문제 발견) → 사용자 결정 대기.
- 사용자 요청: Taste Skill · Impeccable · Ponytail 이 방송국에 도움이 되는지 확인하고 필요하면 사용.
- **Impeccable 검사기 사용**(`npx impeccable detect <html>`, 무료·키 없음, 웹 화면 전용): 실제 브라우저(Playwright)로 다시 확인한 문제만 고침.
  - 할머니 '레시피 보기' 버튼 글자 대비 2.8:1(밝은 화면)·1.5:1(어두운 화면) — 원인 `.shell a { color: inherit }` 가 버튼 글자색을 덮음 → `a.gw-btn`.
  - 기사 아래 '다음 이야기' 버튼 2.8:1 — 같은 원인 → `a.edition-next`.
  - 과거뉴스 첫 화면 날짜 패의 '과거 뉴스' 10px·'오후 편성' 12.6px → 최소 13px·14px, 흐림 제거. 어두운 화면 로고 작은 빨간 글자 3.6:1 → #ec7a64.
  - 공유 버튼: LINE·네이버 초록 위 흰 글자 2.3:1 → 짙은 글자, 페이스북 파랑 한 단계 짙게.
  - 2026-11-02 사용자 요청 "AI 티 나는 디자인 다 수정(기능은 해치지 말고)" → 고침:
  - 사선 줄무늬(과거뉴스 썸네일 위 띠)·필름 구멍 줄무늬 → 단색 띠 / 로고 대체 동심원 그라데이션 → 단색 원.
  - 한쪽 굵은 색 테두리(상품 칸·샘플 안내·지난 레시피 머리·일본 기사 소제목·오늘의 레시피 카드·일본 옆 카드) → 없애거나 가는 선·밑줄로. 인용문 4px → 2px, 페이지 머리 밑줄 4px → 2px.
  - 사진 출처 10.4px → 13px, 사진 위 작은 글 자간 넓힘 제거, 기사 소제목 크기 단계 본문→h3→h2 각 1.25배.
  - 한국어·일본어 글의 줄표(—) → `build.py cjk_dashes`: 제목 줄은 가운뎃점, 문장 끝 뒤는 마침표, 쌍점이 이미 있으면 쉼표, 나머지는 쌍점. 원고 파일은 그대로, 화면에서만 바꿈.
  - 남은 경고는 검사기 오판(실제 화면에서 확인): 목록 줄 '여백 없음'(링크 안에 위아래 16px 이상 있음), 과거뉴스 '제목 크기 평평'(실제 40/29/24px), 일본 페이지 머리(일본은 밑줄 0).
  - 확인: 3개 브랜드 9개 사이트 첫 화면+기사, 밝은/어두운 화면에서 13px 미만 글자 0, 대비 미달 0(숨은 '본문 바로가기' 제외).
- 2026-11-04 모바일 확인: 9개 사이트 모든 페이지(89쪽)를 360·390·768·1024·1440 폭에서 옆으로 밀림 검사 → 기사 속 넓은 표만 문제 → 표 안에서만 옆으로 밀어 보게 고침, 0건.
- 2026-11-04 캐시: build.py `asset_version` — style.css·site.js 주소 끝에 내용 해시 `?v=` 를 붙여, 디자인을 고쳐 올리면 방문자도 바로 새 파일을 받음.
- 2026-11-04 사용자 "AI 티가 너무 난다, 기능은 그대로": taste-skill(Leonxlnx, 별 약 1.5만) 하우스 규칙 + ui-ux-pro-max(nextlevelbuilder, 별 약 7.4만) 참고해 `style.css` 끝에 '디자인 정리' 층만 덧붙임(HTML·기능 변화 없음 확인). 알약 표시 → 색 글자, 상자·색 띠 머리 → 굵은 제목+선, 떠오르는 카드 그림자 제거, 과거뉴스 카드 위 칸은 메인 사진 자리라 높이 유지(사진 섞여도 줄 맞음), 사진 없을 때만 파스텔 → 꺼진 흑백TV 같은 짙은 단색+연도, 빨간 숫자 배지 → 회색 숫자, 미국 첫 화면 파란 빈 상자 숨김, 모서리 3px. ui-ux-pro-max 의 자동 추천(랜딩 페이지형·클레이 스타일)은 시니어 뉴스에 안 맞아 쓰지 않음. 밝은/어두운 화면 13px 미만 0, 대비 미달 0.
- Taste Skill: 새 웹사이트를 처음 디자인하는 도구(웹 사진도 끌어옴) → 이미 정한 디자인이 있어 쓰지 않음.
- Ponytail: 코드를 짧게 쓰게 하는 규칙(검토는 '과한 코드'만 봄, 버그·보안 안 봄) → 방송국 코드는 안전장치가 핵심이라 기본 사용 안 함.

## 할머니 레시피 9개 언어 (2026-11-17 사용자 결정)
- 레시피 사이트만 9개 언어: 한·일·영(원래) + **중국어 간체 `gw/cn`(zh-CN)·번체 `gw/tw`(zh-TW)·스페인어 `gw/es`·프랑스어 `gw/fr`·독일어 `gw/de`·러시아어 `gw/ru`**. 시니어·과거뉴스는 그 나라 소식이라 늘리지 않음(사용자와 합의).
- 새 6개 판: 화면 글자는 Claude가 직접 번역해 `sites.json`에 넣음(비용 0), 영상은 영어 쇼츠, 아마존·페이스북·인스타 칸은 비움(나중에 정함). 사이트별 `lang_name`(언어 바꾸기 줄에 보이는 이름).
- 화면: 레시피 사이트 맨 위 **언어 바꾸기 줄**(🌐, 지금 언어가 맨 앞, 휴대폰은 한 줄로 옆으로 밀기). 기사 화면이면 그 기사의 번역판으로 이동, 번역판이 없으면 그 언어 첫 화면. 검색엔진용 hreflang 에 `x-default`(영어판) 추가.
- build.py: 6개 언어 날짜·요일 형식(`WEEKDAYS`, `MONTHS`, `fmt_date`, `fmt_short`), `FLOW_LABELS`·`VIDEO_LABELS` 6개 언어(전체 언어 코드 먼저 찾고 앞 두 글자로 대체), `lang_sites`. style.css: 중국어·러시아어 글꼴, 언어 줄.
- 번역(노예2 `YouTubePublisher\publisher\gw_translate.py`): 영어 글(`gw/us`)을 **GPT-4o-mini**로 6개 언어 번역, 1편 6개 언어 약 0.006달러. 엔진 검사(머리말 키·영상 ID·재료/단계 개수·소제목·표·링크 주소·g/ml 분량 숫자·길이·면책 문구) 통과한 것만 올림, 실패 시 2번 더. 하루 비용 상한 0.5달러, 비용 기록 `YouTubePublisher\logs\gw_translate_cost.jsonl`.
- 자동 게시(`site_publish.py` `gw_translations`): 영어 글이 올라갈 때 번역본도 같이. 번역본은 `YouTubePublisher\state\gw_translations\<언어>\` 에 저장 → 영어 원문(영상 ID 줄 빼고)이 그대로면 다시 번역 안 함. 한 번 실행에 새 번역 6개까지(업로드 작업을 오래 안 붙잡게). `pages/`(about·grades·privacy)도 같은 방식으로 번역.

## 과거뉴스 첫 화면 정리 (2026-11-18 사용자 "오전밖에 없는데 오전 표시 안 됨, 지난 뉴스는 날짜로")
- 하루 한 회차라 '오전 편성' 대신 **오늘의 방송 / Today's broadcast / 今日の放送** 하나(sites.json tm 라벨 `edition_day`). 오전·오후가 둘 다 있는 날만 예전처럼 나눔(home_tm.html `split`).
- 오전·오후 표시 전부 없앰: tm 사이트 `show_slot: false` → 목록·기사의 '오전' 표시 숨김, 썸네일 판 글자는 '오늘의 방송'(macros.html). 소개 문구·사이트 설명·about 의 '오전 6개·오후 6개' → '매일 6개'(한·일·미).
- 지난 방송 목록: 최근 8개 → **날짜별 묶음 4일치, 그날 이야기 전부**(build.py `earlier_days`, 키 `stories`). 날짜 머리 `.archive-day`.
- 하루 6편이 안 채워지던 원인: 노예2 `site_publish.py` 가 예전 12편 규칙대로 **1~6번 글만** 올림 → 방송에서 빠진 이야기 대신 들어간 예비 이야기(7·8·9번)가 사이트에 없었음(방송은 10/30 이후 매일 6편). 고침: `tm_lineup()` — 업로드 폴더 `source.json` 의 실제 방송 이야기 순서대로, 연도+제목 글자 겹침으로 글 번호를 찾아 올림(사이트 순서 = 방송 순서). '보정 전 초안 건너뜀' 규칙도 없앰(사용자: 방송된 건 전부 올림). 지난 날짜 모두 다시 올려 한·일·미 모든 날 6편 확인. 백업 `site_publish_backup_20261118_lineup.py`.

## 예약 공개 전 영상·빈 광고 자리 (2026-11-18 사용자 "할머니 영상이 비공개·로그인으로 뜬다", "광고 비어 있는 곳에 관련 사진")
- 원인: 영상은 유튜브 **예약 공개**(publish_at)로 올라가는데, 게시 프로그램이 업로드 승인되자마자 사이트 글(영상 ID 포함)을 올림 → 공개 전 영상이 '비공개 동영상·로그인'으로 보임(할머니 한·일 다음 날분, 미국 당일·다음 날분, 과거뉴스 미국 당일).
- 고침: 노예2 `site_publish.py` `not_out`·`outbox_items` — 공개 시각 전인 회차의 글은 `wait_video: true` 를 붙이고 영상 ID 를 뺌 → build.py 가 그 글을 숨김. 공개 시각이 지나면 다음 실행(5분마다)에 표시 없는 글로 다시 올라가 사이트에 나타남. 할머니·과거뉴스·시니어, 6개 번역판 모두. 백업 `site_publish_backup_20261118_waitvideo.py`.
- 빈 광고 자리: 광고 번호(sites.json ads)가 없는 자리 → **같은 사이트의 사진 있는 글 하나**(사진+제목, 누르면 그 글, 머리 "이런 이야기도 있어요" 9개 언어 `PROMO_LABELS`). 페이지마다 다른 글(`promo_seed`). 광고 번호를 넣으면 자동으로 광고. 2026-11-18 사용자 "추천 상품도 상품 말고 일반 사진": 사이트 공통 추천 상품·기사별 상품 자리도 링크가 없으면 같은 방식(macros.html `promo(off)`, 자리마다 다른 off → 한 페이지 안 같은 글 안 겹침, 1,125쪽 겹침 0). 제휴 링크가 들어오면 자동으로 상품. 넓은 자리는 사진 왼쪽·제목 오른쪽. 전 사이트(시니어·과거뉴스·할머니 9개 언어) 적용.

## 제목·요약 줄바꿈과 할머니 세로 영상 (2026-11-18 사용자 "영상 옆 글자가 한 글자만 다음 줄로, 단어 중간에서 끊김, 자동으로 맞게, 모바일도")
- build.py 필터 `tt`(보이는 제목)·`pt`(보이는 요약), 모든 사이트 첫 화면·목록·기사·추천 칸에 적용(메타 태그는 그대로):
  - 제목의 '｜'·' | ' 뒤 부제는 새 줄(`.t-sub`, 조금 작게).
  - 일본어 = BudouX(Google, Apache-2.0) 구절 + 긴 구절은 글자 종류 바뀌는 곳에서 한 번 더, 'おば|あちゃん' 같은 짧은 히라가나 조각은 붙임. 중국어(간체·번체) = jieba(MIT) 낱말. 구절 사이에만 `<wbr>` + `.px { word-break: keep-all }`. 문장부호는 앞 구절에 붙여 줄 첫머리에 안 옴. 한국어는 원래 keep-all.
  - CSS: 제목 `text-wrap: balance`, 요약 `text-wrap: pretty`(마지막 줄 한두 글자 방지).
  - requirements.txt 에 budoux·jieba (Cloudflare 빌드가 설치). 못 불러오면 예전처럼 그냥 글자.
- 요약이 160자에서 단어 중간에 잘려 있던 것('crunchy r', 미국 386개 중 134개): `tidy_summary` — 문장 끝까지(절반 이상 남으면), 아니면 낱말 경계 + '…'. 원고 파일은 그대로.
- 할머니 쇼츠 영상 자리 = 세로 9:16(`.video-short`), 썸네일은 유튜브 세로 그림 `oar2.jpg`(없으면 보통 썸네일). 첫 화면은 영상 왼쪽·글 오른쪽 가운데 맞춤, 휴대폰은 영상 폭 62% 가운데. 기사 화면 영상 최대 16rem.

## 컨트롤 판넬 웹사이트 사이트별 표시 (2026-11-18 사용자 "웹사이트가 여러 종류인데 왜 통합으로 나오냐, 분리해서")
- 전에는 각 방송국 창 '블로그·SNS'에 '최근 사이트 게시 결과 (전체)' = 세 브랜드 합친 GitHub 반영 줄(SITE_PUBLISHED 22 등)만 나옴.
- 노예2 `site_publish.py` `write_site_status` → 실행마다 `YouTubePublisher\logs\site_status.json`: 사이트(브랜드/나라)별 자동 게시 글 수·최신 글 날짜·공개 대기(예약 공개 전 숨긴 글) 수·마지막 반영 시각과 파일 수·문제 줄(건너뜀·없음·오류). 백업 `site_publish_backup_20261118_sitestatus.py`.
- 노예2 `station_status._blog` 가 `per_site` 로 넘김 → jeff·노예2 `console_ui._station_common` '사이트별 상태' 표(시니어 일·미 / 과거뉴스 한·일·미 / 할머니 9개 언어, 사이트 이름 누르면 그 사이트). 백업 `station_status.py.before_sitesplit`·`console_ui.py.before_sitesplit`(두 PC). jeff 판넬에서 세 창 모두 확인.
- 같은 날 사용자 "그게 아니라 몇 명 봤는지 페이지뷰·분석": 지표(노예2 `tools\metrics_collect.py`, 3시간마다)의 웹사이트는 도메인(브랜드) 합계뿐이었음 → `by_site()`: 클라우드플레어 `httpRequestsAdaptiveGroups`(무료 플랜, 표본 근사값)에서 주소 앞부분(/kr/ /jp/ …)별로 사람이 연 글 페이지(GET·HTML·200)의 오늘·어제·7일 방문·7일/28일 페이지뷰·28일 흐름·7일 많이 본 글 5개. 백업 `metrics_collect_backup_20261118_bysite.py`. jeff `metrics_ui.py`(백업 `.before_bysite`): 첫 화면 '웹사이트 7일 방문' 칸 아래 사이트별 7일 페이지뷰, 방송국 화면 '웹사이트'에 사이트별 표(넓은 칸). 오늘·어제는 UTC 날짜, 검색 로봇이 섞일 수 있음. (웹 분석 RUM 은 통계 열쇠에 계정 권한이 없어 못 씀.)
- 같은 날 사용자 "전날은 왜 없어? / 일별은 없는 거야? → 넣어줘": 시간별 숫자(15일)를 받아 **한국 시간 날짜**로 나눔(`kst_daily`, 오늘·전날도 한국 시간). 방송국 화면 '웹사이트'에 **일별 페이지뷰 표**(최근 15일, 줄 = 날짜·요일, 칸 = 사이트, 괄호 = 방문, 맨 끝 합계, 오늘은 '진행 중'), 사이트별 표 '어제' → '전날', 첫 화면은 사이트별 '전날/7일'.

## 유튜브 썸네일·채널 인증 (2026-11-17)
- 맞춤 썸네일·15분 넘는 영상은 채널 **전화 인증**이 있어야 함(API `longUploadsStatus` = allowed 면 인증됨, eligible 이면 안 됨). 번호 1개로 1년에 2채널까지.
- 상태(11-17): 인증됨 = 과거뉴스 일본, 시니어 일본·미국, 노래 모음(11-17 사용자). **안 됨 = 과거뉴스 한국·미국**(다른 번호 필요), 할머니 3개(쇼츠라 불필요).
- 노예2 `upload.py`: 썸네일 실패 이유 기록(`THUMB_FAILED 403 forbidden …`), uploaded.json `thumb_failed` 표시 → `retry_thumbs()`가 업로드 실행 때마다 다시 넣음(채널이 아직 막혀 있으면 6시간마다 한 번만 시도, 기록 `logs\thumb_retry.json`). 과거뉴스 한국 19편·미국 18편 표시해 둠 → 인증되면 자동으로 들어감. 백업 `upload_backup_20261117_thumbretry.py`.

## 과거뉴스·시니어 썸네일 문구·사진 (2026-11-17 사용자 "썸네일에서 보고 싶게, 단어 한 개 이럼 안 된다", "시니어도 마찬가지")
- 문제였던 것: 큰 줄이 '연도+낱말'('1995년 비자금 수뢰', 'Geneva 1985', '1997年の衝撃', AI 실패 시 '1997년의 오늘'), 바탕은 완성 영상 아무 장면(그 시절 다른 사진·'NOT FROM THE EVENT'·출처 글씨가 뽑힘).
- 노예2 `autometa.py`(HOOK_V 5): 큰 줄 = 궁금하게 만드는 후크(질문·반전·숫자, 좋은/나쁜 예 지시), **연도 금지**(`WEAK_RX`, 금액 숫자는 허용), '○○년의 오늘' 대체 문구 없앰. 숫자 대조는 '1,000'='1000'. 시니어도 같은 규칙.
- 과거뉴스는 제작 엔진이 1번 기사 재료를 보냄: jeff·노예1 `tm_documentary\thumb_assets.py`(새 파일) + `episode_daily.py` → source.json `thumb_assets` = 원고 `title_hook`(영상 안 후크 카드 문구)·`title_what`·사건 사진 원본(`<회차>_thumb.jpg`). 사진 고르기: 주인공 인물 → 원고에 이름 나오는 주제·물건(사건 해 ±3년) / 'era'·장소·지도·AI·사건 뒤 사진 금지 / 맞는 사진 없으면 사진 없음. `tm_backfill.py send`가 사진도 노예2 `tm_from_jeff`로.
- 노예2 `thumbnail.py`: 사진 원본이 오면 바탕(세로 인물 사진은 '사진 왼쪽·글 오른쪽'), 없으면 영상 장면을 크게 흐리고 어둡게(분위기만, 넓은 배치).
- 백업: 노예2 `autometa_backup_20261117_hook.py`·`thumbnail_backup_20261117_photo.py`, jeff·노예1 `episode_daily_backup_20261117_thumb.py`·`tm_backfill_backup_20261117_thumb.py`.
- 2026-11-17 밤 점검(바뀐 코드 뒤 올라간 영상은 아직 없음 → 다음 업로드분 미리 확인, 기록 노예2 `ControlTower\CHANGES_20261117_THUMB_CHECK.md`):
  - 한국 11/18 이 옛 문구 '1997년의 오늘' → 원인: Gemini 후크 '1달러 1000원?'을 숫자 대조가 '1' 때문에 말없이 버림. `autometa.py` `_extra_numbers`('1'은 허용), `_thumb_why`(막힌 이유 로그 `HOOK_THUMB_REJECTED` + 이유 알려 주고 한 번만 다시 받기). 백업 `autometa_backup_20261117_numcheck.py`.
  - 썸네일 재료 도입 전 회차(한국 11/18, 미국 11/18~20)는 jeff·노예1 제작 폴더에서 thumb_assets 를 다시 뽑아 넣고 다시 만듦(백업 노예2 `ControlTower\backups\20261117_2300_thumb_assets_backfill\`).
  - 띠 모양 사진(미국 11/20 사다트 1656x5067 → 눈만 나옴): jeff·노예1 `thumb_assets._strip`(세로>가로×2·가로>세로×2.6 안 고름, 두 PC 같은 코드) + 노예2 `thumbnail.py` 안전장치(오면 흐린 바탕, `THUMB_RAW_PHOTO_STRIP`). 백업 `thumb_assets_backup_20261117_strip.py`·`thumbnail_backup_20261117_strip.py`.
  - 실제 유튜브 반영 확인은 11/18 11:00 한 번(예약).
  - 11/18 11:00 확인: 과거뉴스 일본 11/18 새 방식 그대로 반영(후크 '改札でタッチ？'+설명 줄). 시니어 일본 11/18 오전은 **Gemini 402(선불 잔액 없음)** 로 후크를 못 받아 규칙 문구(기사 제목)가 단어 중간에서 잘림('…見えた落') → `autometa._clean_fallback`: '…'·'、'·'!?' 같은 끊는 자리에서 자름. 같은 날 다른 감시가 `thumbnail.py` 에 '안 들어가면 넓은 배치로 다시' 안전장치 추가(11/08 오후 TEXT_DOES_NOT_FIT). Gemini 잔액은 사용자 충전 필요.
  - 채널 인증 대기 37편(한국 19·미국 18, 사용자 '새 방식으로 다시 만들기'): 제작 PC 폴더에서 원고 후크·사건 사진을 다시 뽑아 thumb.jpg 를 새 방식으로 다시 만들어 둠(제목·설명은 그대로, 원고 후크가 길거나 연도 든 2편은 Gemini 후크). 백업 노예2 `ControlTower\backups\20261117_2300_thumb37_newstyle\`. 인증되면 retry_thumbs 가 이 그림을 넣음.

## 할머니 쇼츠 9개 언어 (2026-11-17 사용자 결정)
- 새 채널 없이 단계적으로. 1단계(적용): 영어 쇼츠(gw_en) 올릴 때 **6개 언어 제목·설명**(유튜브 localizations)을 함께 붙임 — 노예2 `YouTubePublisher\publisher\yt_localize.py`(gpt-4o-mini 1번에 6개 언어, 영상 1편 0.1센트 미만, 비용 기록·하루 상한은 gw_translate 와 같음), `upload.py` 가 사용. 설명란 사이트 주소는 그 언어 사이트(/cn/ 등, 글 없으면 그 언어 첫 화면). 검사(제목 100자·설명 5000자·< > 없음·주소·g/ml 숫자·#shorts) 못 통과한 언어만 빠지고, 번역·업로드 문제가 생겨도 영어로는 올라감. 결과는 회차 폴더 `localizations.json`.
- 2026-11-17 사용자 "업로드 전에 확인하고 올려": 노예2 `config\LOCALIZE_REVIEW.flag` 가 있으면 gw_en 은 6개 언어 제목·설명을 먼저 만들고 Claude 가 확인해 회차 폴더에 `LOCALIZE_CHECKED.json`(use true/false)을 남길 때까지 업로드 대기(`LOCALIZE_CHECK_WAIT`). 12시간 넘게 확인이 없으면 영어만 올림. 플래그를 지우면 확인 없이 바로. 첫 확인 11/19분(11/18 03:40 예약). **사용자 결정(11/17 밤): 11/19·20·21분 3일만 확인**하고 문제 없으면 11/21분 뒤 플래그를 지워 확인 끔(예약 3개).
- 이미 올라간 영상은 그대로 둠(사용자). 자막 트랙은 다른 권한(영상 관리·자막) 로그인이 필요 → 아직 안 함. 언어별 목소리(다국어 오디오)는 API로 못 올림(스튜디오에서만, 쇼츠 지원 여부 확인 필요).
- 2단계(나중에): 반응 좋은 언어만 채널 따로.

## 할머니 레시피 「사 먹을 텐데…」 코너 (2026-11-17 사용자 결정)
- 설계도: Claude 문서 「할머니 레시피 「대신 사 먹는다면」 코너 설계도」. 코너 이름 **어차피 사 먹을 텐데…** / どうせ外で食べるなら / Eating out anyway?
- 내용: 오늘 레시피 주재료가 든 사 먹기·배달 메뉴 하나 → 메뉴를 재료로 나눠 재료마다 옛 책(동의보감·본초강목·컬페퍼) 효능 문장을 "책에 이렇게 쓰여 있다"로 소개(숙취·병명도 책 그대로, 사용자 결정) → "한번 드셔 보세요". 영상 끝 안내 바로 앞, 쇼츠·가로 둘 다, 월~금 새 레시피 + 일요일 모아보기(토요일 비교는 아직).
- 메뉴 고르는 순서: 그 나라 일반 메뉴 → 같은 재료 아시아 식당 메뉴(미국) → **효능이 비슷한** 재료가 든 메뉴(사용자: "대체가 아니라 효능·효과가 비슷한 것") → 없으면 그날 코너 빠짐. '비슷한 효능' = 원문 장부 tags 첫째(대표 효능)가 같은 재료 우선. 대사도 "옛 책에 ○○와 비슷한 효능이 적힌 △△". 오늘 레시피와 같은 음식(same_as)은 추천 안 함.
- 노예2 파일: `GrandmaWisdom\alt_menu.py`, `data\menu_ledger.json`, `data\classic_seed.json` → `build_classic.py`가 원문 사본(`data\classic_src\corpus.json`)과 글자 그대로 대조해 `data\classic_ledger.json`. AI 비용 없음. `video_maker.build_video`에 호출(START_DAY 2026-11-22 부터), 사이트 글은 `publisher\site_publish.py with_alt_menu`가 참고 자료 위에 표로 넣음.
- 2026-11-17 전환(사용자 결정 ①): 코너 시작에 **오프닝 영상** 4초 — 영화 배급사 오프닝 분위기(어두운 화면·빛줄기·금빛 "할머니 건강레시피 제공", 웅장한 소리, 특정 회사 로고·오프닝은 따라 하지 않음) → "띠링!" 반전 → 장난스러운 타이틀 롤 "어차피 사 먹을 텐데..."(글자가 통통 떨어짐, 색 점, 징글). 소리는 전부 직접 합성. 글꼴 OFL: Jua·Mochiy Pop One·Chewy / Nanum Myeongjo·Shippori Mincho·Cinzel Decorative. 만드는 도구 `GrandmaWisdom\make_stinger.py` → `assets\alt_stinger\stinger_<ko|ja|en>_<wide|short>.mp4`. video_maker 가 코너 맨 앞에 그대로 끼움(`clip` 장면), 코너 동안 위 큰 제목은 코너 이름, 끝 안내에서 레시피 제목으로 돌아옴. 코너 이름(한국어) **어차피 사 먹을 텐데…**.
- 2026-11-17 계화(木犀花, 본초강목 '生津辟臭化痰') 원문 추가 → 11/27 계화차도 세 나라 모두 코너(대표 효능 '가래'가 같은 생강·무·사과). 원문 장부 42줄.
- 2026-11-17 순서 고침: 코너는 영상 **맨 끝**(할머니 마지막 인사 → 오프닝 → 코너). 오프닝 타이틀 롤에 작은 글씨 "레시피 알려 드려도..." 추가.
- 2026-11-17 사이트 **'집에서 만들기'(menu) 코너**(사용자 승인): 코너 메뉴의 만드는 법 글 `content/gw/<나라>/menu/<첫 방송일>-am.md`(재료표·만드는 법·팁·옛 책 표, 구글 레시피 데이터). 9개 레시피 사이트 sections 에 `menu` 추가(아래 메뉴 아이콘 Lucide utensils). 영어 글 → 노예2 gw_translate 로 6개 언어.
  - `hold_until: YYYY-MM-DD` 머리말 → 그 날짜 전엔 사이트에 안 넣음(build.py). 둘째 코너부터는 글이 생겨야 탭·목록이 생김. 레시피 첫 화면의 '오늘' 날짜·지난 글은 첫 코너(recipe) 기준.
  - 메뉴 글에는 영상 자리 표시·'오늘의 레시피' 표시 없음(macros.html).
  - 노예2 `GrandmaWisdom\data\menu_pages.json` {나라: {메뉴: 글 날짜}} → `alt_menu.py` 가 ① 코너 마지막 대사에 "만드는 법은 채널 프로필 링크의 홈페이지에 있어요" ② 레시피 사이트 글 코너 단락에 `../menu/<날짜>-am.html` 링크. 새 메뉴가 나오면 글을 만들고 여기에 추가.
  - 11/22~27 메뉴: 한국 쌀국수·애플 시나몬 파이·수정과·버섯전골·카레라이스·대추차 / 일본 フォー·アップルパイ·チャイ·きのこの炊き込みご飯·カレーライス(11/26)·ぶり大根 / 미국 Pho·Apple pie·Chai latte·Mushroom risotto·Chicken tikka masala·Hot apple cider.
- 2026-11-17 배경 영상 고침(사용자 승인): `video_maker.stock_clip` — Pexels·Pixabay 모두 새 영상이 없으면 이미 쓴 영상을 다시 씀(전에는 무늬 배경만 나옴, 로그 `STOCK_REUSE`). 세 나라 공통. 백업 `backups\video_maker_20261117_reuseclip.py`.
- 남은 일: 시험 영상(노예2 `OUTPUT\ALT_TEST_20261117`) 사용자 확인 → 괜찮으면 시험 폴더·`LOGS\alt_test_run.py` 삭제.
- 2026-11-17 밤 시험 영상 점검: 가로 영상 코너 첫 2컷이 **초록 크로마키 영상**(pixabay_51927, 'apple pie' 검색) → `video_maker.green_screen()`: 앞·가운데·뒤 3장의 형광 초록 비율 25% 넘으면 안 씀(로그 `GREEN_SCREEN_SKIP`, 결과 `VIDEO_CACHE\green_check.json`), Pexels 캐시·Pexels 받기·Pixabay 세 곳. 최근 영상 93개 검사 오판 0. 백업 `backups\video_maker_20261117_greenscreen.py`. 19:02 시험 영상은 배경 재사용 고침 전 것이라 한·일·영 시험 영상을 다시 만듦(무료, 22:28~22:48).
- 2026-11-17 영어 영상의 옛 책 한자 원문이 □□□ 로 나옴(Segoe 에 한자 없음) → `video_maker.cjk_safe()`: 영어 글꼴로 한자·가나·한글이 든 줄은 그 줄만 한·일 글꼴(TextLayer.text·textlength·wrap). 백업 `backups\video_maker_20261117_cjkfont.py`.

## 시니어 밀린 회차 노예1 병행 제작 (2026-11-17)
- 노예2 타워 '시니어 시간' 대기 때문에 미국 밀린 회차(약 21편)가 하루 3편 정도만 처리됨 → 노예1(i7·32GB)에서 병행. 노예1 = 오래된 회차부터, 노예2 = 최신부터, 맡은 회차 표시(노예2 `ControlTower\state\n1_claims`)로 겹치지 않게.
- 노예2: `ControlTower\tools\n1_queue.py`(10분마다, 목록 `state\n1_remake_queue.json`, 노예1 장부·영상 DB 합치기), `us_remake.py` 가 노예1 몫 건너뜀.
- 노예1: `D:\SNB_REMAKE\tools\n1_remake.py`(예약 작업 SNB_N1_Remake 10분마다, `D:\SNB_REMAKE\ENABLED` 있을 때만 자동). 펙셀스 끔·픽사베이만(사용자). 시험 `--nosend` → 확인 → `--send <key>`.
- 사용자 결정(11-17): 11월 OpenAI 20달러 한도를 넘어도 밀린 회차는 **그냥 만든다**(엔진 한도 40달러 그대로).
- 2026-11-18 시험 통과 → **노예1 자동 켬**(`D:\SNB_REMAKE\ENABLED`). 시험편 일본 10/31 오후: 28분 36초·1080p30·DJ 포함, 노예2 업로드 대기열로 보냄.
  - 노예1 홈 = `C:\Users\miwoo`(일부는 `D:\SNB_REMAKE\home` 로 이어짐), `C:\Users\user` 폴더는 만들 수 없음(관리자 아님) → `tools\n2paths.py`: 받는 글자 파일은 노예2 경로→노예1 경로, 보내는 파일(`put`)은 노예1 경로·`D:\SNB_REMAKE\home` → `C:\Users\user`. 처음 복사본 3,156개 파일 경로 바꿈.
  - 같이 쓰는 기록(지역별): DJ 노래 순서 `DJ_SELECTION_STATE`·DJ 영상 조각 `DJ_AKI_CLIP_HISTORY`·`WORD_MEDIA_HISTORY`·broll_history·COSTS·MEDIA_PROVIDER_STATS·EDITOR_MEMORY·BROLL_KEYWORD_QUEUE (일본 = AssetVault·AppData\Local\SeniorNews, 미국 = WEST\V28_VAULT·V28_WEST_STATE). 회차마다 받아 가고, 만든 뒤 바뀐 부분만 노예2 `n1_queue.merge_jobs`(3방향 합치기)로 얹음.
  - Groq 열쇠: 노예2는 Chatbox 설정에서 읽음 → 노예1은 사용자 환경 변수 GROQ_API_KEY.
  - 펙셀스 끄기: `.venv\Lib\site-packages\sitecustomize.py` 가 urllib·requests·curl(엔진의 curl 대체 요청, 주소를 표준 입력으로 넘김)까지 막음 → 엔진이 펙셀스를 끄고 픽사베이로. (시험 첫 회는 curl 길로 새서 펙셀스가 불렸음, 고침.)
  - DJ에서 멈추면 다음 번엔 뉴스는 두고 `--project` 로 DJ만 다시.

## 할머니 한국어 음성 숫자 읽기 (2026-11-17 사용자 "레몬 슬라이스 이장, 이작은술 — 엔진 고쳐야지")
- 원인: 로컬 음성(Supertonic)은 숫자를 한자어로만 읽음 → "2장"을 '이 장'.
- 노예2 `GrandmaWisdom\ko_numbers.py` `speak_ko()`: 세는 말(개·장·잔·큰술·작은술·송이·줄기·조각·번·시간·살…) 앞 숫자 → 고유어(두 장, 한 작은술), 1~2잔 → 한두 잔, 5~6송이 → 대여섯 송이, 1.5큰술 → 한 큰술 반, 1/3작은술 → 3분의 1 작은술, g·ml·L·℃ → 그램·밀리리터·리터·도. 개월·20대·2단계·2인분·연도 등 한자어로 세는 말은 그대로.
- `video_maker.py` 의 `tts()`·`tts_local_batch()` 에서 한국어일 때만 적용 → 음성만 바뀌고 자막·원고는 그대로. 백업 `backups\video_maker_20261117_konumbers.py`.
- 확인: 지금까지 원고 868줄(186가지)을 바꿔 보고 잘못 바뀐 것 0, 실제 음성으로 만들어 받아쓰기로 '한 작은술·한두 잔·대여섯 송이' 확인.
- 과거뉴스 한국은 이미 `tm_documentary\speakable.py` 에 같은 처리가 있음.

## Gemini 비용 줄이기 (2026-11-18 사용자 "2주에 8만원 너무 많다")
- 구글 청구서(11/1~17 ₩207,052): 출력(생각 포함) ₩93K · 구글 검색 ₩84K(11/7~11 몰림, 지금 하루 ₩450) · 입력 ₩30K. 요즘 하루 ₩1.5~1.8만.
- 프로그램별(장부 `ControlTower\logs\ai_ledger`, 노예2·jeff): 시니어 영상 소재 판정(Groq 한도 차면 Gemini) 하루 ~₩5천, 과거뉴스 원고(ai_editor) ~₩4천, 시니어 원고·블로그 ~₩2~3천.
- **1번 적용(사용자 "바로")**: `BrollSceneSearch._gemini_fit` → gemini-3.1-flash-lite·생각 끔(안 되면 3.8 Flash 생각 끔) + 판정 저장 `LOCALAPPDATA\SeniorNews\VISION_FIT_CACHE.json`(같은 영상·같은 장면이면 다시 안 부름). 실제 영상 20번 비교: 지금 18/20 ₩3.5 → Lite 18/20 ₩0.5. 일본·미국 엔진 같은 파일, 노예1은 코드 동기화로 받음. 백업 `BrollSceneSearch_backup_20261118_cost.py`. `ai_ledger.py` PRICE 에 lite 가격.
- 2번 확인(적용 전): 과거뉴스 ai_editor 생각 1024 제한 시험 4편 — 통과 4/4(지금 3/4), 1번 ₩38 → ₩19. 호출의 약 2/3가 지난 회차(11/02~06 등) 다시 쓰기, 한국 원고 약 40%가 '자료에 없는 숫자'로 다시 씀.
- 지난 회차 다시 쓰기 = 계획된 밀린 과거뉴스 첫 제작(11/10 사용자 결정, 10/30분부터) — 한국·일본 11/18까지 다 올라감, 미국 11/01 한 편만 남음 → 저절로 줄어듦.
- 장부는 11/11부터 검색 수(webSearchQueries)를 세어 1번 $0.014로 넣고 있었음(폭주는 그 전).
- 2026-11-18 사용자 승인: Google Cloud 결제 계정에 예산 알림 「Gemini monthly 200000 KRW alert」(월 ₩200,000, 실제 지출 50·90·100%에서 결제 관리자 메일, 제작은 안 멈춤). 11월은 이미 ₩207K라 이달 알림은 바로 옴.
- 3번 확인: 검색 폭주 = 과거뉴스 옛 `price_compare`(이야기마다 구글 검색) — 11/10 공공 물가표 방식으로 바뀌어 지금은 검색 안 함(함수만 남음). 장부는 검색 요금을 안 셈.
- 2026-11-18 사용자 승인: 과거뉴스 ai_editor 숫자 검사 고침 — 한국어 퇴짜 130번 중 절반은 AI가 지어낸 게 아니라 검사기가 옛 신문 표기("2백16억"·"1억9천1백만"·"6천여만")를 잘못 읽은 탓. `numbers()` 앞에 `_expand_mixed` 추가(같은 크기 단위가 다시 나오면 다른 수로 나눔: "4백7억 3백69억"). jeff·노예1 같은 파일(백업 `ai_editor_backup_20261118_mixednum.py`). 고친 검사기가 전에 놓친 실제 문제 7건 발견: 11/01 한국 현대 세금 "4백47억"(자료는 4백7억, 틀린 숫자 방송됨), 자료에 없는 "1천13km·2천5백 리"(11/14)·"5백 년"(11/15), 반올림 3건("1만 1천"←1만1천6백47 등). 사용자 결정: 11/01 영상은 다시 만들지 않음, 어림은 허용 → `grounding()` 끝 `_rounded`(자료 숫자를 유효숫자 1~3자리로 내림·반올림한 값 허용, 연도 1800~2100은 어림 안 함; 틀린 합계 447억·지어낸 숫자는 계속 걸림). 백업 `ai_editor_backup_20261118_round.py`.


## 컨트롤 타워 한도 경고 (2026-11-18 사용자 "모바일 메시지가 현 상황을 반영 안 한다")
- 원인: 텔레그램 'PEXELS 오늘 사용 481/600 (80%)'은 Pexels 계정 한도(월 2만·시간당 200)가 아니라 시니어 엔진 자체 하루 상한. 엔진은 11/14 Pexels 900·Pixabay 2000으로 올렸는데 노예2 `tower.py`·`config\limits.json` 은 옛 600 그대로. OpenAI 경고도 타워 결제표 예산 $10(엔진 실제 한도 $40).
- 고침(노예2 `tower.py`, 백업 `tower_backup_20261118_caps.py`): `engine_media_caps()` 가 엔진 `SeniorNews.py MEDIA_FREE_DAILY_CAP` 을 읽어 경고·화면에 씀(엔진만 바꾸면 타워도 따라감), `engine_openai_budget()` = 엔진 settings `api_month_limit_usd`. 경고 문구에 "엔진 자체 하루 상한, 계정 한도 아님" 표시. 13:10 타워 재시작.

## 시니어 자막 시간 맞춤 숫자 표기 (2026-11-18 사용자 "고쳐")
- 멈춘 회차: 미국 11/17 오후 기사 2(원고 "twenty-five thousand dollars", 인식 "$25,000" 등 + W-4V를 'Dambivi IV'로), 일본 11/07 오전(옛 형식 원고의 출처 날짜 "2026/11/05" vs 인식 2026年11月5日).
- 고침: `NewsSpeechAlignment.py` 두 곳(일본 `Downloads\SeniorNews_V28_INTEGRATED`, 미국 `C:\Users\user\SeniorNews\REGIONS\WEST\V28_WEST`) `_respell_heard` — 인식된 단어를 원고 표기로 바꿔 맞춤(원고에 바로 그 표기가 다음에 올 때만): 영어 숫자 말(쪼개진 "$25"+",000"도 합침, percent·dollars·hundred 꼴), "85"+percent, "ssa"+"gov"→dot gov, W→'Dambivi' 류, 로마 숫자 IV→4, 한 글자 빠진 약자(S B→SNB), 일본 년월일→빗금 날짜. 시간은 인식 그대로, 결과 words 는 원래 인식값, adjustments 에 기록.
- 시험: 저장된 정렬 68건 회귀 — 망가진 것 0, 새로 통과 7(미국 11/17 오후 기사 2·4·6, 일본 11/07 오전 기사 1 등). 숫자를 바꾼 원고(twenty-six·sixty percent·eighteen hundred·86 percent)는 계속 멈춤. 백업 `ControlTower\backups\20261118_1700_respell\`.
- 일본 11/07 오전 기사 4·5·6 은 옛 형식 원고(**메인타이틀**·출처 이름) 문제라 이어 만들기로는 안 풀림 → 새로 만들기 권장(사용자 결정 대기).
- 왜 안 잡혔나: 미국 11/17 오후는 12:45 장애 → 13:40 온콜이 W-4V 녹음 재확인(WestVoice)만 고치고 '숫자 검사 정상'으로 봄(숫자 말 표기 원인 놓침), 다시 만들기는 시니어 시간 대기열에서 대기. 일본 11/07 은 11/09·11/10 장애 1번씩 → 고치지 못한 채 닫힘, 타워 감시는 STATUS 가 바뀔 때만 알려 이후 9일 조용(노예1 대기열엔 11/17 들어감).
- 2026-11-18 사용자 "진행해": ① 일본 11/07 오전·오후 → 새로 만들기(STATUS.json project 비움, 옛 폴더는 old_project_kept, 백업 `backups\20261118_1700_respell\STATUS_JP_*`) → us_remake/노예1 대기열이 NEW 로 만듦. ② 노예2 `tower.py sn_runs_local`: 6시간 넘게 멈춘 최근 21일 회차를 "아직 멈춤 N일째 (노예1 대기열 있음/없음)"로 하루 한 번 다시 장애 기록(백업 tower.py.before_stale). ③ `ONCALL_PROCEDURE.md`: 못 고친 멈춘 회차는 cannot_fix 대신 need_approval(텔레그램 버튼)로, 같은 회차가 다시 오면 전 기록 보고 실패한 수리 반복 금지. 타워 재시작은 미국 11/17 오후 이어 만들기(16:48 시작) 끝난 뒤(19:00 예약).

## 컨트롤 판넬 과거뉴스 (2026-11-18 사용자 "과거뉴스도 멈춘 거 아니야? 판넬에 그렇게 나온다")
- 판넬이 옛 12단계 진행표(`_schedule/state.json`, 11/05 이후 안 씀)와 멈춘 옛 작업(tm_daily·tm_stock "정지 중")을 보여 주고 있었음 → 실제 제작(jeff 한국·일본, 노예1 미국 tm_backfill)은 안 보였음.
- 실제 문제: 미국 11/22·23·24 건너뜀(11/17 19:2x, 노예1 에 Cloudflare 열쇠 없음 + 사진 검사 15/15 실패), 미국 11/21 검사 보류(이야기 3 영상 조각 보류, clip_held [3]). 감시도 옛 진행표만 봐서 못 잡음.
- 고침: ① 노예1 `tm_backfill_state.json` 에서 11/22~24 SKIPPED 지움(백업 `.before_retry_20261118`) → 18:24 11/22 다시 제작 시작. ② jeff 의 Cloudflare 열쇠(HistoricalNews/CloudflareWorkersAI)를 임시 파일로 노예2 경유 노예1 에 넣고 파일 지움(값은 보지 않음). ③ 노예2 `station_status._hn`: tm_producing_<PC>.json 기준 방송일×국가 결과(완성·제작 중·검사 보류·건너뜀·아직 없음)·PC 상태·한/일/미 비축일, `console_ui` 문구. ④ `tower.py` tm_progress 감시: 앞 7일 검사 보류·건너뜀, 3일 안 방송인데 영상 없음, 40분 넘게 연락 없는 PC 알림(타워 재시작 후 적용, 19:00 예약). 백업 `ControlTower\backups\20261118_1830_hnpanel\`.
- 남은 것: 미국 11/21 검사 보류 처리 결정.
- 2026-11-18 19:40 남은 것 처리: 노예2 타워 재시작(19:40, tm_progress 새 감시 적용). jeff 판넬은 노예2 자료(station_status_n2)를 jeff `console_ui.py` 로 그림 → jeff console_ui 도 같은 문구로 고침(비축 한·일·미, 제작 PC 상태, 백업 `backups\20261118_1830_hnpanel\console_ui.py.jeff`), 화면 확인.
- 미국 11/21 검사 보류 원인 = 11/17 'GPT 사진 판정 하루 상한 4000원' 도달로 이야기 3 사진 1장을 못 봄(사진 문제 아님) → 이야기 3만 다시 검사 PASS, 원래 결과에 합침(백업 CLIP_QC.json.before_recheck_20261118), 상태 지워 다시 보냄 대기.
- 근본 고침(jeff·노예1 `tm_backfill.py`, 백업 `tm_backfill_backup_20261118_caphold.py`): AI 하루 상한으로만 HELD 된 날짜는 다음 날 `release_cap_holds` 가 풀고 `qc()` 가 그 이야기만 `clip_qc --only` 다시 검사해 합침(그날 상한은 우회 안 함). 진짜 사진 문제 보류(한국 11/13 등)는 그대로.
- 2026-11-18 20:00 사용자 "판넬에 과거뉴스 미국 11/01 검사 보류가 붉게": 원인 = 자막 검사 lead_punct — 이야기 2 자막이 "' Kay had spotted…" 로 시작. 나레이션 문장 나누기(`tm_documentary\narrate_v2.sentences`)가 영어 홑따옴표(')를 닫는 따옴표로 안 봐서 "…Mr. November!' Kay" 를 따옴표 앞에서 자름. 고침: 닫는 따옴표 묶음에 `'` 추가(jeff·노예1, 백업 `narrate_v2_backup_20261118_quote.py`, 한·일 문장 나누기 그대로 확인). 11/01 미국: 02_narration.json 문장 13 앞 따옴표를 문장 12 끝으로(백업 .before_quotefix), 이야기 2 영상·회차 묶음 옆으로 → tm_backfill 상태 RETRY(노예1이 그 이야기만 다시 만들고 검사).
- 2026-11-18 사용자 "그런 게 있는데 왜 자동복구에 안 걸리냐": ① 타워 과거뉴스 감시는 옛 진행표만 봤고(오늘 고침), 고친 감시도 앞 7일만 봐서 밀린 지난 회차(미국 11/01, 11/17부터 보류)는 여전히 못 봤음 → `tower.py` tm_progress 에 '지난 회차 검사 보류·건너뜀인데 유튜브에 안 올라간 것'(N일 지남, 하루 한 번) 추가, 19:55 재시작. ② 온콜 절차에 과거뉴스 보류 처리법이 없었음 → `ONCALL_PROCEDURE.md` 'Past news (TM) held / skipped editions' 절(원인 찾는 곳, 그 이야기만 고쳐 RETRY, 손 업로드 금지). ③ tm_backfill 은 돌 때 상태 파일을 메모리에 들고 있다가 덮어씀 → 11/21 풀어 준 것이 19:49 덮여 다시 HELD_QC. 도는 중엔 상태 파일을 고치지 말라는 줄 추가, 11/21 은 노예1 에서 지금 실행이 끝나면 자동으로 풀리게 걸어 둠(release1121.ps1, 끝나면 스스로 지워짐).
- 남은 차이: 노예1 tm_backfill 은 jeff 것보다 옛 판(release_caption_holds·release_crash_skips 없음).
