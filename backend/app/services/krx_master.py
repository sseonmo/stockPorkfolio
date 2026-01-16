import asyncio
from datetime import datetime, timedelta
from typing import Any

import httpx

KRX_STOCK_LIST: list[dict[str, str]] = []
_last_updated: datetime | None = None
_lock = asyncio.Lock()


async def fetch_krx_stock_list() -> list[dict[str, str]]:
    global KRX_STOCK_LIST, _last_updated

    async with _lock:
        if _last_updated and datetime.now() - _last_updated < timedelta(hours=24):
            return KRX_STOCK_LIST

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd",
                    params={
                        "bld": "dbms/MDC/STAT/standard/MDCSTAT01901",
                        "locale": "ko_KR",
                        "mktId": "ALL",
                        "share": "1",
                        "csvxls_is498No": "false",
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd",
                    },
                )
                response.raise_for_status()
                data = response.json()
                stocks = data.get("OutBlock_1", [])

                KRX_STOCK_LIST = [
                    {
                        "code": item.get("ISU_SRT_CD", ""),
                        "name": item.get("ISU_ABBRV", ""),
                        "market": item.get("MKT_NM", ""),
                    }
                    for item in stocks
                    if item.get("ISU_SRT_CD") and item.get("ISU_ABBRV")
                ]
                _last_updated = datetime.now()
                return KRX_STOCK_LIST

        except Exception:
            if KRX_STOCK_LIST:
                return KRX_STOCK_LIST
            return _get_fallback_stocks()


def _get_fallback_stocks() -> list[dict[str, str]]:
    return [
        {"code": "005930", "name": "삼성전자", "market": "KOSPI"},
        {"code": "000660", "name": "SK하이닉스", "market": "KOSPI"},
        {"code": "035420", "name": "NAVER", "market": "KOSPI"},
        {"code": "035720", "name": "카카오", "market": "KOSPI"},
        {"code": "005380", "name": "현대차", "market": "KOSPI"},
        {"code": "051910", "name": "LG화학", "market": "KOSPI"},
        {"code": "006400", "name": "삼성SDI", "market": "KOSPI"},
        {"code": "003670", "name": "포스코퓨처엠", "market": "KOSPI"},
        {"code": "131970", "name": "두산테스나", "market": "KOSPI"},
        {"code": "010140", "name": "삼성중공업", "market": "KOSPI"},
        {"code": "055550", "name": "신한지주", "market": "KOSPI"},
        {"code": "105560", "name": "KB금융", "market": "KOSPI"},
        {"code": "086790", "name": "하나금융지주", "market": "KOSPI"},
        {"code": "017670", "name": "SK텔레콤", "market": "KOSPI"},
        {"code": "030200", "name": "KT", "market": "KOSPI"},
        {"code": "012330", "name": "현대모비스", "market": "KOSPI"},
        {"code": "028260", "name": "삼성물산", "market": "KOSPI"},
        {"code": "034730", "name": "SK", "market": "KOSPI"},
        {"code": "003550", "name": "LG", "market": "KOSPI"},
        {"code": "015760", "name": "한국전력", "market": "KOSPI"},
        {"code": "096770", "name": "SK이노베이션", "market": "KOSPI"},
        {"code": "032830", "name": "삼성생명", "market": "KOSPI"},
        {"code": "068270", "name": "셀트리온", "market": "KOSPI"},
        {"code": "207940", "name": "삼성바이오로직스", "market": "KOSPI"},
        {"code": "066570", "name": "LG전자", "market": "KOSPI"},
        {"code": "000270", "name": "기아", "market": "KOSPI"},
        {"code": "018260", "name": "삼성에스디에스", "market": "KOSPI"},
        {"code": "036570", "name": "엔씨소프트", "market": "KOSPI"},
        {"code": "259960", "name": "크래프톤", "market": "KOSPI"},
        {"code": "251270", "name": "넷마블", "market": "KOSPI"},
        {"code": "373220", "name": "LG에너지솔루션", "market": "KOSPI"},
        {"code": "352820", "name": "하이브", "market": "KOSPI"},
        {"code": "011170", "name": "롯데케미칼", "market": "KOSPI"},
        {"code": "004020", "name": "현대제철", "market": "KOSPI"},
        {"code": "005490", "name": "POSCO홀딩스", "market": "KOSPI"},
        {"code": "009150", "name": "삼성전기", "market": "KOSPI"},
        {"code": "090430", "name": "아모레퍼시픽", "market": "KOSPI"},
        {"code": "097950", "name": "CJ제일제당", "market": "KOSPI"},
        {"code": "079550", "name": "LIG넥스원", "market": "KOSPI"},
        {"code": "012450", "name": "한화에어로스페이스", "market": "KOSPI"},
        {"code": "047050", "name": "포스코인터내셔널", "market": "KOSPI"},
        {"code": "042660", "name": "한화오션", "market": "KOSPI"},
        {"code": "402340", "name": "SK스퀘어", "market": "KOSPI"},
        {"code": "247540", "name": "에코프로비엠", "market": "KOSDAQ"},
        {"code": "086520", "name": "에코프로", "market": "KOSDAQ"},
        {"code": "041510", "name": "에스엠", "market": "KOSDAQ"},
        {"code": "122870", "name": "와이지엔터테인먼트", "market": "KOSDAQ"},
        {"code": "263750", "name": "펄어비스", "market": "KOSDAQ"},
        {"code": "293490", "name": "카카오게임즈", "market": "KOSDAQ"},
        {"code": "196170", "name": "알테오젠", "market": "KOSDAQ"},
    ]


async def search_by_name(keyword: str, limit: int = 10) -> list[dict[str, Any]]:
    stocks = await fetch_krx_stock_list()
    keyword_lower = keyword.lower()

    results = []
    for stock in stocks:
        name = stock["name"]
        code = stock["code"]

        if keyword in name or keyword_lower in name.lower() or keyword == code:
            results.append({
                "code": code,
                "name": name,
                "market": stock["market"],
            })
            if len(results) >= limit:
                break

    return results
