"""Create or recreate all Silver and Gold materialized views.

Run this script to (re)build the medallion layers:
    python -m pipeline.medallion_ddl

Or use the CLI:
    python -m pipeline.cli refresh
"""

from sqlalchemy import text
from pipeline.db import engine


def create_all():
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS gold"))

        # =====================================================================
        # SILVER LAYER
        # =====================================================================

        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS gold.anomaly_flags CASCADE"))
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS gold.restoration_outcomes CASCADE"))
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS gold.fishing_conditions CASCADE"))
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS gold.invasive_detections CASCADE"))
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS gold.water_quality_monthly CASCADE"))
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS gold.species_trends CASCADE"))
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS gold.site_ecological_summary CASCADE"))
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS gold.watershed_scorecard CASCADE"))
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS silver.species_observations CASCADE"))
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS silver.water_conditions CASCADE"))
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS silver.interventions_enriched CASCADE"))

        # --- Silver: Unified Species Observations ---
        conn.execute(text("""
            CREATE MATERIALIZED VIEW silver.species_observations AS
            SELECT
                o.id, o.site_id, s.watershed, s.name as watershed_name,
                o.source_type, o.source_id, o.observed_at,
                extract(year from o.observed_at)::int as obs_year,
                extract(month from o.observed_at)::int as obs_month,
                extract(quarter from o.observed_at)::int as obs_quarter,
                o.taxon_name, o.taxon_rank,
                COALESCE(o.iconic_taxon,
                    CASE WHEN o.source_type IN ('fish_habitat','gbif_fish') THEN 'Actinopterygii' ELSE NULL END
                ) as taxonomic_group,
                o.quality_grade,
                CASE
                    WHEN o.source_type = 'biodata' THEN 'professional_survey'
                    WHEN o.source_type = 'inaturalist' AND o.quality_grade = 'research' THEN 'citizen_science_verified'
                    WHEN o.source_type = 'inaturalist' THEN 'citizen_science_unverified'
                    WHEN o.source_type = 'fish_habitat' THEN 'agency_official'
                    WHEN o.source_type = 'gbif_fish' THEN 'museum_specimen'
                    WHEN o.source_type IN ('owri','pcsrf','noaa_restoration') THEN 'intervention_record'
                    WHEN o.source_type = 'fish_barrier' THEN 'infrastructure_record'
                    ELSE 'other'
                END as data_tier,
                o.latitude, o.longitude, o.location,
                -- Enriched fields from iNaturalist backfill
                o.data_payload->>'common_name' as common_name,
                o.data_payload->>'conservation_status' as conservation_status,
                o.data_payload->>'photo_url' as photo_url,
                o.data_payload->>'photo_license' as photo_license,
                (o.data_payload->>'positional_accuracy')::float as positional_accuracy_m,
                (o.data_payload->>'captive')::boolean as is_captive,
                (o.data_payload->>'obscured')::boolean as is_obscured,
                o.data_payload
            FROM observations o
            JOIN sites s ON s.id = o.site_id
            WHERE o.taxon_name IS NOT NULL
               OR o.source_type IN ('owri','pcsrf','noaa_restoration','fish_barrier')
        """))
        conn.execute(text("CREATE INDEX ON silver.species_observations (watershed, obs_year)"))
        conn.execute(text("CREATE INDEX ON silver.species_observations (taxonomic_group)"))
        conn.execute(text("CREATE INDEX ON silver.species_observations (taxon_name)"))
        conn.execute(text("CREATE INDEX ON silver.species_observations (site_id, observed_at)"))

        # --- Silver: Unified Water Conditions ---
        conn.execute(text("""
            CREATE MATERIALIZED VIEW silver.water_conditions AS
            SELECT
                t.id, t.site_id, s.watershed, s.name as watershed_name,
                t.source_type, t.station_id, t.timestamp,
                t.timestamp::date as obs_date,
                extract(year from t.timestamp)::int as obs_year,
                extract(month from t.timestamp)::int as obs_month,
                CASE
                    WHEN t.parameter IN ('temperature','temperature_mean') AND t.source_type IN ('usgs','owdp') THEN 'water_temperature'
                    WHEN t.parameter = 'temperature_max' AND t.source_type = 'prism' THEN 'air_temperature_max'
                    WHEN t.parameter = 'temperature_min' AND t.source_type = 'prism' THEN 'air_temperature_min'
                    WHEN t.parameter = 'temperature_mean' AND t.source_type = 'prism' THEN 'air_temperature_mean'
                    WHEN t.parameter IN ('air_temperature','air_temperature_avg') THEN 'air_temperature'
                    WHEN t.parameter IN ('dissolved_oxygen','oxygen') THEN 'dissolved_oxygen'
                    WHEN t.parameter = 'dissolved_oxygen_saturation' THEN 'do_saturation'
                    WHEN t.parameter IN ('phosphorus','orthophosphate') THEN 'phosphorus'
                    WHEN t.parameter LIKE 'nitrogen%' OR t.parameter = 'nitrate_+_nitrite' THEN 'nitrogen'
                    WHEN t.parameter LIKE 'chlorophyll%' THEN 'chlorophyll_a'
                    ELSE t.parameter
                END as parameter,
                CASE WHEN t.unit = 'degF' THEN round(((t.value - 32) * 5.0 / 9.0)::numeric, 2)
                     ELSE round(t.value::numeric, 2)
                END as value,
                CASE WHEN t.unit = 'degF' THEN 'degC'
                     WHEN t.unit IN ('deg C','degC') THEN 'degC'
                     WHEN t.unit IN ('mg/L','mg/l') THEN 'mg/L'
                     WHEN t.unit IN ('uS/cm','uS/cm @25C','umho/cm') THEN 'uS/cm'
                     ELSE t.unit
                END as unit,
                t.quality_flag,
                CASE
                    WHEN t.parameter IN ('temperature','temperature_mean','temperature_max','temperature_min','air_temperature','air_temperature_avg') THEN 'temperature'
                    WHEN t.parameter IN ('discharge','gage_height') THEN 'hydrology'
                    WHEN t.parameter IN ('dissolved_oxygen','oxygen','dissolved_oxygen_saturation') THEN 'oxygen'
                    WHEN t.parameter = 'ph' THEN 'chemistry'
                    WHEN t.parameter IN ('phosphorus','orthophosphate','nitrogen','chlorophyll_a','turbidity') THEN 'nutrients'
                    WHEN t.parameter IN ('snow_water_equivalent','snow_depth','precipitation','precipitation_cumulative','soil_moisture') THEN 'climate'
                    WHEN t.parameter LIKE 'sport_catch%' OR t.parameter = 'trout_stocked' THEN 'fishing'
                    ELSE 'other'
                END as parameter_category
            FROM time_series t
            JOIN sites s ON s.id = t.site_id
            WHERE t.value IS NOT NULL AND t.value > -999998
        """))
        conn.execute(text("CREATE INDEX ON silver.water_conditions (watershed, parameter, obs_date)"))
        conn.execute(text("CREATE INDEX ON silver.water_conditions (parameter_category)"))
        conn.execute(text("CREATE INDEX ON silver.water_conditions (site_id, parameter, timestamp)"))

        # --- Silver: Enriched Interventions ---
        conn.execute(text("""
            CREATE MATERIALIZED VIEW silver.interventions_enriched AS
            SELECT
                i.id, i.site_id, s.watershed, s.name as watershed_name,
                i.type as raw_type,
                CASE
                    WHEN i.type = 'Riparian' THEN 'riparian_restoration'
                    WHEN i.type = 'Instream' THEN 'instream_habitat'
                    WHEN i.type = 'Fish Passage' THEN 'fish_passage'
                    WHEN i.type = 'Fish Screening' THEN 'fish_screening'
                    WHEN i.type = 'Instream Flow' THEN 'flow_restoration'
                    WHEN i.type = 'Upland' THEN 'upland_restoration'
                    WHEN i.type = 'Road' THEN 'road_improvement'
                    WHEN i.type = 'Wetland' THEN 'wetland_restoration'
                    WHEN i.type LIKE 'Salmonid Habitat%' THEN 'salmon_habitat'
                    WHEN i.type LIKE 'Salmonid Restoration%' THEN 'salmon_planning'
                    WHEN i.type LIKE 'Salmonid Research%' THEN 'salmon_monitoring'
                    WHEN i.type LIKE 'Public Outreach%' THEN 'outreach'
                    ELSE 'other'
                END as intervention_category,
                i.started_at, i.completed_at,
                extract(year from COALESCE(i.started_at, i.completed_at))::int as intervention_year,
                i.description, i.location
            FROM interventions i
            JOIN sites s ON s.id = i.site_id
        """))
        conn.execute(text("CREATE INDEX ON silver.interventions_enriched (watershed, intervention_year)"))
        conn.execute(text("CREATE INDEX ON silver.interventions_enriched (intervention_category)"))

        # =====================================================================
        # GOLD LAYER
        # =====================================================================

        # --- Gold: Site Ecological Summary ---
        conn.execute(text("""
            CREATE MATERIALIZED VIEW gold.site_ecological_summary AS
            SELECT
                o.site_id, o.watershed, o.watershed_name, o.obs_year,
                count(DISTINCT o.taxon_name) as species_richness,
                count(DISTINCT CASE WHEN o.taxonomic_group = 'Plantae' THEN o.taxon_name END) as plant_species,
                count(DISTINCT CASE WHEN o.taxonomic_group = 'Aves' THEN o.taxon_name END) as bird_species,
                count(DISTINCT CASE WHEN o.taxonomic_group = 'Insecta' THEN o.taxon_name END) as insect_species,
                count(DISTINCT CASE WHEN o.taxonomic_group = 'Actinopterygii' THEN o.taxon_name END) as fish_species,
                count(DISTINCT CASE WHEN o.taxonomic_group = 'Amphibia' THEN o.taxon_name END) as amphibian_species,
                count(DISTINCT CASE WHEN o.taxonomic_group = 'Fungi' THEN o.taxon_name END) as fungi_species,
                count(*) as total_observations,
                count(CASE WHEN o.data_tier = 'professional_survey' THEN 1 END) as professional_obs,
                count(CASE WHEN o.data_tier = 'citizen_science_verified' THEN 1 END) as verified_citizen_obs,
                count(DISTINCT o.taxonomic_group) as taxonomic_groups_observed
            FROM silver.species_observations o
            WHERE o.obs_year >= 2019 AND o.taxon_name IS NOT NULL
            GROUP BY o.site_id, o.watershed, o.watershed_name, o.obs_year
        """))
        conn.execute(text("CREATE INDEX ON gold.site_ecological_summary (watershed, obs_year)"))

        # --- Gold: Species Trends ---
        conn.execute(text("""
            CREATE MATERIALIZED VIEW gold.species_trends AS
            WITH yearly AS (
                SELECT site_id, watershed, obs_year,
                       count(DISTINCT taxon_name) as species_count, count(*) as obs_count
                FROM silver.species_observations
                WHERE taxon_name IS NOT NULL AND obs_year >= 2019
                GROUP BY site_id, watershed, obs_year
            )
            SELECT y.site_id, y.watershed, y.obs_year, y.species_count, y.obs_count,
                   lag(y.species_count) OVER (PARTITION BY y.site_id ORDER BY y.obs_year) as prev_year_species,
                   y.species_count - lag(y.species_count) OVER (PARTITION BY y.site_id ORDER BY y.obs_year) as species_delta,
                   CASE WHEN lag(y.species_count) OVER (PARTITION BY y.site_id ORDER BY y.obs_year) > 0
                        THEN round(((y.species_count::float / lag(y.species_count) OVER (PARTITION BY y.site_id ORDER BY y.obs_year) - 1) * 100)::numeric, 1)
                   END as species_pct_change
            FROM yearly y
        """))
        conn.execute(text("CREATE INDEX ON gold.species_trends (watershed, obs_year)"))

        # --- Gold: Water Quality Monthly ---
        conn.execute(text("""
            CREATE MATERIALIZED VIEW gold.water_quality_monthly AS
            SELECT
                w.site_id, w.watershed, w.station_id, w.parameter, w.unit, w.parameter_category,
                w.obs_year, w.obs_month,
                round(avg(w.value)::numeric, 2) as avg_value,
                round(min(w.value)::numeric, 2) as min_value,
                round(max(w.value)::numeric, 2) as max_value,
                count(*) as reading_count,
                count(CASE WHEN w.parameter = 'water_temperature' AND w.value > 18 THEN 1 END) as temp_above_18c,
                count(CASE WHEN w.parameter = 'dissolved_oxygen' AND w.value < 6 THEN 1 END) as do_below_6
            FROM silver.water_conditions w
            WHERE w.parameter_category IN ('temperature','hydrology','oxygen','chemistry','nutrients')
              AND w.obs_year >= 2020
            GROUP BY w.site_id, w.watershed, w.station_id, w.parameter, w.unit, w.parameter_category, w.obs_year, w.obs_month
        """))
        conn.execute(text("CREATE INDEX ON gold.water_quality_monthly (watershed, parameter, obs_year, obs_month)"))

        # --- Gold: Invasive Detections ---
        conn.execute(text("""
            CREATE MATERIALIZED VIEW gold.invasive_detections AS
            SELECT
                o.site_id, o.watershed, o.watershed_name, o.taxon_name, o.taxonomic_group,
                count(*) as detection_count,
                min(o.observed_at)::date as first_detected,
                max(o.observed_at)::date as last_detected,
                count(DISTINCT o.obs_year) as years_detected,
                count(CASE WHEN o.obs_year >= 2024 THEN 1 END) as recent_detections,
                count(CASE WHEN o.obs_year < 2024 THEN 1 END) as prior_detections
            FROM silver.species_observations o
            WHERE o.taxon_name IN (
                'Reynoutria japonica','Fallopia japonica','Phalaris arundinacea',
                'Myriophyllum spicatum','Potamogeton crispus','Cirsium arvense',
                'Cirsium vulgare','Centaurea stoebe','Cytisus scoparius',
                'Rubus armeniacus','Hedera helix','Lithobates catesbeianus',
                'Procambarus clarkii','Elodea canadensis','Iris pseudacorus',
                'Robinia pseudoacacia'
            )
            GROUP BY o.site_id, o.watershed, o.watershed_name, o.taxon_name, o.taxonomic_group
        """))
        conn.execute(text("CREATE INDEX ON gold.invasive_detections (watershed)"))

        # --- Gold: Fishing Conditions ---
        conn.execute(text("""
            CREATE MATERIALIZED VIEW gold.fishing_conditions AS
            SELECT
                w.site_id, w.watershed, w.obs_year, w.obs_month,
                round(avg(CASE WHEN w.parameter = 'water_temperature' AND w.source_type = 'usgs' THEN w.value END)::numeric, 1) as avg_water_temp_c,
                round(max(CASE WHEN w.parameter = 'water_temperature' AND w.source_type = 'usgs' THEN w.value END)::numeric, 1) as max_water_temp_c,
                round(avg(CASE WHEN w.parameter = 'discharge' THEN w.value END)::numeric, 0) as avg_discharge_cfs,
                round(avg(CASE WHEN w.parameter = 'dissolved_oxygen' THEN w.value END)::numeric, 1) as avg_do_mg_l,
                sum(CASE WHEN w.parameter = 'sport_catch_steelhead' THEN w.value END)::int as steelhead_harvest,
                sum(CASE WHEN w.parameter = 'sport_catch_chinook' THEN w.value END)::int as chinook_harvest,
                sum(CASE WHEN w.parameter = 'sport_catch_coho' THEN w.value END)::int as coho_harvest,
                sum(CASE WHEN w.parameter = 'trout_stocked' THEN w.value END)::int as trout_stocked
            FROM silver.water_conditions w
            WHERE w.obs_year >= 2020
            GROUP BY w.site_id, w.watershed, w.obs_year, w.obs_month
        """))
        conn.execute(text("CREATE INDEX ON gold.fishing_conditions (watershed, obs_year, obs_month)"))

        # --- Gold: Restoration Outcomes ---
        conn.execute(text("""
            CREATE MATERIALIZED VIEW gold.restoration_outcomes AS
            SELECT
                i.site_id, i.watershed, i.intervention_category, i.intervention_year,
                count(*) as intervention_count,
                (SELECT count(DISTINCT o.taxon_name) FROM silver.species_observations o
                 WHERE o.site_id = i.site_id AND o.obs_year BETWEEN i.intervention_year - 2 AND i.intervention_year - 1
                   AND o.taxon_name IS NOT NULL) as species_before,
                (SELECT count(DISTINCT o.taxon_name) FROM silver.species_observations o
                 WHERE o.site_id = i.site_id AND o.obs_year BETWEEN i.intervention_year + 1 AND i.intervention_year + 2
                   AND o.taxon_name IS NOT NULL) as species_after
            FROM silver.interventions_enriched i
            WHERE i.intervention_year IS NOT NULL AND i.intervention_year >= 2015
              AND i.intervention_category NOT IN ('outreach','salmon_planning','salmon_monitoring','other')
            GROUP BY i.site_id, i.watershed, i.intervention_category, i.intervention_year
        """))
        conn.execute(text("CREATE INDEX ON gold.restoration_outcomes (watershed, intervention_year)"))

        # --- Gold: Watershed Scorecard ---
        conn.execute(text("""
            CREATE MATERIALIZED VIEW gold.watershed_scorecard AS
            SELECT
                s.watershed, s.name as watershed_name,
                (SELECT count(*) FROM observations o WHERE o.site_id = s.id) as total_observations,
                (SELECT count(*) FROM time_series t WHERE t.site_id = s.id) as total_time_series,
                (SELECT count(*) FROM interventions i WHERE i.site_id = s.id) as total_interventions,
                (SELECT count(DISTINCT o.taxon_name) FROM observations o WHERE o.site_id = s.id AND o.taxon_name IS NOT NULL) as total_species,
                (SELECT count(DISTINCT o.taxon_name) FROM observations o WHERE o.site_id = s.id AND o.iconic_taxon = 'Actinopterygii') as fish_species,
                (SELECT count(DISTINCT o.taxon_name) FROM observations o WHERE o.site_id = s.id AND o.iconic_taxon = 'Amphibia') as amphibian_species,
                (SELECT count(DISTINCT t.station_id) FROM time_series t WHERE t.site_id = s.id AND t.source_type = 'usgs') as usgs_stations,
                (SELECT count(DISTINCT t.station_id) FROM time_series t WHERE t.site_id = s.id AND t.source_type = 'snotel') as snotel_stations,
                (SELECT count(*) FROM stream_flowlines f WHERE f.site_id = s.id) as stream_reaches,
                (SELECT count(*) FROM wetlands w WHERE w.site_id = s.id) as wetland_polygons,
                (SELECT count(*) FROM fire_perimeters fp WHERE fp.site_id = s.id) as fire_events,
                (SELECT count(*) FROM impaired_waters iw WHERE iw.site_id = s.id) as impaired_segments,
                (SELECT count(*) FROM watershed_boundaries wb WHERE wb.site_id = s.id) as huc12_count
            FROM sites s
        """))

        # --- Gold: Anomaly Flags ---
        conn.execute(text("""
            CREATE MATERIALIZED VIEW gold.anomaly_flags AS
            SELECT 'temperature_exceedance' as anomaly_type,
                   w.site_id, w.watershed, w.station_id, w.obs_date as detected_date,
                   w.value as measured_value, 18.0 as threshold, 'degC' as unit,
                   'Water temperature exceeded 18C salmonid stress threshold' as description
            FROM silver.water_conditions w
            WHERE w.parameter = 'water_temperature' AND w.value > 18 AND w.obs_year >= 2024
            UNION ALL
            SELECT 'low_dissolved_oxygen', w.site_id, w.watershed, w.station_id, w.obs_date,
                   w.value, 6.0, 'mg/L',
                   'Dissolved oxygen dropped below 6 mg/L fish survival threshold'
            FROM silver.water_conditions w
            WHERE w.parameter = 'dissolved_oxygen' AND w.value < 6 AND w.obs_year >= 2024
        """))
        conn.execute(text("CREATE INDEX ON gold.anomaly_flags (watershed, detected_date)"))
        conn.execute(text("CREATE INDEX ON gold.anomaly_flags (anomaly_type)"))

        conn.commit()
        print("All materialized views created.")


if __name__ == "__main__":
    create_all()
