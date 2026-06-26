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
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "deliverables" / "_assets" / "theme.css"

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
    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>{_theme()}</style></head>
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


def build_dashboard(db_path: Path, out_path: Path) -> None:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    tasks = con.execute(
        "SELECT id,title,status,priority,domain,created_at FROM tasks ORDER BY id DESC"
    ).fetchall()
    delivs = con.execute(
        "SELECT id,task_id,slug,title,html_path,created_at FROM deliverables ORDER BY id DESC"
    ).fetchall()
    con.close()

    open_n = sum(1 for t in tasks if t["status"] in ("todo", "doing"))
    done_n = sum(1 for t in tasks if t["status"] == "done")

    def esc(x):
        return html.escape(str(x or ""), quote=True)

    def trow(t):
        st = t["status"]
        plabel, pcls = _PRIO.get(t["priority"], ("보통", "p-mid"))
        text = f'{t["title"]} {t["domain"] or ""} {_STATUS_KO.get(st, st)}'
        return (
            f'<tr data-status="{esc(st)}" data-text="{esc(text)}">'
            f'<td class="id" data-v="{t["id"]}">#{t["id"]:03d}</td>'
            f'<td class="ttl">{esc(t["title"])}</td>'
            f'<td><span class="badge b-{esc(st)}">{esc(_STATUS_KO.get(st, st))}</span></td>'
            f'<td data-v="{t["priority"] or 2}"><span class="prio {pcls}">{plabel}</span></td>'
            f'<td class="dim">{esc(t["domain"])}</td>'
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
  <span class="stamp">최종 빌드 {stamp}</span>
</header>
<section class="stats">
  <div class="stat"><div class="num">{open_n}</div><div class="lab">진행 / 대기</div></div>
  <div class="stat s-done"><div class="num">{done_n}</div><div class="lab">완료</div></div>
  <div class="stat s-deliv"><div class="num">{len(delivs)}</div><div class="lab">산출물</div></div>
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
<footer class="dash-foot">🌱 Seed · 더블클릭으로 열리는 정적 대시보드 (서버 불필요)</footer>
</div>"""

    page = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(_wsname())} · 대시보드</title>
<style>{_theme()}</style></head>
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
