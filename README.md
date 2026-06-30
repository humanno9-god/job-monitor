# 국내 보험사 채용 모니터

손해보험·생명보험사 27곳의 채용공고를 한눈에 보는 대시보드입니다.
매일 한국시간 오전 10시 자동으로 갱신되며, 대시보드의 Refresh 버튼은 최신 갱신 결과를 다시 불러옵니다.

## 동작 방식
- GitHub Actions가 매일 오전 10시(KST)에 `scraper.py`를 실행해 `data.json`을 갱신합니다
- GitHub Pages가 `docs/index.html`로 그 결과를 보여줍니다
- 회사 목록/링크는 `companies.json`에서 수정 가능합니다
