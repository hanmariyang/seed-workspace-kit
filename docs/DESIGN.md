# Workspace Starter Kit — 설계 문서 (v0)

> 처음 Claude Code 를 쓰는 사람이, **자기 업무에 맞는** 워크스페이스(디렉토리 · 에이전트 · 스킬 · 로컬 DB · md/html 산출물 뷰어)를 인터뷰 한 번으로 세팅하도록 돕는 부트스트랩 키트.
>
> 코드명: **Seed** (인터뷰로 씨앗을 심으면 워크스페이스가 자란다) — 확정 (2026-06-26).
> 배포 형태: **템플릿 git repo** — 확정 (2026-06-26).

---

## 0. 확정된 전제 (2026-06-26)

| 항목 | 결정 |
|---|---|
| 1차 대상 | **범용 (누구나)** — 회사·사내 도구 색 제거. 순수 개인 생산성 워크스페이스 |
| 로컬 DB | **SQLite 단일 파일** (`workspace.db`). 인프라 0, Docker 없음. Postgres 승격 경로만 열어둠 |
| 산출물 뷰어 | **정적 대시보드 기본** + 옵션 `--serve`. 더블클릭으로 열림, 의존성 0 |
| 이번 산출 | **설계 문서만** (코드 X) |

---

## 1. 핵심 원칙 — "복사가 아니라 인터뷰"

기성 워크스페이스를 통째로 복사시키면 신규 사용자의 업무와 안 맞아 방치된다.
키트의 본질은 **템플릿 배포가 아니라 인터뷰 기반 생성**이다.

```
사용자가 /onboard 실행
  → 6~8개 질문 인터뷰 (직무 · 도메인 · 반복 업무 · 산출물 형태 · 조력자 성향)
  → 답변을 변수로 받아 시드 파일을 채워 "맞춤 생성"
  → 첫 산출물 1개를 즉석에서 만들어 md+html 로 띄우며 "이렇게 돌아갑니다" 시연
```

마지막 **시연(first deliverable)** 이 설계의 핵심. 신규 사용자는 빈 구조를 받으면 못 쓴다.
첫 산출물이 브라우저에 뜨는 순간이 "아 이거구나" 하는 전환점.

### 설계 4원칙
1. **의존성 0 진입** — Python 표준 라이브러리(`sqlite3`)만으로 동작. `pip install` 없이 시작
2. **소스 + 렌더 동시 보존** — 모든 산출물은 `.md`(소스) + `.html`(렌더) 쌍으로 저장
3. **최소 골격** — 에이전트 1~2명, 코어 스킬 3개. 과설계 금지. 필요해지면 자란다
4. **승격 경로만 열어둠** — SQLite→Postgres, 정적→서버, 1인→다인 전환 문서만 남기고 강제 X

---

## 2. 생성되는 디렉토리 구조 — 원탁 × 카파시 혼합

두 계보를 합친다. **원탁**에서 운영 골격을, **카파시(LLM Wiki + 미니멀리즘)**에서 지식 보존 방식과 단순함을 가져온다.

```
my-workspace/
├── CLAUDE.md              # [원탁] 정체성·규칙·조력자 정의 (인터뷰로 자동 생성)
├── PROGRAM.md             # [카파시] 워크스페이스 "아이디어 파일" — 작동 원리 + 개선 로그.
│                          #          에이전트가 스스로 읽고 갱신하는 단일 지시서/캔버스
├── .claude/
│   ├── agents/            # [원탁] 인터뷰 기반 조력자 1~2명 (.md)
│   ├── skills/            # [원탁] /task · /deliver · /view 코어 스킬
│   └── settings.json      # 최소 설정 (권한 allowlist 시드)
├── workspace.db           # [상태] SQLite 단일 파일 — tasks·deliverables 메타 (구조화 상태)
├── wiki/                  # [카파시·지식] 플랫 마크다운 지식베이스. RAG 없음.
│   │                      #               git 버전관리, 어떤 LLM이든 그냥 읽음
│   ├── index.md           #   - 위키 목차 (한 줄 포인터, 원탁 MEMORY.md 식)
│   └── *.md               #   - 한 파일 = 한 주제. 쌓이는 지식은 전부 여기 평문으로
├── bin/                   # [카파시·미니멀] 단일 파일 도구. 의존성 0 우선
│   ├── ws.py              #   - DB 헬퍼 CLI (add/list/done/deliver/build)
│   └── render.py          #   - md → html 렌더러 + 대시보드 빌더
├── deliverables/          # [원탁] 산출물 (각 폴더에 slug.md + slug.html — 이중 저장)
│   ├── _dashboard.html    #   - 자동 생성 대시보드 (DB 스냅샷 임베드)
│   └── _assets/           #   - 공용 CSS (대시보드·산출물 공통 테마)
├── notes/inbox/           # [원탁] 분류 전 빠른 메모 (정제되면 wiki/ 로 승격)
└── archive/               # 완료/폐기
```

