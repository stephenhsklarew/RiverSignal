"""Run all 5 predictive models."""

from rich.console import Console

console = Console()


def refresh_predictions():
    """Run all prediction models and update gold tables."""
    console.print("\n  [bold]Phase 4: Predictive models[/bold]")

    from pipeline.predictions.hatch_forecast import refresh_hatch_forecast
    from pipeline.predictions.catch_forecast import refresh_catch_forecast
    from pipeline.predictions.health_anomaly import refresh_health_anomaly
    from pipeline.predictions.species_distribution import refresh_species_distribution
    from pipeline.predictions.restoration_impact import refresh_restoration_forecast

    refresh_hatch_forecast()
    refresh_catch_forecast()
    refresh_health_anomaly()
    refresh_species_distribution()
    refresh_restoration_forecast()

    console.print("  [green]All prediction models complete.[/green]")
