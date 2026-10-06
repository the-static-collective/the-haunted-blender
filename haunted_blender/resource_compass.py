"""FRANKEN BLENDER 008e — quantity-first resource compass.

This module ranks *supply*, not aesthetics.

Order:
  repeatable local $0
  repeatable provider $0
  daily free
  weekly free
  regenerating included allowance
  finite free credit
  one-shot promo
  paid
  unavailable

Within a supply class:
  more obtainable seconds first,
  then empirical reliability,
  then empirical human KEEP rate.

QUALITY IS TERTIARY.
"""
from __future__ import annotations

import copy
import math

SCHEMA = "haunted-blender/resource-compass/v1"

CLASS_PRIORITY = {
    "local_repeatable_zero": 0,
    "free_repeatable": 1,
    "free_daily": 2,
    "free_weekly": 3,
    "included_regenerating": 4,
    "finite_free_credit": 5,
    "one_shot_promo": 6,
    "paid": 7,
    "unavailable": 8,
}


def classify(model: dict) -> str:
    explicit = str(model.get("availabilityClass") or "").strip()
    if explicit:
        if explicit not in CLASS_PRIORITY:
            raise ValueError(f"Unknown availabilityClass: {explicit}")
        return explicit

    if not model.get("available", True) or model.get("spendClass") == "unavailable":
        return "unavailable"

    spend = str(model.get("spendClass") or "paid")
    entitlement = str(model.get("entitlement") or "").lower()
    free_runs = int(model.get("freeRunsRemaining") or 0)
    reset_seconds = model.get("resetSeconds")
    repeatable_free = bool(model.get("repeatableFree", False))

    if spend == "free":
        if repeatable_free:
            return "free_repeatable"
        if reset_seconds is not None:
            reset = int(reset_seconds)
            if reset <= 86400:
                return "free_daily"
            if reset <= 7 * 86400:
                return "free_weekly"
        if free_runs > 0:
            if any(token in entitlement for token in ("one", "promo", "trial", "welcome")):
                return "one_shot_promo"
            return "finite_free_credit"
        return "finite_free_credit"

    if spend == "included":
        if reset_seconds is not None or model.get("regeneratingAllowance") is True:
            return "included_regenerating"
        return "finite_free_credit"

    if spend == "paid":
        return "paid"

    return "unavailable"


def _model_usage(usage: dict | None, provider_id: str, model_name: str) -> dict:
    if not usage:
        return {}
    provider = (usage.get("providers") or {}).get(provider_id) or {}
    return (provider.get("models") or {}).get(model_name) or {}


def _provider_usage(usage: dict | None, provider_id: str) -> dict:
    if not usage:
        return {}
    return (usage.get("providers") or {}).get(provider_id) or {}


def _capacity_seconds(model: dict, availability_class: str) -> float:
    seconds_per_run = float(
        model.get("secondsPerRun")
        or model.get("maxSeconds")
        or model.get("durationSeconds")
        or 0
    )
    if availability_class in {"local_repeatable_zero", "free_repeatable"}:
        return math.inf

    runs = model.get("maxRunsPerWindow")
    if runs is None:
        runs = model.get("freeRunsRemaining")
    if runs is None:
        credit_cost = model.get("creditCost")
        balance = model.get("creditBalance")
        if credit_cost not in (None, 0) and balance is not None:
            runs = math.floor(float(balance) / float(credit_cost))
    if runs is None:
        runs = 1 if availability_class in {
            "free_daily",
            "free_weekly",
            "one_shot_promo",
            "paid",
        } else 0
    return max(0.0, seconds_per_run * max(0, int(runs)))


def rank_observation(observation: dict, usage: dict | None = None) -> dict:
    rows = [
        {
            "providerId": "haunted-blender-local",
            "profileId": "local",
            "model": "zero-dollar-film-mill",
            "routeKind": "deterministic-derivative",
            "availabilityClass": "local_repeatable_zero",
            "priority": CLASS_PRIORITY["local_repeatable_zero"],
            "capacitySeconds": None,
            "capacityMeaning": "unbounded-by-provider",
            "spendClass": "free",
            "quality": {"keepRate": None, "samples": 0},
            "reliability": {"successRate": 1.0, "samples": 0},
            "reason": "Local deterministic substrate has no provider quota.",
        }
    ]

    for provider in observation.get("providers") or []:
        provider_id = str(provider["providerId"])
        p_usage = _provider_usage(usage, provider_id)
        provider_events = int(p_usage.get("events") or 0)
        provider_successes = int(p_usage.get("successes") or 0)
        reliability = (
            provider_successes / provider_events if provider_events else None
        )
        for model in provider.get("models") or []:
            name = str(model["model"])
            availability_class = classify(model)
            capacity = _capacity_seconds(model, availability_class)
            m_usage = _model_usage(usage, provider_id, name)
            accepted = int(m_usage.get("accepted") or 0)
            declined = int(m_usage.get("declined") or 0)
            editorial_samples = accepted + declined
            keep_rate = accepted / editorial_samples if editorial_samples else None
            rows.append(
                {
                    "providerId": provider_id,
                    "profileId": provider.get("profileId"),
                    "model": name,
                    "routeKind": model.get("routeKind"),
                    "availabilityClass": availability_class,
                    "priority": CLASS_PRIORITY[availability_class],
                    "capacitySeconds": None if math.isinf(capacity) else round(capacity, 6),
                    "capacityMeaning": (
                        "unbounded-by-provider" if math.isinf(capacity)
                        else "currently-observed-window"
                    ),
                    "spendClass": model.get("spendClass"),
                    "estimatedUsdMicros": model.get("estimatedUsdMicros"),
                    "creditCost": model.get("creditCost"),
                    "creditBalance": model.get("creditBalance"),
                    "resetSeconds": model.get("resetSeconds"),
                    "freeRunsRemaining": model.get("freeRunsRemaining"),
                    "quality": {
                        "keepRate": round(keep_rate, 6) if keep_rate is not None else None,
                        "samples": editorial_samples,
                    },
                    "reliability": {
                        "successRate": round(reliability, 6) if reliability is not None else None,
                        "samples": provider_events,
                    },
                    "reason": (
                        "Supply class dominates; capacity dominates; observed quality breaks late ties."
                    ),
                }
            )

    def sort_key(row: dict):
        capacity = row["capacitySeconds"]
        cap_key = -1e100 if capacity is None else -float(capacity)
        reliability = row["reliability"]["successRate"]
        keep = row["quality"]["keepRate"]
        return (
            int(row["priority"]),
            cap_key,
            -(reliability if reliability is not None else -1),
            -(keep if keep is not None else -1),
            str(row["providerId"]),
            str(row["model"]),
        )

    rows.sort(key=sort_key)
    return {
        "schema": SCHEMA,
        "optimizationOrder": [
            "repeatability",
            "obtainable-seconds",
            "empirical-reliability",
            "empirical-quality",
        ],
        "rows": rows,
        "laws": [
            "QUANTITY BEFORE DURATION BEFORE QUALITY",
            "ONE-SHOT PROMO != REPEATABLE FREE",
            "FINITE CREDIT != INFRASTRUCTURE",
            "OBSERVED KEEP RATE != FUTURE AUTHORITY",
            "LOCAL ZERO-DOLLAR SUBSTRATE COMES FIRST",
        ],
    }
