#!/usr/bin/env python3
"""Seed — md → html 렌더러 + 대시보드 빌더 (의존성 0, 표준 라이브러리만).

- md_to_html(text): 경량 마크다운 → HTML 본문 변환 (헤더/리스트/표/코드/인용/링크/강조)
- render_file(md, html, title): 산출물 .md 를 테마 입힌 .html 로
- build_dashboard(db, out): workspace.db 스냅샷을 정적 대시보드 HTML 로 (서버 불필요)

추후 더 풍부한 변환이 필요하면 `markdown` 패키지로 교체 가능 (DESIGN §9-3). 지금은 무의존이 기본.
"""
from __future__ import annotations
import html
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "deliverables" / "_assets" / "theme.css"

# 인라인 SVG 파비콘 (외부 파일 없이 자기완결 · file:// 더블클릭 대응). 🌱 새싹 마크.
FAVICON = (
    "<link rel=\"icon\" href=\"data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
    "%3Crect width='32' height='32' rx='8' fill='%2327a456'/%3E"
    "%3Cpath d='M16 26 V15.5' stroke='%23fff' stroke-width='2.6' stroke-linecap='round'/%3E"
    "%3Cpath d='M15.5 17.5 C10 17.8 6.6 14.6 6.4 9.6 C12 9.3 15.3 12.5 15.5 17.5 Z' fill='%23d7f4e1'/%3E"
    "%3Cpath d='M16.5 15.5 C21.4 14 24 10.2 23.2 5.6 C18.4 7 15.7 10.9 16.5 15.5 Z' fill='%23fff'/%3E"
    "%3C/svg%3E\">"
)

# ---------------------------------------------------------------- 테마 커스텀
# seed.json 의 theme.accent / theme.mode 로 대시보드·문서 색을 바꾼다.
# 각 액센트 = (라이트: seed, seed-d, seed-l | 다크: seed, seed-d, seed-l)
ACCENTS = {
    "green":  ("#27a456", "#1c8345", "#e7f6ec", "#3ecb72", "#7fe0a0", "#16291d"),
    "blue":   ("#2f7fe0", "#1f5fb8", "#e6eefb", "#5ea6f0", "#9cc6f6", "#16223a"),
    "violet": ("#7c5cd6", "#5f43b0", "#eee9fb", "#a48cec", "#c3b2f2", "#241a3a"),
    "teal":   ("#0e9e8e", "#0a7a6e", "#e0f5f2", "#3fc7b6", "#86ddd2", "#0f2b28"),
    "amber":  ("#d9820a", "#9c5f08", "#fbeecd", "#e6a53a", "#f0c67f", "#2c2110"),
    "rose":   ("#d6455c", "#b02f46", "#fbe6ea", "#f0748a", "#f4a6b3", "#2c1620"),
}
_DEFAULT_THEME = {"accent": "green", "mode": "light"}


def _theme_cfg() -> dict:
    cfg = ROOT / "seed.json"
    if cfg.exists():
        try:
            t = json.loads(cfg.read_text(encoding="utf-8")).get("theme", {})
            if isinstance(t, dict):
                return {**_DEFAULT_THEME, **t}
        except Exception:
            pass
    return dict(_DEFAULT_THEME)


def _accent_css(accent: str) -> str:
    """seed.json 액센트 → :root(라이트) + [data-theme=dark] 오버라이드 CSS."""
    a = ACCENTS.get(accent, ACCENTS["green"])
    return (
        f":root{{--seed:{a[0]};--seed-d:{a[1]};--seed-l:{a[2]}}}"
        f'[data-theme="dark"]{{--seed:{a[3]};--seed-d:{a[4]};--seed-l:{a[5]}}}'
    )


def _theme_init_js(default_mode: str) -> str:
    """플래시 없이 초기 data-theme 설정 (localStorage 우선, 없으면 seed.json mode)."""
    dm = "dark" if default_mode == "dark" else "light"
    return (
        "<script>(function(){var d='" + dm + "';"
        "try{var s=localStorage.getItem('seed-theme');if(s)d=s;}catch(e){}"
        "if(d==='dark')document.documentElement.dataset.theme='dark';})();</script>"
    )

