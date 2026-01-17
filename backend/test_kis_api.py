import asyncio
import os
from app.external.kis_client import kis_client
from app.core.config import settings

# 환경 변수 로드 (이미 설정되어 있다고 가정하지만 명시적으로 확인)
print(f"KIS_APP_KEY configured: {bool(settings.kis_app_key)}")

async def check_price():
    try:
        print("KIS API로 삼성전자(005930) 가격 조회 시도...")
        price_data = await kis_client.get_stock_price("005930")
        
        if price_data:
            print("=" * 40)
            print(f"종목: {price_data.get('ticker')}")
            print(f"현재가: {price_data.get('current_price')}원")
            print(f"등락: {price_data.get('change')} ({price_data.get('change_percent')}%)")
            print(f"거래량: {price_data.get('volume')}")
            print("=" * 40)
        else:
            print("가격 데이터를 가져오지 못했습니다.")
            
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(check_price())