### 설계 핵심: 상태 ≠ 지식 (이중 보존의 분업)
- **상태(state)** = 변하는 구조화 데이터(업무·산출물 메타) → **SQLite**. 쿼리·집계·대시보드용
- **지식(knowledge)** = 쌓이는 텍스트(정책·결정 이유·배운 것) → **`wiki/*.md` 플랫 마크다운**. 카파시 원칙: *"평문 텍스트는 실패 모드가 거의 없고, 띄울 서비스가 필요 없고, git 으로 버전관리되며, 어떤 LLM이든 그냥 읽는다."*
- **흐름**: `notes/inbox/` 빠른 메모 → 정제 → `wiki/*.md` 지식 승격 → `wiki/index.md` 에 한 줄 포인터

### 핵심 비교 — 기성 풀스택 대비

| 기성(원탁류) | 키트(Seed) | 차용 계보 |
|---|---|---|
| Postgres+Redis+Docker 3컨테이너 | SQLite 1파일 | 카파시(미니멀) |
| 에이전트 4인 회의체 | 조력자 1~2명 | — (신규자엔 4인 과함) |
| projects/ 다수 | 단일 워크스페이스 | — |
| DB에 지식·상태 혼재 | **상태=DB / 지식=wiki 분리** | 카파시(LLM Wiki) |
| DB+파일 동시 저장 | **그대로 계승** | 원탁 |
| (없음) | **PROGRAM.md 아이디어 파일** | 카파시(program.md) |

---

### 명명 규약 — 기본값 (인터뷰에서 제안 → 확정)

폴더·파일·제목의 이름은 **기본값을 못박되**, `/onboard` 인터뷰에서 건축가가 이 기본값을 **제안하고 사용자가 확정/조정**한다(§7). 한번 정하면 워크스페이스 전체가 그 규약을 따른다 — `bin/ws.py` 가 강제한다.

| 대상 | 기본 패턴 | 예시 |
|---|---|---|
| 산출물 폴더 | `{PREFIX}-{id:03d}-{slug}` | `WS-007-3분기-보고서` |
| 산출물 파일 | `{slug}.md` · `{slug}.html` | `3분기-보고서.md` |
| wiki 지식 | `{topic-slug}.md` | `정산-정책.md` |
| 빠른 메모 | `{YYYY-MM-DD}-{slug}.md` | `2026-06-26-아이디어.md` |
| 대시보드 | `_dashboard.html` (고정) | — |
| 아카이브 | 원래 이름 유지 + `archive/` 이동 | — |

규칙(기본값):
- **PREFIX** — 워크스페이스 이름에서 2~3자 대문자. 인터뷰 7번(이름) 답에서 자동 제안. 원탁의 `HM-` 패턴 계승. *없음*도 선택 가능(숫자만)
- **id** — zero-pad 3자리, `tasks.id` 기반. 단조 증가 → 폴더가 시간순 정렬
- **slug** — kebab-case(하이픈 연결). **한글 유지가 기본**(macOS 안전, 의미 보존). 영문 slug 원하면 인터뷰에서 전환
- **날짜** — ISO `YYYY-MM-DD` 고정
- **제목(title)** — DB·문서 헤더에 들어가는 사람이 읽는 원문. slug 는 title 에서 자동 파생(아래 정규화)
- **slug 정규화** — 소문자화(영문) · 공백→하이픈 · 금지문자 `/ \ : * ? " < > |` 제거 · 연속 하이픈 1개로 축약 · 앞뒤 하이픈 제거

