"""
국내 손해보험/생명보험사 채용공고 스크래퍼

전략:
1순위: catch.co.kr의 회사별 채용정보 페이지 (서버 렌더링이라 안정적)
2순위(catch_id 없는 회사): 잡코리아 키워드 검색 결과에서 해당 회사명이 포함된 공고만 추출

핵심 원칙: 회사 하나가 실패해도 전체 스크립트가 죽지 않는다.
실패한 회사는 status="error"로 표시하고 site_url 링크만 보여준다.
"""

import json
import re
import time
from datetime import datetime, timezone, timedelta

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}
TIMEOUT = 15
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
        row = a.find_parent("tr")
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
                "condition": condition,
            }
        )
    return jobs[:15]


def scrape_jobkorea_fallback(company_name: str):
    """catch_id가 없는 회사는 잡코리아 검색으로 대체"""
    url = "https://www.jobkorea.co.kr/Search/"
    resp = requests.get(
        url, params={"stext": company_name}, headers=HEADERS, timeout=TIMEOUT
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = []
    seen = set()
    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href = a["href"]
        if not title or company_name not in title:
            continue
        if href in seen:
            continue
        seen.add(href)
        if href.startswith("/"):
            href = "https://www.jobkorea.co.kr" + href
        jobs.append({"title": title, "url": href, "deadline": "", "condition": ""})
        if len(jobs) >= 10:
            break
    return jobs


def scrape_company(company: dict):
    name = company["name"]
    try:
        if company.get("catch_id"):
            jobs = scrape_catch(company["catch_id"])
            source = "catch.co.kr"
        else:
            jobs = scrape_jobkorea_fallback(name)
            source = "jobkorea(fallback)"

        return {
            "name": name,
            "type": company["type"],
            "site_url": company["site_url"],
            "status": "ok" if jobs else "empty",
            "source": source,
            "jobs": jobs,
            "error": None,
        }
    except Exception as e:
        return {
            "name": name,
            "type": company["type"],
            "site_url": company["site_url"],
            "status": "error",
            "source": None,
            "jobs": [],
            "error": str(e)[:200],
        }


def main():
    with open("companies.json", encoding="utf-8") as f:
        companies = json.load(f)

    results = []
    for c in companies:
        results.append(scrape_company(c))
        time.sleep(1)

    output = {
        "updated_at": datetime.now(KST).isoformat(),
        "companies": results,
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    ok = sum(1 for r in results if r["status"] == "ok")
    err = sum(1 for r in results if r["status"] == "error")
    print(f"완료: 성공 {ok}건 / 실패 {err}건 / 전체 {len(results)}건")


if __name__ == "__main__":
    main()
