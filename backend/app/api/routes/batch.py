from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.models.user import User
from app.api.routes.auth import get_current_user
from app.tasks.batch_tasks import (
    _update_kr_prices,
    _update_us_prices,
    _create_daily_snapshot,
)

router = APIRouter()


class BatchResponse(BaseModel):
    status: str
    message: str
    task: str
    target_date: str | None = None


def parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)")


@router.post("/update-kr-prices", response_model=BatchResponse)
async def trigger_update_kr_prices(
    _: Annotated[User, Depends(get_current_user)],
    target_date: str | None = Query(None, description="대상 날짜 (YYYY-MM-DD)"),
) -> dict:
    try:
        parsed_date = parse_date(target_date)
        await _update_kr_prices(parsed_date)
        target = parsed_date or date.today()
        return {
            "status": "success",
            "message": f"{target} 한국 주식 가격이 업데이트되었습니다.",
            "task": "update_kr_prices",
            "target_date": str(target),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-us-prices", response_model=BatchResponse)
async def trigger_update_us_prices(
    _: Annotated[User, Depends(get_current_user)],
    target_date: str | None = Query(None, description="대상 날짜 (YYYY-MM-DD)"),
) -> dict:
    try:
        parsed_date = parse_date(target_date)
        await _update_us_prices(parsed_date)
        target = parsed_date or date.today()
        return {
            "status": "success",
            "message": f"{target} 미국 주식 가격이 업데이트되었습니다.",
            "task": "update_us_prices",
            "target_date": str(target),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-snapshot", response_model=BatchResponse)
async def trigger_create_snapshot(
    _: Annotated[User, Depends(get_current_user)],
    target_date: str | None = Query(None, description="대상 날짜 (YYYY-MM-DD)"),
) -> dict:
    try:
        parsed_date = parse_date(target_date)
        await _create_daily_snapshot(parsed_date)
        target = parsed_date or date.today()
        return {
            "status": "success",
            "message": f"{target} 일일 스냅샷이 생성되었습니다.",
            "task": "create_daily_snapshot",
            "target_date": str(target),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh-all", response_model=BatchResponse)
async def trigger_refresh_all(
    _: Annotated[User, Depends(get_current_user)],
    target_date: str | None = Query(None, description="대상 날짜 (YYYY-MM-DD)"),
) -> dict:
    try:
        parsed_date = parse_date(target_date)
        await _update_kr_prices(parsed_date)
        await _update_us_prices(parsed_date)
        target = parsed_date or date.today()
        return {
            "status": "success",
            "message": f"{target} 모든 데이터가 새로고침되었습니다.",
            "task": "refresh_all",
            "target_date": str(target),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
