from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.models import WebhookDeliveryLog, WebhookEvent, WebhookSubscription


async def dispatch_webhook(db: Session, site_id: UUID, event: WebhookEvent, payload: dict) -> None:
    subs = (
        db.query(WebhookSubscription)
        .filter(
            WebhookSubscription.site_id == site_id,
            WebhookSubscription.event_type == event,
            WebhookSubscription.is_active == True,
        )
        .all()
    )
    for sub in subs:
        success = False
        status_code = None
        error = None
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(sub.callback_url, json=payload)
                status_code = resp.status_code
                success = 200 <= resp.status_code < 300
        except Exception as exc:
            error = str(exc)
        db.add(
            WebhookDeliveryLog(
                subscription_id=sub.id,
                payload=payload,
                status_code=status_code,
                success=success,
                error_message=error,
            )
        )
    db.commit()


def dispatch_webhook_sync(db: Session, site_id: UUID, event: WebhookEvent, payload: dict) -> None:
    subs = (
        db.query(WebhookSubscription)
        .filter(
            WebhookSubscription.site_id == site_id,
            WebhookSubscription.event_type == event,
            WebhookSubscription.is_active == True,
        )
        .all()
    )
    for sub in subs:
        success = False
        status_code = None
        error = None
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(sub.callback_url, json=payload)
                status_code = resp.status_code
                success = 200 <= resp.status_code < 300
        except Exception as exc:
            error = str(exc)
        db.add(
            WebhookDeliveryLog(
                subscription_id=sub.id,
                payload=payload,
                status_code=status_code,
                success=success,
                error_message=error,
            )
        )
    db.commit()
