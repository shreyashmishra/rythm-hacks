from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from ..models import AuditEvent, User


def log_audit_event(
    db: Session,
    *,
    actor_user_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None,
    patient_profile_id: str | None = None,
    encounter_id: str | None = None,
    details: dict[str, object] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        patient_profile_id=patient_profile_id,
        encounter_id=encounter_id,
        details=details,
    )
    db.add(event)
    return event


def serialize_audit_event(event: AuditEvent, actor: User | None = None) -> dict[str, object]:
    active_actor = actor or event.actor_user
    return {
        "id": event.id,
        "action": event.action,
        "resourceType": event.resource_type,
        "resourceId": event.resource_id,
        "createdAt": event.created_at.isoformat(),
        "details": event.details or {},
        "actor": (
            {
                "id": active_actor.id,
                "name": active_actor.name,
                "role": active_actor.role.value,
            }
            if active_actor
            else None
        ),
    }


def fetch_recent_audit_events(
    db: Session,
    *,
    patient_profile_id: str,
    limit: int = 12,
) -> list[dict[str, object]]:
    statement: Select[tuple[AuditEvent, User | None]] = (
        select(AuditEvent, User)
        .outerjoin(User, User.id == AuditEvent.actor_user_id)
        .where(AuditEvent.patient_profile_id == patient_profile_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(limit)
    )
    rows: Iterable[tuple[AuditEvent, User | None]] = db.execute(statement).all()
    return [serialize_audit_event(event, actor) for event, actor in rows]