# ---------------------------------------------------------------- inline
_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITAL = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _inline(text: str) -> str:
    text = html.escape(text)
    text = _CODE.sub(r"<code>\1</code>", text)
    text = _LINK.sub(r'<a href="\2">\1</a>', text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITAL.sub(r"<em>\1</em>", text)
    return text


# ---------------------------------------------------------------- blocks
def md_to_html(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]

        # fenced code
        if line.lstrip().startswith("```"):
            buf, i = [], i + 1
            while i < n and not lines[i].lstrip().startswith("```"):
                buf.append(html.escape(lines[i]))
                i += 1
            i += 1
            out.append("<pre><code>" + "\n".join(buf) + "</code></pre>")
            continue

        # blank
        if not line.strip():
            i += 1
            continue

        # heading
        m = re.match(r"(#{1,6})\s+(.*)", line)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{_inline(m.group(2).strip())}</h{lvl}>")
            i += 1
            continue

        # horizontal rule
        if re.match(r"^\s*([-*_])\1\1+\s*$", line):
            out.append("<hr>")
            i += 1
            continue

        # table  (header row | --- | rows)
        if line.lstrip().startswith("|") and i + 1 < n and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1]):
            head = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            th = "".join(f"<th>{_inline(c)}</th>" for c in head)
            trs = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>")
            continue

        # blockquote
        if line.lstrip().startswith(">"):
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(_inline(lines[i].lstrip()[1:].strip()))
                i += 1
            out.append("<blockquote>" + "<br>".join(buf) + "</blockquote>")
            continue

        # unordered / ordered list
        if re.match(r"^\s*([-*+]|\d+\.)\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.\s+", line))
            tag = "ol" if ordered else "ul"
            buf = []
            while i < n and re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i]):
                item = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", lines[i])
                buf.append(f"<li>{_inline(item)}</li>")
                i += 1
            out.append(f"<{tag}>" + "".join(buf) + f"</{tag}>")
            continue

        # paragraph (consume until blank)
        buf = []
        while i < n and lines[i].strip() and not re.match(r"^(#{1,6}\s|>|\s*([-*+]|\d+\.)\s|```)", lines[i]):
            buf.append(_inline(lines[i].strip()))
            i += 1
        out.append("<p>" + "<br>".join(buf) + "</p>")

    return "\n".join(out)


# ---------------------------------------------------------------- shell
def _theme() -> str:
    return THEME.read_text(encoding="utf-8") if THEME.exists() else ""