→ 인터뷰에서 건축가는 이 표를 **한 화면으로 제안**하고 "이대로 갈까요? / PREFIX·slug 언어만 바꿀까요?" 식의 **단일 확정 질문**으로 닫는다. 심문하지 않는다.

---

## 3. 로컬 DB — SQLite 스키마 (4 테이블)

`workspace.db`. 작게 시작, 컬럼 확장 여지만 둠.

```sql
-- 업무
CREATE TABLE tasks (
  id          INTEGER PRIMARY KEY,
  title       TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'todo',   -- todo | doing | done | dropped
  priority    INTEGER DEFAULT 2,              -- 1 high · 2 normal · 3 low
  domain      TEXT,                           -- 인터뷰에서 받은 사용자 도메인 태그
  created_at  TEXT NOT NULL,                  -- ISO8601 (앱에서 stamp)
  closed_at   TEXT
);

-- 산출물 (md+html 쌍의 메타)
CREATE TABLE deliverables (
  id          INTEGER PRIMARY KEY,
  task_id     INTEGER REFERENCES tasks(id),
  slug        TEXT NOT NULL UNIQUE,           -- 폴더/파일명
  title       TEXT NOT NULL,
  md_path     TEXT NOT NULL,
  html_path   TEXT NOT NULL,
  content     TEXT,                           -- 본문 사본 (DB 단독 조회용 — 동시 저장 패턴)
  created_at  TEXT NOT NULL
);

-- 빠른 메모
CREATE TABLE notes (
  id          INTEGER PRIMARY KEY,
  body        TEXT NOT NULL,
  tag         TEXT,
  created_at  TEXT NOT NULL
);

-- 결정 로그 (가벼운 의사결정 기록 — 선택적 사용)
CREATE TABLE decisions (
  id          INTEGER PRIMARY KEY,
  task_id     INTEGER REFERENCES tasks(id),
  summary     TEXT NOT NULL,
  rationale   TEXT,
  created_at  TEXT NOT NULL
);
```

설계 노트:
- **타임스탬프는 앱이 찍는다** (DB default 아님) — 워크플로 재현/이식성 위해 ISO8601 문자열 고정
- `deliverables.content` 사본 보존 = 기성 워크스페이스의 "DB+파일 동시 저장" 계승. 대시보드가 파일 못 읽어도 DB만으로 렌더 가능
- 외부키는 느슨하게(NULL 허용) — 업무 없이 막 만든 산출물도 허용

---

## 4. md/html 산출물 뷰어 (요청의 핵심)

### 기본 = 정적 대시보드 (서버 없음)
- 산출물 저장(`/deliver`) 시 3개 동시 발생:
  1. `deliverables/<slug>/<slug>.md` (소스)
  2. `deliverables/<slug>/<slug>.html` (렌더 — 공용 테마 CSS 인라인 임베드)
  3. `deliverables/_dashboard.html` **재생성** — DB의 tasks/deliverables 스냅샷을 HTML 테이블로 구워넣음
- 사용자는 **`_dashboard.html` 더블클릭** → 업무 목록 + 산출물 목록 → 클릭해 각 산출물 열람
- `file://` 로 열려야 하므로 대시보드는 **데이터를 임베드**(외부 fetch·DB 직접 읽기 X). 저장 시마다 새로 굽는 방식으로 신선도 유지

### 옵션 = 로컬 서버 (`/view --serve`)
- `python -m http.server` 한 줄로 `deliverables/` 서빙 → 더 쾌적한 브라우징
- 데이터는 동일. 진입은 어디까지나 정적이 디폴트

### 렌더 테마
- `deliverables/_assets/` 에 공용 CSS 1개. 산출물 HTML 과 대시보드가 같은 테마 공유
- 마크다운→HTML 변환은 표준 라이브러리 기반 경량 변환기 또는 단일 파일 의존성 1개(택1, 빌드 단계에서 결정). **의존성 0 우선**

### 승격 경로 (강제 X, 문서만)
정적 → 작은 Flask/FastAPI 대시보드(실시간 DB 조회·필터·검색) → 필요 시. 키트엔 안내만.

---

## 5. 에이전트 & 스킬 스캐폴딩

