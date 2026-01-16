from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.models.user import User
from app.api.routes.auth import get_current_user
from app.tasks.batch_tasks import (
    _update_kr_prices,
    _update_us_prices,
    _create_daily_snapshot,
)
import asyncio

router = APIRouter()


class BatchResponse(BaseModel):
    status: str
    message: str
    task: str


@router.post("/update-kr-prices", response_model=BatchResponse)
async def trigger_update_kr_prices(
    _: Annotated[User, Depends(get_current_user)],
) -> dict:
    """한국 주식 가격 업데이트 배치 실행"""
    try:
        await _update_kr_prices()
        return {
            "status": "success",
            "message": "한국 주식 가격이 업데이트되었습니다.",
            "task": "update_kr_prices",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-us-prices", response_model=BatchResponse)
async def trigger_update_us_prices(
    _: Annotated[User, Depends(get_current_user)],
) -> dict:
    """미국 주식 가격 업데이트 배치 실행"""
    try:
        await _update_us_prices()
        return {
            "status": "success",
            "message": "미국 주식 가격이 업데이트되었습니다.",
            "task": "update_us_prices",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-snapshot", response_model=BatchResponse)
async def trigger_create_snapshot(
    _: Annotated[User, Depends(get_current_user)],
) -> dict:
    """일일 포트폴리오 스냅샷 생성 배치 실행"""
    try:
        await _create_daily_snapshot()
        return {
            "status": "success",
            "message": "일일 스냅샷이 생성되었습니다.",
            "task": "create_daily_snapshot",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh-all", response_model=BatchResponse)
async def trigger_refresh_all(
    _: Annotated[User, Depends(get_current_user)],
) -> dict:
    """모든 배치 작업 실행 (가격 업데이트 + 스냅샷)"""
    try:
        await _update_kr_prices()
        await _update_us_prices()
        await _create_daily_snapshot()
        return {
            "status": "success",
            "message": "모든 데이터가 새로고침되었습니다.",
            "task": "refresh_all",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
