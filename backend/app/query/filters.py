import re
from dataclasses import asdict, dataclass
from difflib import get_close_matches

from sqlalchemy.orm import Session

from app.db.models.core import BusinessUnit, Division, Leader, Region, StrategicObjective, StrategicPillar


@dataclass
class QueryFilters:
    division_name: str | None = None
    business_unit_name: str | None = None
    region_name: str | None = None
    leader_name: str | None = None
    strategic_pillar_name: str | None = None
    strategic_objective_name: str | None = None
    document_type: str | None = None
    fiscal_year: int | None = None
    quarter: int | None = None


QUARTER_PATTERN = re.compile(r"\bq([1-4])\b", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")


def _fuzzy_match(value: str | None, options: list[str], question: str) -> str | None:
    if value:
        candidates = get_close_matches(value, options, n=1, cutoff=0.6)
        if candidates:
            return candidates[0]
    for option in options:
        if option.lower() in question:
            return option
    return None


def resolve_filters(db: Session, question: str, provided: dict | None) -> QueryFilters:
    provided = provided or {}
    lowered = question.lower()

    divisions = [row.name for row in db.query(Division).filter(Division.active.is_(True)).all()]
    business_units = [row.name for row in db.query(BusinessUnit).filter(BusinessUnit.active.is_(True)).all()]
    regions = [row.name for row in db.query(Region).filter(Region.active.is_(True)).all()]
    leaders = [row.full_name for row in db.query(Leader).filter(Leader.active.is_(True)).all()]
    pillars = [row.name for row in db.query(StrategicPillar).all()]
    objectives = [row.title for row in db.query(StrategicObjective).filter(StrategicObjective.active.is_(True)).all()]

    quarter_match = QUARTER_PATTERN.search(question)
    year_match = YEAR_PATTERN.search(question)

    filters = QueryFilters(
        division_name=_fuzzy_match(provided.get("division_name"), divisions, lowered),
        business_unit_name=_fuzzy_match(provided.get("business_unit_name"), business_units, lowered),
        region_name=_fuzzy_match(provided.get("region_name"), regions, lowered),
        leader_name=_fuzzy_match(provided.get("leader_name"), leaders, lowered),
        strategic_pillar_name=_fuzzy_match(provided.get("strategic_pillar_name"), pillars, lowered),
        strategic_objective_name=_fuzzy_match(provided.get("strategic_objective_name"), objectives, lowered),
        document_type=provided.get("document_type"),
        fiscal_year=int(year_match.group(1)) if year_match else None,
        quarter=int(quarter_match.group(1)) if quarter_match else None,
    )

    if "annual" in lowered and not filters.document_type:
        filters.document_type = "annual_strategy"
    if ("quarter" in lowered or filters.quarter) and not filters.document_type:
        filters.document_type = "quarterly_report"

    return filters


def filters_to_dict(filters: QueryFilters) -> dict:
    return asdict(filters)
