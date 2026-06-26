---
name: view
description: >
  산출물 대시보드를 연다. "대시보드 열어줘", "산출물 보여줘", "뭐 했는지 보자" 등에서 사용.
  기본은 정적 파일을 더블클릭(open), 옵션으로 로컬 서버.
---

# /view — 대시보드 열기

`deliverables/_dashboard.html` 은 업무·산출물을 한눈에 보여주는 정적 대시보드다. 서버 없이 열린다.

## 절차

1. 대시보드를 최신으로 재빌드(안전):
   ```bash
   python bin/ws.py build
   ```
2. 열기:
   ```bash
   open deliverables/_dashboard.html          # macOS
   # xdg-open deliverables/_dashboard.html     # Linux
   ```

## 옵션 — 로컬 서버 (`--serve`)

더 쾌적한 브라우징을 원하면 정적 서버를 띄운다:
```bash
python -m http.server -d deliverables 8765
# 브라우저에서 http://localhost:8765/_dashboard.html
```
서버는 백그라운드로 띄우고, 사용자가 멈추라고 할 때까지 둔다.
