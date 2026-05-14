"""Base class for ingestion adapters."""

import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime, timezone

from rich.console import Console
from sqlalchemy.orm import Session

from pipeline.models import DataSource, IngestionJob

console = Console()


class IngestionAdapter(ABC):
    """Base class for all data source adapters."""

    source_type: str

    def __init__(self, session: Session, site_id: uuid.UUID, *, from_date: date | None = None):
        """
        Args:
          session: SQLAlchemy session.
          site_id: Site UUID this adapter is running against.
          from_date: Optional override for the start of the ingestion window.
            When set, overrides each adapter's built-in last_sync / default
            lookback logic. Used for one-off backfill runs over arbitrary
            historical ranges (see plan-2026-05-14-tqs-forecast-history.md).
            Adapters opt in by consulting `self.from_date` in their ingest()
            implementation.
        """
        self.session = session
        self.site_id = site_id
        self.from_date = from_date

    def get_last_sync(self) -> datetime | None:
        ds = (
            self.session.query(DataSource)
            .filter_by(site_id=self.site_id, source_type=self.source_type)
            .first()
        )
        return ds.last_sync_at if ds else None

    def update_last_sync(self, ts: datetime) -> None:
        ds = (
            self.session.query(DataSource)
            .filter_by(site_id=self.site_id, source_type=self.source_type)
            .first()
        )
        if ds:
            ds.last_sync_at = ts
            ds.status = "healthy"
        else:
            ds = DataSource(
                site_id=self.site_id,
                source_type=self.source_type,
                config={},
                last_sync_at=ts,
                status="healthy",
            )
            self.session.add(ds)

    def create_job(self) -> IngestionJob:
        job = IngestionJob(
            site_id=self.site_id,
            source_type=self.source_type,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(job)
        self.session.flush()
        return job

    def complete_job(
        self, job: IngestionJob, created: int, updated: int
    ) -> None:
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.records_created = created
        job.records_updated = updated
        self.update_last_sync(job.completed_at)
        self.session.commit()

    def fail_job(self, job: IngestionJob, error: str) -> None:
        job.status = "failed"
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = error
        self.session.commit()

    def run(self) -> None:
        job = self.create_job()
        try:
            created, updated = self.ingest()
            self.complete_job(job, created, updated)
            console.print(
                f"  [green]✓[/green] {self.source_type}: "
                f"{created} created, {updated} updated"
            )
        except Exception as e:
            self.session.rollback()
            job = self.session.merge(job)
            self.fail_job(job, str(e))
            console.print(f"  [red]✗[/red] {self.source_type}: {e}")
            raise

    @abstractmethod
    def ingest(self) -> tuple[int, int]:
        """Run ingestion. Returns (records_created, records_updated)."""
        ...
