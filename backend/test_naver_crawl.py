import asyncio
import httpx
from bs4 import BeautifulSoup

async def get_naver_price(ticker: str):
    # 시세 페이지 조회
    url = f"https://finance.naver.com/item/sise.naver?code={ticker}"
    
    async with httpx.AsyncClient() as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = await client.get(url, headers=headers)
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 정규장 현재가
        # strong 태그의 id="_nowVal" (없을 수도 있음, sise 페이지 구조 확인 필요)
        # 보통 class="t_02" 같은 클래스를 사용함
        
        print(f"URL: {url}")
        
        # iframe으로 불러오는 경우가 많아 직접 데이터가 없을 수 있음.
        # 시간외 단일가는 iframe인 경우가 많음.
        
        # 시간외 단일가 전용 페이지 시도
        # https://finance.naver.com/item/sise_time.naver?code=005930&thistime=...&page=1
        
        # 일단 sise_time.naver 호출해보기 (시간외 말고 정규장 시간별 시세일 수 있음)
        
        return 0

async def get_naver_overtime_price(ticker: str):
    # 시간외 단일가 페이지
    url = f"https://finance.naver.com/item/sise_time.naver?code={ticker}&thistime=20240115180000" # thistime은 무시될 수 있음
    
    async with httpx.AsyncClient() as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = await client.get(url, headers=headers)
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 시간외 단일가 테이블의 첫 번째 행 (최신)
        # 테이블 구조가 복잡할 수 있으니 확인 필요
        # 보통 class="type2" 테이블의 첫 번째 tr
        
        # 실제로는 item/sise_time.naver는 '시간별 시세'이고, '시간외 단일가'는 다름
        # 시간외 단일가는 https://finance.naver.com/item/sise_time.naver?code=005930&thistime=20260117180000 등이 아님.
        
        # 정확한 URL은 'https://finance.naver.com/item/last_day.naver?code=...' 등 다양함.
        # 하지만 '시간외 단일가' 탭이 따로 있음.
        
        print("시간외 단일가 크롤링은 페이지 구조 분석이 필요합니다.")
        return None

if __name__ == "__main__":
    asyncio.run(get_naver_price("005930"))
