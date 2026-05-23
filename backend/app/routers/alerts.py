from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.models import Alert
from app.schemas import AlertCreate, AlertRead, AlertUpdate
from app.services import alert_engine, notifier
from app.services.ratio_fetcher import RatioFetchError, fetch_ratio
from app.worker import get_latest_quote

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRead])
async def list_alerts(session: AsyncSession = Depends(get_session)) -> list[Alert]:
    result = await session.exec(select(Alert).order_by(Alert.id))
    return list(result.all())


@router.post("", response_model=AlertRead, status_code=201)
async def create_alert(
    payload: AlertCreate,
    session: AsyncSession = Depends(get_session),
) -> Alert:
    alert = Alert(
        name=payload.name,
        threshold=payload.threshold,
        operator=payload.operator,
        enabled=payload.enabled,
    )

    quote = get_latest_quote()
    if quote is None:
        try:
            quote = await fetch_ratio()
        except RatioFetchError:
            quote = None

    if quote is not None:
        alert_engine.disarm_if_already_met(alert, quote.ratio)

    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert


@router.get("/{alert_id}", response_model=AlertRead)
async def get_alert(
    alert_id: int,
    session: AsyncSession = Depends(get_session),
) -> Alert:
    alert = await session.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/{alert_id}", response_model=AlertRead)
async def update_alert(
    alert_id: int,
    payload: AlertUpdate,
    session: AsyncSession = Depends(get_session),
) -> Alert:
    alert = await session.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(alert, key, value)

    quote = get_latest_quote()
    if quote is not None:
        alert_engine.disarm_if_already_met(alert, quote.ratio)

    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    alert = await session.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    await session.delete(alert)
    await session.commit()


@router.post("/{alert_id}/test")
async def test_alert(
    alert_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    alert = await session.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    try:
        await notifier.send_discord_test()
    except notifier.NotifierError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"status": "sent", "alert_id": str(alert_id)}