에이전트는 **두 종류**다. 역할이 정반대이므로 섞지 않는다.

### 5a. 건축 에이전트 — `workspace-architect` (키트 소속, 1회성)
- 워크스페이스를 **세우는** 에이전트. `/onboard` 를 운전(§6-A): 인터뷰 → 골격 생성 → first deliverable 시연 → 점화 후 물러난다
- **범용**이므로 원탁식 페르소나(하로·미야자키…)를 입히지 않는다. 중립·친근·간결한 안내자
- 키트에 1명 포함. 사용자가 매일 부르는 에이전트가 아니라 *최초 1회* 부르는 빌더
- 실제 정의: `projects/workspace-kit/agents/workspace-architect.md` (본 문서와 함께 생성)

### 5b. 조력 에이전트 — 인터뷰가 낳는 1~2명 (워크스페이스 소속, 상시)
- "어떤 성향의 조력자가 필요한가"를 인터뷰에서 물어 `.claude/agents/` 에 1~2명 생성
- 기성 워크스페이스의 4인 회의체는 **과함** → 신규자는 1명(범용 조력자)부터, 원하면 2명(예: 실행가 + 검토가)
- 생성된 agent.md 에 사용자 직무·도메인·톤을 주입. 이들이 `/deliver`(§6-B)를 매일 운전
- 건축가가 떠난 뒤 이들이 워크스페이스의 주민이 된다

### 코어 스킬 3종 (`.claude/skills/`)
| 스킬 | 역할 |
|---|---|
| `/task` | 업무 등록·조회·상태 변경 (`ws.py` 래핑) |
| `/deliver` | 산출물 생성 → md+html 동시 저장 → DB 기록 → 대시보드 재빌드 |
| `/view` | 대시보드 열기 (기본 정적, `--serve` 로 서버) |

스킬은 `bin/ws.py` / `bin/render.py` CLI 를 호출하는 얇은 래퍼. 로직은 CLI 에, 트리거는 스킬에.

---

## 6. 기본 파이프라인

원탁의 `/wontak`(분류→라우팅→실행→DB/파일 저장→리포트)을 신규자용으로 증류. **두 개의 파이프라인**만 둔다.

### 6-A. 온보딩 파이프라인 — `/onboard` (1회성, 워크스페이스 건축)
워크스페이스를 **처음 세우는** 흐름. `workspace-architect` 에이전트(§5b)가 운전.

```
1. 인터뷰   사용자에게 6~8문항을 한 번에 하나씩, 적응형으로 (§7)
2. 설계     답변 → 변수 셋 (직무·도메인·산출물형태·조력자수·톤·이름)
3. 생성     디렉토리 골격 + CLAUDE.md + PROGRAM.md + .claude/agents·skills + workspace.db 스키마
4. 시연     첫 업무 1개로 first deliverable 를 md+html 로 즉석 빌드
5. 점화     _dashboard.html 을 띄워 보여주며 "여기서 시작하세요" → 종료
```
- 멱등성: 이미 구축된 워크스페이스에서 재실행하면 **덮어쓰지 않고** 누락분만 보완(diff 모드)
- 산출: 빈 구조가 아니라 *이미 한 번 돌아간* 워크스페이스를 넘긴다 (4·5단계가 핵심)

### 6-B. 업무 파이프라인 — `/deliver` (반복, 일상 운영)
세팅 후 **매일 도는** 흐름. 조력자 에이전트가 운전.

```
1. Capture   요청을 tasks 에 등록 (id·domain·priority)
2. Route     유형 분류 → 어떤 조력자/스킬/템플릿을 쓸지 결정
3. Execute   조력자가 작업 수행
4. Persist   ┌ deliverables/<slug>/<slug>.md  (소스)
             ├ deliverables/<slug>/<slug>.html (렌더, 테마 임베드)
             ├ workspace.db  deliverables 행 + content 사본 (이중 저장)
             └ (지식이면) wiki/<topic>.md 갱신 + wiki/index.md 포인터
5. Report    _dashboard.html 재빌드 → 결과 링크 반환
```

