import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.core.config import settings
from app.services.krx_master import search_by_name

logger = logging.getLogger(__name__)


class KISClient:
    TOKEN_FILE = "kis_token_cache.json"
    TOKEN_MAX_AGE_HOURS = 23

    def __init__(self):
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None
        self._token_issued_at: datetime | None = None
        self._lock = asyncio.Lock()

    def _is_token_valid(self, expires_at: datetime, issued_at: datetime | None) -> bool:
        now = datetime.now()
        
        if now >= expires_at:
            logger.info("Token expired (past expires_at)")
            return False
        
        if issued_at:
            hours_since_issued = (now - issued_at).total_seconds() / 3600
            if hours_since_issued >= self.TOKEN_MAX_AGE_HOURS:
                logger.info(f"Token too old: {hours_since_issued:.1f} hours since issued")
                return False
        
        return True

    def _load_token_from_disk(self) -> str | None:
        if not os.path.exists(self.TOKEN_FILE):
            return None
        try:
            with open(self.TOKEN_FILE, "r") as f:
                data = json.load(f)
                
                expires_at_str = data.get("expires_at")
                if not expires_at_str:
                    return None
                    
                expires_at = datetime.fromisoformat(expires_at_str)
                issued_at_str = data.get("issued_at")
                issued_at = datetime.fromisoformat(issued_at_str) if issued_at_str else None
                
                if self._is_token_valid(expires_at, issued_at):
                    self._access_token = data.get("access_token")
                    self._token_expires_at = expires_at
                    self._token_issued_at = issued_at
                    return self._access_token
                    
        except Exception as e:
            logger.warning(f"Failed to load token from disk: {e}")
        return None

    def _save_token_to_disk(self, token: str, expires_at: datetime, issued_at: datetime):
        try:
            with open(self.TOKEN_FILE, "w") as f:
                json.dump({
                    "access_token": token,
                    "expires_at": expires_at.isoformat(),
                    "issued_at": issued_at.isoformat()
                }, f)
        except Exception as e:
            logger.warning(f"Failed to save token to disk: {e}")

    def _invalidate_token(self):
        self._access_token = None
        self._token_expires_at = None
        self._token_issued_at = None
        try:
            if os.path.exists(self.TOKEN_FILE):
                os.remove(self.TOKEN_FILE)
                logger.info("Token cache file removed")
        except Exception as e:
            logger.warning(f"Failed to remove token cache file: {e}")

    async def _request_new_token(self) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.kis_base_url}/oauth2/tokenP",
                json={
                    "grant_type": "client_credentials",
                    "appkey": settings.kis_app_key,
                    "appsecret": settings.kis_app_secret,
                },
            )
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Token request failed: {response.status_code} - {error_detail}")
                raise httpx.HTTPStatusError(
                    f"Token request failed: {response.status_code}",
                    request=response.request,
                    response=response
                )
            
            data = response.json()
            access_token = data.get("access_token")
            
            if not access_token:
                raise ValueError("No access_token in response")
            
            expires_in = int(data.get("expires_in", 86400))
            now = datetime.now()
            expires_at = now + timedelta(seconds=expires_in - 300)
            
            self._access_token = access_token
            self._token_expires_at = expires_at
            self._token_issued_at = now
            
            self._save_token_to_disk(access_token, expires_at, now)
            logger.info(f"New token issued, expires at {expires_at}")
            
            return access_token

    async def _get_access_token(self, force_refresh: bool = False) -> str:
        async with self._lock:
            if force_refresh:
                logger.info("Force refreshing token")
                self._invalidate_token()
            
            if (self._access_token and self._token_expires_at and 
                self._is_token_valid(self._token_expires_at, self._token_issued_at)):
                return self._access_token

            loaded_token = self._load_token_from_disk()
            if loaded_token:
                return loaded_token

            return await self._request_new_token()

    async def _request(
        self,
        method: str,
        endpoint: str,
        tr_id: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        _retry: bool = True,
    ) -> dict[str, Any]:
        token = await self._get_access_token()
        headers = {
            "authorization": f"Bearer {token}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": tr_id,
            "content-type": "application/json; charset=utf-8",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method,
                f"{settings.kis_base_url}{endpoint}",
                headers=headers,
                params=params,
                json=data,
            )
            
            if response.status_code in (400, 401) and _retry:
                logger.warning(f"API request failed with {response.status_code}, refreshing token and retrying")
                self._invalidate_token()
                return await self._request(method, endpoint, tr_id, params, data, _retry=False)
            
            response.raise_for_status()
            return response.json()

    async def search_stock(self, keyword: str) -> list[dict[str, Any]]:
        is_code = keyword.isdigit() and len(keyword) == 6

        if is_code:
            return await self._search_by_code(keyword)
        else:
            return await self._search_by_name(keyword)

    async def _search_by_code(self, code: str) -> list[dict[str, Any]]:
        if not settings.kis_app_key:
            mock_data = [
                {"pdno": "005930", "prdt_name": "삼성전자", "market": "KOSPI", "prpr": "72000"},
                {"pdno": "000660", "prdt_name": "SK하이닉스", "market": "KOSPI", "prpr": "135000"},
                {"pdno": "131970", "prdt_name": "두산테스나", "market": "KOSPI", "prpr": "51000"},
            ]
            return [s for s in mock_data if s["pdno"] == code]

        try:
            result = await self._request(
                "GET",
                "/uapi/domestic-stock/v1/quotations/search-stock-info",
                "CTPF1604R",
                params={"PRDT_TYPE_CD": "300", "PDNO": code},
            )
            output = result.get("output", [])
            if isinstance(output, dict):
                return [output] if output else []
            return output
        except Exception:
            return []

    async def _search_by_name(self, keyword: str) -> list[dict[str, Any]]:
        matches = await search_by_name(keyword, limit=10)

        if not matches:
            return []

        if not settings.kis_app_key:
            return [
                {"pdno": m["code"], "prdt_name": m["name"], "market": m["market"], "prpr": "0"}
                for m in matches
            ]

        results = []
        for match in matches[:5]:
            price_info = await self.get_stock_price(match["code"])
            results.append({
                "pdno": match["code"],
                "prdt_name": match["name"],
                "market": match["market"],
                "prpr": str(int(price_info.get("current_price", 0))) if price_info else "0",
            })

        return results

    async def get_stock_price(self, ticker: str) -> dict[str, Any] | None:
        if not settings.kis_app_key:
            return {
                "ticker": ticker,
                "open_price": 71500.0 if ticker == "005930" else 9800.0,
                "high_price": 72500.0 if ticker == "005930" else 10200.0,
                "low_price": 71000.0 if ticker == "005930" else 9700.0,
                "current_price": 72000.0 if ticker == "005930" else 10000.0,
                "change": 100.0,
                "change_percent": 0.5,
                "volume": 1000000,
            }

        try:
            result = await self._request(
                "GET",
                "/uapi/domestic-stock/v1/quotations/inquire-price",
                "FHKST01010100",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": ticker},
            )
            output = result.get("output", {})
            return {
                "ticker": ticker,
                "open_price": float(output.get("stck_oprc", 0)),
                "high_price": float(output.get("stck_hgpr", 0)),
                "low_price": float(output.get("stck_lwpr", 0)),
                "current_price": float(output.get("stck_prpr", 0)),
                "change": float(output.get("prdy_vrss", 0)),
                "change_percent": float(output.get("prdy_ctrt", 0)),
                "volume": int(output.get("acml_vol", 0)),
            }
        except Exception:
            return None

    async def get_daily_prices(
        self, ticker: str, start_date: str, end_date: str
    ) -> list[dict[str, Any]]:
        if not settings.kis_app_key:
            return []

        try:
            result = await self._request(
                "GET",
                "/uapi/domestic-stock/v1/quotations/inquire-daily-price",
                "FHKST01010400",
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": ticker,
                    "FID_PERIOD_DIV_CODE": "D",
                    "FID_ORG_ADJ_PRC": "0",
                },
            )
            return result.get("output", [])
        except Exception:
            return []


kis_client = KISClient()
