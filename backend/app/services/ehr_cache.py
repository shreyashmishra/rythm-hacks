from __future__ import annotations

import json
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from ..config import settings


_redis_client: Redis | None | object = None
_UNSET = object()


def _get_cache_key(patient_profile_id: str) -> str:
    return f"patient-encounters:{patient_profile_id}"


def set_redis_client_for_testing(client: Redis | None) -> None:
    global _redis_client
    _redis_client = client


def get_redis_client() -> Redis | None:
    global _redis_client

    if _redis_client is _UNSET:
        return None

    if _redis_client is None:
        if not settings.redis_url:
            _redis_client = _UNSET
            return None

        try:
            _redis_client = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
                health_check_interval=30,
            )
            _redis_client.ping()
        except RedisError:
            _redis_client = _UNSET
            return None

    return _redis_client


def get_cached_patient_encounters(
    patient_profile_id: str,
) -> list[dict[str, Any]] | None:
    client = get_redis_client()
    if client is None:
        return None

    try:
        cached_payload = client.get(_get_cache_key(patient_profile_id))
    except RedisError:
        return None

    if cached_payload is None:
        return None

    try:
        parsed_payload = json.loads(cached_payload)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed_payload, list):
        return None
    return parsed_payload


def cache_patient_encounters(
    patient_profile_id: str,
    encounters: list[dict[str, Any]],
) -> None:
    client = get_redis_client()
    if client is None:
        return

    try:
        client.setex(
            _get_cache_key(patient_profile_id),
            settings.encounter_cache_ttl_seconds,
            json.dumps(encounters, separators=(",", ":")),
        )
    except RedisError:
        return


def invalidate_patient_encounters(patient_profile_id: str) -> None:
    client = get_redis_client()
    if client is None:
        return

    try:
        client.delete(_get_cache_key(patient_profile_id))
    except RedisError:
        return