def _page(title: str, body: str, subtitle: str = "") -> str:
    sub = f'<p class="sub">{html.escape(subtitle)}</p>' if subtitle else ""
    tc = _theme_cfg()
    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
{FAVICON}
<style>{_theme()}</style><style>{_accent_css(tc["accent"])}</style>
{_theme_init_js(tc["mode"])}</head>
<body><div class="wrap">
<header class="doc-head"><h1>{html.escape(title)}</h1>{sub}</header>
<main class="doc">{body}</main>
<footer class="doc-foot">🌱 Seed · generated</footer>
</div></body></html>"""


def render_file(md_path: Path, html_path: Path, title: str, subtitle: str = "") -> None:
    body = md_to_html(Path(md_path).read_text(encoding="utf-8"))
    Path(html_path).write_text(_page(title, body, subtitle), encoding="utf-8")


# ---------------------------------------------------------------- dashboard
_STATUS_KO = {"todo": "대기", "doing": "진행", "done": "완료", "dropped": "폐기"}
_PRIO = {1: ("높음", "p-hi"), 2: ("보통", "p-mid"), 3: ("낮음", "p-lo")}

DASH_JS = """
<script>
(function(){
  // 테마 토글 (라이트↔다크, localStorage 저장)
  var tt=document.getElementById('tt'), root=document.documentElement;
  function syncTt(){ if(tt) tt.textContent=(root.dataset.theme==='dark')?'☀️':'🌙'; }
  syncTt();
  if(tt) tt.addEventListener('click',function(){
    var dark=root.dataset.theme==='dark';
    if(dark) delete root.dataset.theme; else root.dataset.theme='dark';
    try{ localStorage.setItem('seed-theme', dark?'light':'dark'); }catch(e){}
    syncTt();
  });

  var q=document.getElementById('q'), state='all';
  function vis(){
    var term=(q.value||'').trim().toLowerCase();
    document.querySelectorAll('table.grid').forEach(function(tb){
      var shown=0, rows=tb.querySelectorAll('tbody tr');
      rows.forEach(function(tr){
        if(tr.classList.contains('empty'))return;
        var txt=(tr.dataset.text||tr.textContent).toLowerCase();
        var st=tr.dataset.status;
        var okT=!term||txt.indexOf(term)>-1;
        var okS=(state==='all')||(st===undefined)||(st===state);
        var show=okT&&okS; tr.style.display=show?'':'none'; if(show)shown++;
      });
      var c=tb.parentNode.querySelector('h2 .count'); if(c)c.textContent=shown;
      var empty=tb.querySelector('tr.empty'); if(empty)empty.style.display=shown?'none':'';
    });
  }
  q.addEventListener('input',vis);
  document.querySelectorAll('#statusFilter .chip').forEach(function(ch){
    ch.addEventListener('click',function(){
      document.querySelectorAll('#statusFilter .chip').forEach(function(x){x.classList.remove('on');});
      ch.classList.add('on'); state=ch.dataset.st; vis();
    });
  });
  document.querySelectorAll('table.grid thead th.s').forEach(function(th){
    th.addEventListener('click',function(){
      var table=th.closest('table'), tbody=table.querySelector('tbody');
      var idx=Array.prototype.indexOf.call(th.parentNode.children,th);
      var type=th.dataset.type||'text', asc=!th.classList.contains('asc');
      table.querySelectorAll('th').forEach(function(h){h.classList.remove('asc','desc');});
      th.classList.add(asc?'asc':'desc');
      var rows=Array.prototype.slice.call(tbody.querySelectorAll('tr')).filter(function(r){return !r.classList.contains('empty');});
      rows.sort(function(a,b){
        var av=a.children[idx].dataset.v, bv=b.children[idx].dataset.v;
        av=(av!==undefined)?av:a.children[idx].textContent.trim();
        bv=(bv!==undefined)?bv:b.children[idx].textContent.trim();
        if(type==='num'){return asc?(av-bv):(bv-av);}
        return asc?String(av).localeCompare(String(bv),'ko'):String(bv).localeCompare(String(av),'ko');
      });
      rows.forEach(function(r){tbody.appendChild(r);});
    });
  });
  vis();
})();
</script>
"""


def _wsname() -> str:
    cfg = ROOT / "seed.json"
    if cfg.exists():
        try:
            return json.loads(cfg.read_text(encoding="utf-8")).get("name", "Workspace")
        except Exception:
            pass
    return "Workspace"


def _parse_ts(s: str):
    for fmt, ln in (("%Y-%m-%dT%H:%M:%S", 19), ("%Y-%m-%d", 10)):
        try:
            return datetime.strptime(s[:ln], fmt)
        except Exception:
            continue
    return None


def growth_line(db_path: Path) -> str:
    """성장 나이테 — created_at 타임스탬프를 읽어 워크스페이스가 자란 이야기 한 줄로.
    차트·그래프 없이 문장만 (원탁 6회차 절제선). 새 데이터·표면 0, 읽기 전용."""
    con = sqlite3.connect(str(db_path))

    def stamps(table):
        try:
            return [r[0] for r in con.execute(f"SELECT created_at FROM {table}").fetchall() if r[0]]
        except sqlite3.OperationalError:
            return []

    ts = stamps("tasks") + stamps("deliverables") + stamps("decisions") + stamps("notes")
    d_n = con.execute("SELECT COUNT(*) FROM deliverables").fetchone()[0]
    try:
        dec_n = con.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    except sqlite3.OperationalError:
        dec_n = 0
    con.close()
    wiki_dir = db_path.parent / "wiki"
    k_n = len(list(wiki_dir.glob("*.md"))) if wiki_dir.exists() else 0

    dts = [d for d in (_parse_ts(s) for s in ts) if d]
    if not dts:
        return "🌱 방금 심어진 워크스페이스입니다 — 첫 씨앗을 심어보세요."

    age = (datetime.now() - min(dts)).days
    grew = []
    if d_n:
        grew.append(f"산출물 {d_n}")
    if k_n:
        grew.append(f"지식 {k_n}")
    if dec_n:
        grew.append(f"결정 {dec_n}")
    grew_s = "·".join(grew) if grew else "첫 자람을 기다리는 중"
    age_s = "오늘 심었어요" if age == 0 else f"심은 지 {age}일째"

    busy = ""
    (by, bw), bc = Counter(d.isocalendar()[:2] for d in dts).most_common(1)[0]
    if bc >= 3:
        mon = date.fromisocalendar(by, bw, 1)
        busy = f" 가장 바빴던 주는 {mon.month}월 {mon.day}일 주간이었어요."
    return f"🌱 이 워크스페이스는 {age_s} — {grew_s} 만큼 자랐습니다.{busy}"


def _checkup_chip(db_path: Path, deliv_count: int) -> str:
    """재문진 시점이면 대시보드에 조용한 칩 하나(수동 신호). 강제 X — 권유만."""
    cfgp = db_path.parent / "seed.json"
    if not cfgp.exists():
        return ""
    try:
        c = json.loads(cfgp.read_text(encoding="utf-8"))
    except Exception:
        return ""
    last = c.get("last_checkup")
    if not last:
        due = deliv_count >= 8
    else:
        try:
            days = (datetime.now() - datetime.strptime(last[:10], "%Y-%m-%d")).days
        except Exception:
            days = 0
        due = days >= 30 or (deliv_count - c.get("last_checkup_deliv", 0)) >= 15
    return '<span class="stamp" style="opacity:1">🌱 재문진 권장 · <code>/checkup</code></span>' if due else ""


def build_dashboard(db_path: Path, out_path: Path) -> None:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    tasks = con.execute(
        "SELECT id,title,status,priority,domain,created_at FROM tasks ORDER BY id DESC"
    ).fetchall()
    delivs = con.execute(
        "SELECT id,task_id,slug,title,html_path,created_at FROM deliverables ORDER BY id DESC"
    ).fetchall()
    dec_n = con.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    con.close()
    # 지식(wiki) 수는 파일에서 파생 — 별도 저장 없음
    wiki_dir = db_path.parent / "wiki"
    know_n = len(list(wiki_dir.glob("*.md"))) if wiki_dir.exists() else 0

    doing_n = sum(1 for t in tasks if t["status"] == "doing")
    open_n = sum(1 for t in tasks if t["status"] in ("todo", "doing"))
    done_n = sum(1 for t in tasks if t["status"] == "done")
    total_n = len(tasks)
    pct = round(done_n * 100 / total_n) if total_n else 0

    def esc(x):
        return html.escape(str(x or ""), quote=True)

    def trow(t):
        st = t["status"]
        plabel, pcls = _PRIO.get(t["priority"], ("보통", "p-mid"))
        dom = t["domain"] or ""
        domcell = f'<span class="dtag">{esc(dom)}</span>' if dom else ""
        text = f'{t["title"]} {dom} {_STATUS_KO.get(st, st)}'
        return (
            f'<tr data-status="{esc(st)}" data-text="{esc(text)}">'
            f'<td class="id" data-v="{t["id"]}">#{t["id"]:03d}</td>'
            f'<td class="ttl">{esc(t["title"])}</td>'
            f'<td><span class="badge b-{esc(st)}">{esc(_STATUS_KO.get(st, st))}</span></td>'
            f'<td data-v="{t["priority"] or 2}"><span class="prio {pcls}">{plabel}</span></td>'
            f'<td data-v="{esc(dom)}">{domcell}</td>'
            f'<td class="dim">{esc((t["created_at"] or "")[:10])}</td></tr>'
        )

    def drow(d):
        return (
            f'<tr data-text="{esc(d["title"]+" "+d["slug"])}">'
            f'<td class="id" data-v="{d["id"]}">#{d["id"]:03d}</td>'
            f'<td><a href="{esc(_rel(d["html_path"], out_path))}">{esc(d["title"])}</a></td>'
            f'<td class="dim">{esc(d["slug"])}</td>'
            f'<td class="dim">{esc((d["created_at"] or "")[:10])}</td></tr>'
        )

    trows = "".join(trow(t) for t in tasks) or '<tr class="empty"><td colspan="6">아직 업무가 없습니다 — <code>ws.py add</code></td></tr>'
    drows = "".join(drow(d) for d in delivs) or '<tr class="empty"><td colspan="4">아직 산출물이 없습니다 — <code>ws.py deliver</code></td></tr>'
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    body = f"""<div class="dash">
<header class="dash-head">
  <span class="brand">🌱 {esc(_wsname())}</span>
  <h1>대시보드</h1>
  <button class="ttog" id="tt" title="라이트/다크 전환" aria-label="테마 전환">🌙</button>
  {_checkup_chip(db_path, len(delivs))}
  <span class="stamp">최종 빌드 {stamp}</span>
