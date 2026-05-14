"""CLI for RiverSignal data ingestion pipelines."""

import click
from rich.console import Console
from rich.table import Table

from pipeline.config.watersheds import WATERSHEDS
from pipeline.db import engine, get_session
from pipeline.models import Observation, Site, TimeSeries

console = Console()


def get_or_create_site(session, watershed_key: str) -> Site:
    """Get existing site or create one from watershed config."""
    config = WATERSHEDS[watershed_key]
    site = session.query(Site).filter_by(watershed=watershed_key).first()
    if not site:
        site = Site(
            name=config["name"],
            watershed=watershed_key,
            bbox=config["bbox"],
            huc12_codes=[],
        )
        session.add(site)
        session.flush()
        console.print(f"  Created site: {config['name']} ({site.id})")
    return site


@click.group()
def main():
    """RiverSignal data ingestion platform."""
    pass


@main.command()
@click.argument(
    "source", type=click.Choice(["inaturalist", "usgs", "wqp", "snotel", "biodata", "streamnet", "mtbs", "nhdplus", "restoration", "fish_passage", "prism", "impaired", "wetlands", "wbd", "fishing", "macrostrat", "pbdb", "blm_sma", "dogami", "mrds", "idigbio", "recreation", "wqp_bugs", "gbif", "washington", "utah", "all"])
)
@click.option(
    "--watershed", "-w",
    type=click.Choice(list(WATERSHEDS.keys()) + ["all"]),
    default="all",
    help="Watershed to ingest (default: all)",
)
@click.option(
    "--from-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Override the adapter's default lookback start date (YYYY-MM-DD). "
         "Used for backfill runs. Without this, each adapter uses its built-in "
         "delta-sync logic (last_sync timestamp).",
)
def ingest(source: str, watershed: str, from_date):
    """Run ingestion pipeline for a data source."""
    from pipeline.ingest.biodata import BioDataAdapter
    from pipeline.ingest.fish_passage import FishPassageAdapter
    from pipeline.ingest.fishing import FishingDataAdapter
    from pipeline.ingest.geology import (
        BLMLandOwnershipAdapter, DOGAMIAdapter, GeologicUnitsAdapter,
        IDigBioFossilAdapter, MRDSAdapter, PBDBFossilAdapter,
    )
    from pipeline.ingest.inaturalist import INaturalistAdapter
    from pipeline.ingest.spatial import ImpairedWatersAdapter, WatershedBoundaryAdapter, WetlandsAdapter
    from pipeline.ingest.mtbs import MTBSAdapter
    from pipeline.ingest.nhdplus import NHDPlusAdapter
    from pipeline.ingest.owdp import OWDPAdapter
    from pipeline.ingest.prism import PRISMAdapter
    from pipeline.ingest.restoration import RestorationAdapter
    from pipeline.ingest.snotel import SNOTELAdapter
    from pipeline.ingest.streamnet import StreamNetAdapter
    from pipeline.ingest.gbif import GBIFFossilAdapter
    from pipeline.ingest.recreation import RecreationAdapter
    from pipeline.ingest.usgs import USGSAdapter
    from pipeline.ingest.utah import UtahDataAdapter
    from pipeline.ingest.washington import WashingtonDataAdapter
    from pipeline.ingest.wqp_bugs import WQPBugsAdapter

    adapters = {
        "inaturalist": INaturalistAdapter,
        "usgs": USGSAdapter,
        "wqp": OWDPAdapter,
        "snotel": SNOTELAdapter,
        "biodata": BioDataAdapter,
        "streamnet": StreamNetAdapter,
        "mtbs": MTBSAdapter,
        "nhdplus": NHDPlusAdapter,
        "restoration": RestorationAdapter,
        "fish_passage": FishPassageAdapter,
        "prism": PRISMAdapter,
        "fishing": FishingDataAdapter,
        "impaired": ImpairedWatersAdapter,
        "wetlands": WetlandsAdapter,
        "wbd": WatershedBoundaryAdapter,
        "macrostrat": GeologicUnitsAdapter,
        "pbdb": PBDBFossilAdapter,
        "blm_sma": BLMLandOwnershipAdapter,
        "dogami": DOGAMIAdapter,
        "mrds": MRDSAdapter,
        "idigbio": IDigBioFossilAdapter,
        "gbif": GBIFFossilAdapter,
        "recreation": RecreationAdapter,
        "wqp_bugs": WQPBugsAdapter,
        "utah": UtahDataAdapter,
        "washington": WashingtonDataAdapter,
    }

    watersheds = list(WATERSHEDS.keys()) if watershed == "all" else [watershed]
    sources = list(adapters.keys()) if source == "all" else [source]
    from_date_arg = from_date.date() if from_date else None
    if from_date_arg:
        console.print(f"[yellow]Backfill mode: from {from_date_arg}[/yellow]")

    session = get_session()
    try:
        for ws in watersheds:
            console.print(f"\n[bold]{WATERSHEDS[ws]['name']}[/bold]")
            site = get_or_create_site(session, ws)

            for src in sources:
                adapter = adapters[src](session, site.id, from_date=from_date_arg)
                adapter.run()
    finally:
        session.close()

    from app.routers.data_status import refresh_data_status_cache
    refresh_data_status_cache()
    console.print("[dim]Refreshed /data-status cache.[/dim]")


