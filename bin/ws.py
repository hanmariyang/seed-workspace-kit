#!/usr/bin/env python3
"""Seed — 워크스페이스 DB 헬퍼 CLI (의존성 0, 표준 라이브러리만).

명령:
  init                      workspace.db 생성 + 디렉토리 보장
  add  "제목" [--domain D] [--priority 1|2|3]      업무 등록 → id 출력
  list [--status todo|doing|done|dropped|all]      업무 목록
  done <id>                                        업무 완료
  start <id>                                       업무 진행중(doing)
  note ["메모"] [--tag T]                           빠른 메모 기록 · 인자 없으면 최근 목록
  decide ["결정"] [--why 이유] [--task ID]          결정 기록 · 인자 없으면 최근 목록
  promote <note_id> [--topic S] [--title T]        메모를 wiki/*.md 지식으로 승격 (DB→md 단방향)
  search "검색어" [--limit N]                        업무·메모·결정·산출물·wiki 통합 검색
  deliver "제목" [--task ID] [--from FILE] [--template NAME] [--slug S]   산출물 생성 (md+html+DB) + 대시보드 재빌드
  templates                                        산출물 유형 템플릿 목록
  build                                            대시보드만 재빌드
  view                                             대시보드를 기본 브라우저로 열기 (mac/linux/win 자동)

명명 규약은 seed.json 이 강제한다 (PREFIX / id_pad / slug_lang).
Python 3.8+ (표준 라이브러리만).
"""
from __future__ import annotations
import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402  (같은 bin/ 디렉토리)

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "workspace.db"
CONFIG = ROOT / "seed.json"
DELIV = ROOT / "deliverables"
DASH = DELIV / "_dashboard.html"
WIKI = ROOT / "wiki"
TEMPLATES = ROOT / "templates"

DEFAULT_CONFIG = {
    "name": "My Workspace", "prefix": "WS", "id_pad": 3, "slug_lang": "ko",
    # 대시보드/문서 테마 — accent: green|blue|violet|teal|amber|rose · mode: light|dark
    "theme": {"accent": "green", "mode": "light"},
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY, title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'todo', priority INTEGER DEFAULT 2,
  domain TEXT, created_at TEXT NOT NULL, closed_at TEXT);