</header>
<section class="stats">
  <div class="stat"><div class="num">{total_n}</div><div class="lab">전체 업무</div></div>
  <div class="stat s-doing"><div class="num">{doing_n}</div><div class="lab">진행 중</div></div>
  <div class="stat s-done"><div class="num">{done_n}<small>· {pct}%</small></div><div class="lab">완료</div></div>
  <div class="stat s-deliv"><div class="num">{len(delivs)}</div><div class="lab">산출물</div></div>
  <div class="stat"><div class="num">{dec_n}</div><div class="lab">결정</div></div>
  <div class="stat"><div class="num">{know_n}</div><div class="lab">지식</div></div>
</section>
<div class="toolbar">
  <input id="q" class="search" type="search" placeholder="제목·도메인·slug 검색…" autocomplete="off">
  <div class="chips" id="statusFilter">
    <button class="chip on" data-st="all">전체</button>
    <button class="chip" data-st="todo">대기</button>
    <button class="chip" data-st="doing">진행</button>
    <button class="chip" data-st="done">완료</button>
  </div>
</div>
<section>
  <h2>📋 업무 <span class="count"></span></h2>
  <table class="grid"><thead><tr>
    <th class="s" data-type="num">ID</th><th class="s">제목</th><th class="s">상태</th>
    <th class="s" data-type="num">우선</th><th class="s">도메인</th><th class="s">생성</th>
  </tr></thead><tbody>{trows}</tbody></table>
