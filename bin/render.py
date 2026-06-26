#!/usr/bin/env python3
"""Seed — md → html 렌더러 + 대시보드 빌더 (의존성 0, 표준 라이브러리만).

- md_to_html(text): 경량 마크다운 → HTML 본문 변환 (헤더/리스트/표/코드/인용/링크/강조)
- render_file(md, html, title): 산출물 .md 를 테마 입힌 .html 로
- build_dashboard(db, out): workspace.db 스냅샷을 정적 대시보드 HTML 로 (서버 불필요)

추후 더 풍부한 변환이 필요하면 `markdown` 패키지로 교체 가능 (DESIGN §9-3). 지금은 무의존이 기본.
"""
from __future__ import annotations
import html
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
def build_dashboard(db_path: Path, out_path: Path) -> None:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    tasks = con.execute(
        "SELECT id,title,status,priority,domain,created_at,closed_at FROM tasks ORDER BY id DESC"
    ).fetchall()
    delivs = con.execute(
        "SELECT id,task_id,slug,title,html_path,created_at FROM deliverables ORDER BY id DESC"
    ).fetchall()
    con.close()

    open_n = sum(1 for t in tasks if t["status"] in ("todo", "doing"))
    done_n = sum(1 for t in tasks if t["status"] == "done")

    badge = {"todo": "b-todo", "doing": "b-doing", "done": "b-done", "dropped": "b-drop"}
    trows = "".join(
        f'<tr><td class="id">#{t["id"]:03d}</td>'
        f'<td>{html.escape(t["title"])}</td>'
        f'<td><span class="badge {badge.get(t["status"],"")}">{t["status"]}</span></td>'
        f'<td>{html.escape(t["domain"] or "")}</td>'
        f'<td class="dim">{html.escape((t["created_at"] or "")[:10])}</td></tr>'
        for t in tasks
    ) or '<tr><td colspan="5" class="dim">아직 업무가 없습니다.</td></tr>'

    drows = "".join(
        f'<tr><td class="id">#{d["id"]:03d}</td>'
        f'<td><a href="{html.escape(_rel(d["html_path"], out_path))}">{html.escape(d["title"])}</a></td>'
        f'<td class="dim">{html.escape(d["slug"])}</td>'
        f'<td class="dim">{html.escape((d["created_at"] or "")[:10])}</td></tr>'
        for d in delivs
    ) or '<tr><td colspan="4" class="dim">아직 산출물이 없습니다.</td></tr>'

    body = f"""
<section class="stats">
  <div class="stat"><div class="num">{open_n}</div><div class="lab">진행/대기</div></div>
  <div class="stat"><div class="num">{done_n}</div><div class="lab">완료</div></div>
  <div class="stat"><div class="num">{len(delivs)}</div><div class="lab">산출물</div></div>
</section>
<h2>📋 업무</h2>
<table class="grid"><thead><tr><th>ID</th><th>제목</th><th>상태</th><th>도메인</th><th>생성</th></tr></thead>
<tbody>{trows}</tbody></table>
<h2>📄 산출물</h2>
<table class="grid"><thead><tr><th>ID</th><th>제목</th><th>slug</th><th>생성</th></tr></thead>
<tbody>{drows}</tbody></table>
"""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    Path(out_path).write_text(_page("워크스페이스 대시보드", body, f"최종 빌드 {stamp}"), encoding="utf-8")


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