CREATE TABLE IF NOT EXISTS deliverables (
  id INTEGER PRIMARY KEY, task_id INTEGER REFERENCES tasks(id),
  slug TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
  md_path TEXT NOT NULL, html_path TEXT NOT NULL, content TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS notes (
  id INTEGER PRIMARY KEY, body TEXT NOT NULL, tag TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY, task_id INTEGER REFERENCES tasks(id),
  summary TEXT NOT NULL, rationale TEXT, created_at TEXT NOT NULL);
"""

_FORBIDDEN = re.compile(r'[/\\:*?"<>|]')


def now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def cfg() -> dict:
    if CONFIG.exists():
        return {**DEFAULT_CONFIG, **json.loads(CONFIG.read_text(encoding="utf-8"))}
    return dict(DEFAULT_CONFIG)


def slugify(text: str, lang: str = "ko") -> str:
    """명명 규약: 공백→하이픈, 금지문자 제거, 연속 하이픈 축약. ko=한글 유지, en=ASCII 소문자."""
    s = _FORBIDDEN.sub("", text).strip()
    s = re.sub(r"\s+", "-", s)
    if lang == "en":
        s = re.sub(r"[^A-Za-z0-9\-]", "", s).lower()
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "untitled"


def db() -> sqlite3.Connection:
    if not DB.exists():
        sys.exit("workspace.db 없음 — 먼저 `python bin/ws.py init`")
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    return con


# ---------------------------------------------------------------- commands
def cmd_init(_):
    for d in (DELIV / "_assets", WIKI, TEMPLATES, ROOT / "notes" / "inbox", ROOT / "archive"):
        d.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB))
    con.executescript(SCHEMA)
    con.commit()
    con.close()
    if not CONFIG.exists():
        CONFIG.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")
    render.build_dashboard(DB, DASH)
    print(f"✅ init 완료 — {DB.name}, seed.json, 대시보드")


def cmd_add(a):
    con = db()
    cur = con.execute(
        "INSERT INTO tasks(title,status,priority,domain,created_at) VALUES(?,?,?,?,?)",
        (a.title, "todo", a.priority, a.domain, now()),
    )
    con.commit()
    tid = cur.lastrowid
    con.close()
    print(f"➕ #{tid:0{cfg()['id_pad']}d}  {a.title}")


def _set_status(tid: int, status: str):
    con = db()
    closed = now() if status in ("done", "dropped") else None
    con.execute("UPDATE tasks SET status=?, closed_at=? WHERE id=?", (status, closed, tid))
    con.commit()
    n = con.total_changes
    con.close()
    if not n:
        sys.exit(f"#{tid} 없음")


def cmd_done(a):
    _set_status(a.id, "done")
    render.build_dashboard(DB, DASH)
    print(f"✔ #{a.id} 완료")


def cmd_start(a):
    _set_status(a.id, "doing")
    render.build_dashboard(DB, DASH)
    print(f"▶ #{a.id} 진행중")


def cmd_list(a):
    con = db()
    if a.status == "all":
        rows = con.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
    else:
        rows = con.execute("SELECT * FROM tasks WHERE status=? ORDER BY id DESC", (a.status,)).fetchall()
    con.close()
    if not rows:
        print("(없음)")
        return
    pad = cfg()["id_pad"]
    mark = {"todo": "○", "doing": "◐", "done": "●", "dropped": "✕"}
    for r in rows:
        dom = f"  [{r['domain']}]" if r["domain"] else ""
        print(f"{mark.get(r['status'],' ')} #{r['id']:0{pad}d}  {r['title']}{dom}")


def cmd_deliver(a):
    c = cfg()
    con = db()
    # 다음 deliverable id 예측 → 폴더명 = PREFIX-NNN-slug
    nxt = (con.execute("SELECT COALESCE(MAX(id),0)+1 FROM deliverables").fetchone()[0])
    slug = a.slug or slugify(a.title, c["slug_lang"])
    folder_name = f"{c['prefix']}-{nxt:0{c['id_pad']}d}-{slug}" if c["prefix"] else f"{nxt:0{c['id_pad']}d}-{slug}"
    folder = DELIV / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    md_path = folder / f"{slug}.md"
    html_path = folder / f"{slug}.html"

    # 본문 우선순위: --from 파일 > --template 골격 > stdin > 스텁
    if a.from_:
        content = Path(a.from_).read_text(encoding="utf-8")
    elif a.template:
        tp = TEMPLATES / f"{a.template}.md"
        if not tp.exists():
            avail = ", ".join(sorted(p.stem for p in TEMPLATES.glob("*.md") if p.stem != "README")) if TEMPLATES.exists() else ""
            con.close()
            sys.exit(f"템플릿 '{a.template}' 없음 — 사용 가능: {avail or '(없음)'}  (목록: python bin/ws.py templates)")
        content = _fill_template(tp.read_text(encoding="utf-8"), a.title)
    elif not sys.stdin.isatty():
        content = sys.stdin.read()
    else:
        content = f"# {a.title}\n\n_여기에 내용을 작성하세요._\n"
    md_path.write_text(content, encoding="utf-8")
    render.render_file(md_path, html_path, a.title, subtitle=folder_name)

    con.execute(
        "INSERT INTO deliverables(task_id,slug,title,md_path,html_path,content,created_at) VALUES(?,?,?,?,?,?,?)",
        (a.task, slug, a.title, str(md_path), str(html_path), content, now()),
    )
    con.commit()
    con.close()
    render.build_dashboard(DB, DASH)
    print(f"📄 {folder_name}")
    print(f"   md   {md_path.relative_to(ROOT)}")
    print(f"   html {html_path.relative_to(ROOT)}")
    print(f"   ↻ 대시보드 재빌드 → {DASH.relative_to(ROOT)}")


def cmd_note(a):
    con = db()
    if not a.text:  # 조회 모드 — 인자 없이 호출하면 최근 메모
        rows = con.execute("SELECT * FROM notes ORDER BY id DESC LIMIT ?", (a.limit,)).fetchall()
        con.close()
        if not rows:
            print('(메모 없음) — `python bin/ws.py note "메모 내용"` 로 기록')
            return
        for r in rows:
            tag = f"  #{r['tag']}" if r["tag"] else ""
            print(f"📝 #{r['id']}  {r['body']}{tag}  ({r['created_at'][:10]})")
        return
    cur = con.execute("INSERT INTO notes(body,tag,created_at) VALUES(?,?,?)", (a.text, a.tag, now()))
    con.commit()
    nid = cur.lastrowid
    con.close()
    print(f"📝 note #{nid} 기록")


def cmd_decide(a):
    con = db()
    if not a.text:  # 조회 모드
        rows = con.execute("SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (a.limit,)).fetchall()
        con.close()
        if not rows:
            print('(결정 없음) — `python bin/ws.py decide "결정" --why "이유"` 로 기록')
            return
        for r in rows:
            tsk = f"  [task #{r['task_id']}]" if r["task_id"] else ""
            print(f"⚖ #{r['id']}  {r['summary']}{tsk}  ({r['created_at'][:10]})")
            if r["rationale"]:
                print(f"     ↳ {r['rationale']}")
        return
    if a.task is not None and not con.execute("SELECT 1 FROM tasks WHERE id=?", (a.task,)).fetchone():
        con.close()
        sys.exit(f"task #{a.task} 없음")
    cur = con.execute(
        "INSERT INTO decisions(task_id,summary,rationale,created_at) VALUES(?,?,?,?)",
        (a.task, a.text, a.why, now()),
    )
    con.commit()
    did = cur.lastrowid
    con.close()
    print(f"⚖ decision #{did} 기록")


def cmd_promote(a):
    """메모(임시 상태) → wiki/*.md(영속 지식). 단방향: 승격하면 notes 에서 이동한다."""
    con = db()
    row = con.execute("SELECT * FROM notes WHERE id=?", (a.id,)).fetchone()
    if not row:
        con.close()
        sys.exit(f"note #{a.id} 없음")
    topic = a.topic or slugify(a.title or row["body"][:40], cfg()["slug_lang"])
    WIKI.mkdir(parents=True, exist_ok=True)
    path = WIKI / f"{topic}.md"
    new = not path.exists()
    tag = f" `#{row['tag']}`" if row["tag"] else ""
    with path.open("a", encoding="utf-8") as f:
        if new:
            f.write(f"# {a.title or topic}\n\n")
        f.write(f"- {row['body']}{tag} — _메모 #{row['id']}, {row['created_at'][:10]}_\n")
    con.execute("DELETE FROM notes WHERE id=?", (a.id,))
    con.commit()
    con.close()
    print(f"📖 note #{a.id} → {path.relative_to(ROOT)}  ({'새 지식 문서' if new else '기존 문서에 추가'})")
    print("   메모가 wiki 지식으로 승격되어 notes 에서 이동했습니다.")


def _trunc(s: str, n: int = 78) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def cmd_search(a):
    """DB(업무·메모·결정·산출물) + 파일(wiki·산출물 본문) 통합 검색. 색인 없이 즉석 grep."""
    term = a.term
    like = f"%{term}%"
    lim = a.limit
    con = db()
    tasks = con.execute("SELECT * FROM tasks WHERE title LIKE ? ORDER BY id DESC LIMIT ?", (like, lim)).fetchall()
    notes = con.execute("SELECT * FROM notes WHERE body LIKE ? ORDER BY id DESC LIMIT ?", (like, lim)).fetchall()
    decs = con.execute(
        "SELECT * FROM decisions WHERE summary LIKE ? OR rationale LIKE ? ORDER BY id DESC LIMIT ?",
        (like, like, lim),
    ).fetchall()
    delivs = con.execute("SELECT * FROM deliverables WHERE title LIKE ? ORDER BY id DESC LIMIT ?", (like, lim)).fetchall()
    con.close()

    def scan(base: Path):
        hits = []
        if not base.exists():
            return hits
        for p in sorted(base.rglob("*.md")):
            try:
                for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                    if term.lower() in line.lower():
                        hits.append((p, i, line.strip()))
                        if len(hits) >= lim:
                            return hits
            except Exception:
                continue
        return hits

    wiki_hits = scan(WIKI)
    deliv_hits = scan(DELIV)

    total = len(tasks) + len(notes) + len(decs) + len(delivs) + len(wiki_hits) + len(deliv_hits)
    mark = {"todo": "○", "doing": "◐", "done": "●", "dropped": "✕"}
    print(f'🔎 "{term}" 검색 결과')
    if not total:
        print("  (검색 결과 없음)")
        return
    if tasks:
        print("\n[업무]")
        for r in tasks:
            print(f"  {mark.get(r['status'],' ')} #{r['id']}  {_trunc(r['title'])}")
    if notes:
        print("\n[메모]")
        for r in notes:
            print(f"  📝 #{r['id']}  {_trunc(r['body'])}")
    if decs:
        print("\n[결정]")
        for r in decs:
            print(f"  ⚖ #{r['id']}  {_trunc(r['summary'])}")
    if delivs:
        print("\n[산출물]")
        for r in delivs:
            print(f"  📄 #{r['id']}  {_trunc(r['title'])}")
    if wiki_hits:
        print("\n[wiki]")
        for p, i, line in wiki_hits:
            print(f"  📖 {p.relative_to(ROOT)}:{i}  {_trunc(line)}")
    if deliv_hits:
        print("\n[산출물 본문]")
        for p, i, line in deliv_hits:
            print(f"  📄 {p.relative_to(ROOT)}:{i}  {_trunc(line)}")
    print(f"\n총 {total}건")


def _fill_template(text: str, title: str) -> str:
    """템플릿의 desc 주석 첫 줄을 걷어내고 {{title}}·{{date}} 치환."""
    lines = text.splitlines()
    if lines and lines[0].startswith("<!--") and "desc:" in lines[0]:
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    body = "\n".join(lines).replace("{{title}}", title).replace("{{date}}", now()[:10])
    return body if body.endswith("\n") else body + "\n"


def cmd_templates(_):
    mds = sorted(p for p in TEMPLATES.glob("*.md") if p.stem != "README") if TEMPLATES.exists() else []
    if not mds:
        print("(템플릿 없음) — templates/<이름>.md 로 추가할 수 있습니다")
        return
    print('📑 산출물 템플릿 — `deliver "제목" --template <이름>`\n')
    for p in mds:
        first = p.read_text(encoding="utf-8").splitlines()[:1]
        desc = first[0].split("desc:", 1)[1].replace("-->", "").strip() if first and "desc:" in first[0] else ""
        print(f"  · {p.stem:<12} {desc}")
    print("\n  새 템플릿은 templates/<이름>.md 로 추가 — {{title}}·{{date}} 가 치환됩니다.")


def cmd_build(_):
    render.build_dashboard(DB, DASH)
    print(f"↻ 대시보드 빌드 → {DASH.relative_to(ROOT)}")


def _open(path: Path) -> None:
    """파일을 OS 기본 앱으로 연다 — mac(open)·windows(startfile)·linux(xdg-open) 자동."""
    import subprocess, os
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        elif os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]  # Windows 전용
        else:  # linux / 기타 유닉스
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as e:
        print(f"자동 열기 실패 — 아래 파일을 직접 여세요:\n  {path}\n  ({e})")


def cmd_view(_):
    if not DASH.exists():
        render.build_dashboard(DB, DASH)
    print(f"🌱 대시보드 열기 → {DASH.relative_to(ROOT)}")
    _open(DASH)


# ---------------------------------------------------------------- argparse
def main():
    p = argparse.ArgumentParser(prog="ws", description="Seed 워크스페이스 DB 헬퍼")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init").set_defaults(fn=cmd_init)

    pa = sub.add_parser("add"); pa.add_argument("title")
    pa.add_argument("--domain"); pa.add_argument("--priority", type=int, default=2, choices=[1, 2, 3])
    pa.set_defaults(fn=cmd_add)

    pl = sub.add_parser("list")
    pl.add_argument("--status", default="all", choices=["todo", "doing", "done", "dropped", "all"])
    pl.set_defaults(fn=cmd_list)

    pd = sub.add_parser("done"); pd.add_argument("id", type=int); pd.set_defaults(fn=cmd_done)
    ps = sub.add_parser("start"); ps.add_argument("id", type=int); ps.set_defaults(fn=cmd_start)

    pn = sub.add_parser("note"); pn.add_argument("text", nargs="?")
    pn.add_argument("--tag"); pn.add_argument("--limit", type=int, default=10)
    pn.set_defaults(fn=cmd_note)

    pde = sub.add_parser("decide"); pde.add_argument("text", nargs="?")
    pde.add_argument("--why", dest="why"); pde.add_argument("--task", type=int)
    pde.add_argument("--limit", type=int, default=10)
    pde.set_defaults(fn=cmd_decide)

    pp = sub.add_parser("promote"); pp.add_argument("id", type=int)
    pp.add_argument("--topic"); pp.add_argument("--title")
    pp.set_defaults(fn=cmd_promote)

    pse = sub.add_parser("search"); pse.add_argument("term")
    pse.add_argument("--limit", type=int, default=10)
    pse.set_defaults(fn=cmd_search)

    pv = sub.add_parser("deliver"); pv.add_argument("title")
    pv.add_argument("--task", type=int); pv.add_argument("--from", dest="from_")
    pv.add_argument("--template", "-t"); pv.add_argument("--slug")
    pv.set_defaults(fn=cmd_deliver)

    sub.add_parser("templates").set_defaults(fn=cmd_templates)
    sub.add_parser("build").set_defaults(fn=cmd_build)
    sub.add_parser("view").set_defaults(fn=cmd_view)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