두 파이프라인의 관계: `/onboard` 가 토양을 만들고, `/deliver` 가 그 위에서 반복해 자란다.
공통 규약 — **모든 산출은 (a) 이중 저장, (b) 저장 즉시 대시보드 재빌드, (c) 타임스탬프는 앱이 stamp.**

### 파이프라인 ↔ 구성요소 매핑

| 단계 | 호출 도구 | 기록 위치 |
|---|---|---|
| Capture | `bin/ws.py add` | `workspace.db` tasks |
| Execute | 조력자 agent | (작업 중) |
| Persist | `/deliver` → `ws.py deliver` + `render.py` | deliverables/ + DB + wiki/ |
| Report | `render.py build` | `_dashboard.html` |

---

## 7. 인터뷰 흐름 (`/onboard`)

6~8문항. 각 답이 생성물의 변수가 된다.

1. **직무/역할** — CLAUDE.md 정체성 + 도메인 태그 시드
2. **주요 도메인 1~3개** — `tasks.domain` 기본 태그 세트
3. **반복 업무 유형** — 코어 스킬 외 추가 스킬 후보 판단
4. **주 산출물 형태** (보고서 / 회의록 / 코드 / 슬라이드 …) — 렌더 테마·템플릿 결정
5. **조력자 인원/성향** (1명 범용 vs 2명 실행+검토) — agent 생성 수
6. **조력자 톤** (간결/친근/엄격) — agent.md 어투
7. **워크스페이스 이름** — 디렉토리·CLAUDE.md 제목 + **PREFIX 자동 도출**
8. **명명 규약 확정** — 7번 이름에서 PREFIX·기본 패턴을 **자동 제안**(§명명 규약 표)하고, "이대로 갈까요? PREFIX·slug 언어만 바꿀까요?"로 **단일 확정 질문**. 별도 심문 없음
9. **(선택) 첫 업무 1개** — 즉석 시연용 first deliverable 생성

→ 인터뷰 종료 시 구조 생성 + 첫 산출물을 md+html 로 빌드해 **대시보드를 띄워 보여주며** 온보딩 종료.

---

## 8. 빌드 로드맵 (다음 단계들)

| Phase | 내용 | 산출 |
|---|---|---|
| **P0** | 설계 문서 + 건축 에이전트 | ✅ 본 문서 · `agents/workspace-architect.md` |
| **P1** | 골격 + DB | ✅ `template/` 시드(+`wiki/`·`PROGRAM.md`·`seed.json`), `bin/ws.py` (init/add/list/start/done/deliver/build) |
| **P2** | 뷰어 | ✅ `bin/render.py` (stdlib md→html + 대시보드 빌더), `_assets/theme.css` |
| **P3** | 스킬 3종 | ✅ `/task` `/deliver`(6-B) `/view` (`template/.claude/skills/`) |
| **P4** | 온보딩 | ✅ `/onboard`(6-A) 스킬 + 템플릿 CLAUDE.md/PROGRAM.md `{{치환}}` 골격 |
| **P5** | 패키징 | ⏸ `template/` README·.gitignore 완료. **git init·repo 퍼블리시는 주인 확인 후** |

> **셀프 테스트 (2026-06-26)**: scratch 복제본에서 init→add→start→deliver→done→build 전 흐름 통과. md→html 변환(굵게·코드·표·링크), 대시보드 상대링크·통계·상태 배지 정상 렌더 확인.

---

## 9. 열린 질문 (P1 들어가기 전 정할 것)

1. ~~**코드명**~~ → **Seed 확정** (2026-06-26)
2. ~~**배포 형태**~~ → **템플릿 git repo 확정** (2026-06-26). `gh repo create --template` 로 새 워크스페이스 시작 → `/onboard` 로 맞춤화
3. **md→html 변환** — 의존성 0(표준 라이브러리 경량 변환) vs 단일 패키지 1개 허용(품질↑). 표 큰 거 다룰지에 따라 갈림
4. **타임스탬프 주입** — `ws.py` 가 `datetime.now()` 로 stamp (워크플로 재현 이슈 없는 일반 CLI 이므로 OK)
5. **시연 산출물 템플릿** — first deliverable 을 어떤 형태로 구울지 (간단 보고서 1장 권장)

---

*문서 위치: `projects/workspace-kit/DESIGN.md` · v0 · 2026-06-26*
