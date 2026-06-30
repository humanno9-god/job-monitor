"""
국내 손해보험/생명보험사 채용공고 스크래퍼

전략:
1순위: catch.co.kr의 회사별 채용정보 페이지 (서버 렌더링이라 안정적)
2순위: catch.co.kr이 실패하거나(차단/구조변경) 결과가 비어있으면 잡코리아 검색으로 자동 대체

핵심 원칙: 회사 하나가 실패해도 전체 스크립트가 죽지 않는다.
"""

import json
import re
import time
from datetime import datetime, timezone, timedelta

import requests
from bs4 import BeautifulSoup

HEADERS = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
"(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
"Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
"Referer": "https://www.catch.co.kr/",
"Connection": "keep-alive",
}
TIMEOUT = 20
KST = timezone(timedelta(hours=9))


def scrape_catch(catch_id: str):
"""catch.co.kr 회사별 채용정보 페이지에서 공고 목록 추출"""
url = f"https://www.catch.co.kr/Comp/RecruitInfo/{catch_id}"
resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

jobs = []
seen = set()
for a in soup.find_all("a", href=re.compile(r"/NCS/RecruitInfoDetails/\d+")):
title = a.get_text(strip=True)
href = a.get("href")
if not title or href in seen:
continue
seen.add(href)

# 표(tr) 구조든 div 카드 구조든 모두 대응
row = a.find_parent("tr") or a.find_parent("li") or a.find_parent("div")
condition = ""
deadline = ""
if row:
row_text = row.get_text(" ", strip=True)
d_match = re.search(r"(D-\d+|오늘마감|상시채용|채용시\s*마감)", row_text)
if d_match:
deadline = d_match.group(1)
c_match = re.search(r"(신입|경력\d*년?↑?|학력무관|대졸\(4년\)↑|경력무관)", row_text)
if c_match:
condition = c_match.group(1)

jobs.append(
{
"title": title,
"url": "https://www.catch.co.kr" + href,
"deadline": deadline,
"cond