@main.command()
@click.option("--mode", "-m", type=click.Choice(["all", "light", "heavy"]), default="all",
              help="all=everything, light=silver+fast gold, heavy=slow gold only")
def refresh(mode: str):
    """Refresh Silver and Gold layer materialized views."""
    from pipeline.medallion import refresh_all, refresh_light, refresh_heavy

    console.print(f"\n[bold]Refreshing medallion layers ({mode})...[/bold]")
    if mode == "light":
        refresh_light()
    elif mode == "heavy":
        refresh_heavy()
    else:
        refresh_all()
    from app.routers.data_status import refresh_data_status_cache
    refresh_data_status_cache()
    console.print("[green]Done.[/green]")


@main.command()
@click.option("--from-date", required=True, type=click.DateTime(formats=["%Y-%m-%d"]),
              help="Backcast start date (YYYY-MM-DD), inclusive.")
@click.option("--to-date", required=False, type=click.DateTime(formats=["%Y-%m-%d"]),
              default=None, help="Backcast end date (YYYY-MM-DD), inclusive. Defaults to yesterday.")
@click.option("--chunk-days", type=int, default=30,
              help="Process this many days per insert chunk (default: 30).")
def backcast_tqs(from_date, to_date, chunk_days):
    """Backcast Trip Quality Score history over a date range.

    Writes rows into gold.trip_quality_history with forecast_source='backcast'.
    Does not touch gold.trip_quality_daily. Idempotent via composite PK.
    """
    from datetime import date as _date, timedelta as _td
    from pipeline.predictions.trip_quality import backcast_history

    start = from_date.date()
    end = to_date.date() if to_date else (_date.today() - _td(days=1))
    console.print(f"\n[bold]Backcasting TQS from {start} to {end}[/bold]")
    n = backcast_history(start, end, chunk_days=chunk_days)
    console.print(f"[green]Done. {n} backcast rows written.[/green]")


@main.command()
def status():
    """Show data status for all watersheds."""
    session = get_session()
    try:
        table = Table(title="Watershed Data Status")
        table.add_column("Watershed", style="bold")
        table.add_column("Observations", justify="right")
        table.add_column("Species", justify="right")
        table.add_column("Time Series", justify="right")
        table.add_column("USGS Stations", justify="right")
        table.add_column("WQP Stations", justify="right")
        table.add_column("Date Range")

        from sqlalchemy import func, distinct, text

        for ws_key, ws_config in WATERSHEDS.items():
            site = session.query(Site).filter_by(watershed=ws_key).first()
            if not site:
                table.add_row(ws_config["name"], "—", "—", "—", "—", "—", "not configured")
                continue

            obs_count = (
                session.query(func.count(Observation.id))
                .filter_by(site_id=site.id)
                .scalar()
            )
            species_count = (
                session.query(func.count(distinct(Observation.taxon_name)))
                .filter(Observation.site_id == site.id, Observation.taxon_name.isnot(None))
                .scalar()
            )
            ts_count = (
                session.query(func.count(TimeSeries.id))
                .filter_by(site_id=site.id)
                .scalar()
            )
            usgs_stations = (
                session.query(func.count(distinct(TimeSeries.station_id)))
                .filter(TimeSeries.site_id == site.id, TimeSeries.source_type == "usgs")
                .scalar()
            )
            wqp_stations = (
                session.query(func.count(distinct(TimeSeries.station_id)))
                .filter(TimeSeries.site_id == site.id, TimeSeries.source_type == "owdp")
                .scalar()
            )

            min_date = session.query(func.min(Observation.observed_at)).filter_by(site_id=site.id).scalar()
            max_date = session.query(func.max(Observation.observed_at)).filter_by(site_id=site.id).scalar()

            date_range = "no data"
            if min_date and max_date:
                date_range = f"{min_date.strftime('%Y-%m-%d')} → {max_date.strftime('%Y-%m-%d')}"

            table.add_row(
                ws_config["name"],
                f"{obs_count:,}",
                f"{species_count:,}",
                f"{ts_count:,}",
                str(usgs_stations),
                str(wqp_stations),
                date_range,
            )

        console.print(table)
    finally:
        session.close()


