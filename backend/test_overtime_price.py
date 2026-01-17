import asyncio
from app.external.kis_client import kis_client

async def check_overtime_price():
    try:
        print("KIS API로 삼성전자(005930) 시간외 단일가 조회 시도...")
        
        # 주식시간외단일가현재가 (FHKST01010900) 호출 시도
        result = await kis_client._request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/inquire-overtime-price", 
            "FHKST01010900",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930"
            }
        )
        
        print(f"응답 타입: {type(result)}")
        print(f"전체 응답: {result}")
        
        if isinstance(result, dict):
            output = result.get("output", {})
            if output:
                print("=" * 40)
                print("✅ 시간외 단일가 조회 성공")
                print(f"데이터: {output}")
                print("=" * 40)
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("\n다른 엔드포인트 시도...")
        try:
            # 엔드포인트 이름이 다를 수 있음
            result = await kis_client._request(
                "GET",
                "/uapi/domestic-stock/v1/quotations/inquire-single-price", 
                "FHKST01010900",
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": "005930"
                }
            )
            print("두 번째 시도 결과:", result)
        except Exception as e2:
            print(f"두 번째 시도 오류: {e2}")

if __name__ == "__main__":
    asyncio.run(check_overtime_price())
