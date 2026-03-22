"""Seed minimal reference data for the demo."""

from app.db.session import SessionLocal
from app.db.models.core import ReportingPeriod, PeriodType, StrategicPillar, StrategicObjective


def main() -> None:
    db = SessionLocal()
    try:
        if not db.query(ReportingPeriod).filter(ReportingPeriod.label == "FY2026-Q1").first():
            db.add(ReportingPeriod(label="FY2026-Q1", period_type=PeriodType.quarter, fiscal_year=2026, quarter=1))
        if not db.query(ReportingPeriod).filter(ReportingPeriod.label == "FY2026-Q2").first():
            db.add(ReportingPeriod(label="FY2026-Q2", period_type=PeriodType.quarter, fiscal_year=2026, quarter=2))

        pillar = db.query(StrategicPillar).filter(StrategicPillar.code == "P1").first()
        if pillar is None:
            pillar = StrategicPillar(code="P1", name="Operational Excellence", description="Improve delivery and reliability")
            db.add(pillar)
            db.flush()

        if not db.query(StrategicObjective).filter(StrategicObjective.code == "OBJ-1").first():
            objective = StrategicObjective(code="OBJ-1", title="Raise on-time delivery", strategic_pillar_id=pillar.id)
            db.add(objective)
        db.commit()
        print("Seeded reference data")
    finally:
        db.close()


if __name__ == "__main__":
    main()
