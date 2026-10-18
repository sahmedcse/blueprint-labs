"""Health check: is the service up and can it reach its database?"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from __PKG__.db.session import get_session

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok", "unavailable"]


@router.get("/healthz")
async def healthz(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HealthResponse:
    try:
        await session.execute(text("select 1"))
    except (SQLAlchemyError, OSError):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="unavailable")
    return HealthResponse(status="ok")