</section>
<section>
  <h2>📄 산출물 <span class="count"></span></h2>
  <table class="grid"><thead><tr>
    <th class="s" data-type="num">ID</th><th class="s">제목</th><th class="s">slug</th><th class="s">생성</th>
  </tr></thead><tbody>{drows}</tbody></table>
</section>
<footer class="dash-foot">{esc(growth_line(db_path))}<br><span style="opacity:.55">Seed · 더블클릭으로 열리는 정적 대시보드 (서버 불필요)</span></footer>
</div>"""

    tc = _theme_cfg()
    page = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(_wsname())} · 대시보드</title>
{FAVICON}
<style>{_theme()}</style><style>{_accent_css(tc["accent"])}</style>
{_theme_init_js(tc["mode"])}</head>
<body>{body}{DASH_JS}</body></html>"""
    Path(out_path).write_text(page, encoding="utf-8")


def _rel(target: str, base_file: Path) -> str:
    """대시보드 파일 기준 상대경로 (file:// 더블클릭 대응)."""
    try:
        return str(Path(target).resolve().relative_to(Path(base_file).resolve().parent))
    except ValueError:
        import os
        return os.path.relpath(Path(target).resolve(), Path(base_file).resolve().parent)


if __name__ == "__main__":  # 단독 실행 시 대시보드만 재빌드
    import sys
    db = ROOT / "workspace.db"
    out = ROOT / "deliverables" / "_dashboard.html"
    if not db.exists():
        sys.exit("workspace.db 없음 — 먼저 `python bin/ws.py init`")
    build_dashboard(db, out)
    print(f"대시보드 빌드 → {out}")