@main.command()
def fossil_images():
    """Backfill fossil specimen images from iDigBio, MorphoSource, and Smithsonian."""
    from pipeline.ingest.fossil_images import backfill_all_fossil_images
    backfill_all_fossil_images()


@main.command()
def compare():
    """Generate detailed comparison report across all watersheds."""
    from sqlalchemy import func, distinct

    session = get_session()
    try:
        console.print("\n[bold]Watershed Comparison Report[/bold]\n")

        for ws_key, ws_config in WATERSHEDS.items():
            site = session.query(Site).filter_by(watershed=ws_key).first()
            if not site:
                console.print(f"[dim]{ws_config['name']}: no data[/dim]\n")
                continue

            console.print(f"[bold cyan]{ws_config['name']}[/bold cyan]")

            # Observation stats
            obs_count = session.query(func.count(Observation.id)).filter_by(site_id=site.id).scalar()
            species = session.query(func.count(distinct(Observation.taxon_name))).filter(
                Observation.site_id == site.id, Observation.taxon_name.isnot(None)
            ).scalar()
            research_grade = session.query(func.count(Observation.id)).filter(
                Observation.site_id == site.id, Observation.quality_grade == "research"
            ).scalar()

            console.print(f"  Observations: {obs_count:,} ({research_grade:,} research grade)")
            console.print(f"  Unique species: {species:,}")

            # Taxonomic breakdown
            iconic_counts = (
                session.query(Observation.iconic_taxon, func.count(Observation.id))
                .filter(Observation.site_id == site.id, Observation.iconic_taxon.isnot(None))
                .group_by(Observation.iconic_taxon)
                .order_by(func.count(Observation.id).desc())
                .all()
            )
            if iconic_counts:
                breakdown = ", ".join(f"{name}: {count}" for name, count in iconic_counts[:8])
                console.print(f"  Taxa breakdown: {breakdown}")

            # Time series stats
            ts_count = session.query(func.count(TimeSeries.id)).filter_by(site_id=site.id).scalar()
            usgs_params = (
                session.query(distinct(TimeSeries.parameter))
                .filter(TimeSeries.site_id == site.id, TimeSeries.source_type == "usgs")
                .all()
            )
            wqp_params = (
                session.query(distinct(TimeSeries.parameter))
                .filter(TimeSeries.site_id == site.id, TimeSeries.source_type == "owdp")
                .all()
            )

            console.print(f"  Time series records: {ts_count:,}")
            if usgs_params:
                console.print(f"  USGS parameters: {', '.join(p[0] for p in usgs_params)}")
            if wqp_params:
                console.print(f"  WQP parameters: {', '.join(p[0] for p in wqp_params[:10])}")

            # Date coverage
            obs_min = session.query(func.min(Observation.observed_at)).filter_by(site_id=site.id).scalar()
            obs_max = session.query(func.max(Observation.observed_at)).filter_by(site_id=site.id).scalar()
            ts_min = session.query(func.min(TimeSeries.timestamp)).filter_by(site_id=site.id).scalar()
            ts_max = session.query(func.max(TimeSeries.timestamp)).filter_by(site_id=site.id).scalar()

            if obs_min:
                console.print(f"  Observation range: {obs_min.strftime('%Y-%m-%d')} → {obs_max.strftime('%Y-%m-%d')}")
            if ts_min:
                console.print(f"  Time series range: {ts_min.strftime('%Y-%m-%d')} → {ts_max.strftime('%Y-%m-%d')}")

            console.print()

    finally:
        session.close()


if __name__ == "__main__":
    main()
