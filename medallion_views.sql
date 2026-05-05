-- Medallion Architecture View Definitions
-- Exported from database, 39 views
-- Re-run: python -m pipeline.medallion_ddl

CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- silver.species_observations
DROP MATERIALIZED VIEW IF EXISTS silver.species_observations CASCADE;
CREATE MATERIALIZED VIEW silver.species_observations AS
 SELECT o.id,
    o.site_id,
    s.watershed,
    s.name AS watershed_name,
    o.source_type,
    o.source_id,
    o.observed_at,
    EXTRACT(year FROM o.observed_at)::integer AS obs_year,
    EXTRACT(month FROM o.observed_at)::integer AS obs_month,
    EXTRACT(quarter FROM o.observed_at)::integer AS obs_quarter,
    o.taxon_name,
    o.taxon_rank,
    COALESCE(o.iconic_taxon,
        CASE
            WHEN o.source_type::text = ANY (ARRAY['fish_habitat'::character varying, 'gbif_fish'::character varying]::text[]) THEN 'Actinopterygii'::text
            ELSE NULL::text
        END::character varying) AS taxonomic_group,
    o.quality_grade,
        CASE
            WHEN o.source_type::text = 'biodata'::text THEN 'professional_survey'::text
            WHEN o.source_type::text = 'inaturalist'::text AND o.quality_grade::text = 'research'::text THEN 'citizen_science_verified'::text
            WHEN o.source_type::text = 'inaturalist'::text THEN 'citizen_science_unverified'::text
            WHEN o.source_type::text = 'fish_habitat'::text THEN 'agency_official'::text
            WHEN o.source_type::text = 'gbif_fish'::text THEN 'museum_specimen'::text
            WHEN o.source_type::text = ANY (ARRAY['owri'::character varying, 'pcsrf'::character varying, 'noaa_restoration'::character varying]::text[]) THEN 'intervention_record'::text
            WHEN o.source_type::text = 'fish_barrier'::text THEN 'infrastructure_record'::text
            ELSE 'other'::text
        END AS data_tier,
    o.latitude,
    o.longitude,
    o.location,
    o.data_payload ->> 'common_name'::text AS common_name,
    o.data_payload ->> 'conservation_status'::text AS conservation_status,
    o.data_payload ->> 'photo_url'::text AS photo_url,
    o.data_payload ->> 'photo_license'::text AS photo_license,
    o.data_payload
   FROM observations o
     JOIN sites s ON s.id = o.site_id
  WHERE o.taxon_name IS NOT NULL OR (o.source_type::text = ANY (ARRAY['owri'::character varying, 'pcsrf'::character varying, 'noaa_restoration'::character varying, 'fish_barrier'::character varying]::text[]));;

-- silver.water_conditions
DROP MATERIALIZED VIEW IF EXISTS silver.water_conditions CASCADE;
CREATE MATERIALIZED VIEW silver.water_conditions AS
 SELECT t.id,
    t.site_id,
    s.watershed,
    s.name AS watershed_name,
    t.source_type,
    t.station_id,
    t."timestamp",
    t."timestamp"::date AS obs_date,
    EXTRACT(year FROM t."timestamp")::integer AS obs_year,
    EXTRACT(month FROM t."timestamp")::integer AS obs_month,
        CASE
            WHEN (t.parameter::text = ANY (ARRAY['temperature'::character varying::text, 'temperature_mean'::character varying::text])) AND (t.source_type::text = ANY (ARRAY['usgs'::character varying::text, 'owdp'::character varying::text])) THEN 'water_temperature'::character varying
            WHEN t.parameter::text = 'temperature_max'::text AND t.source_type::text = 'prism'::text THEN 'air_temperature_max'::character varying
            WHEN t.parameter::text = 'temperature_min'::text AND t.source_type::text = 'prism'::text THEN 'air_temperature_min'::character varying
            WHEN t.parameter::text = 'temperature_mean'::text AND t.source_type::text = 'prism'::text THEN 'air_temperature_mean'::character varying
            WHEN t.parameter::text = ANY (ARRAY['air_temperature'::character varying::text, 'air_temperature_avg'::character varying::text]) THEN 'air_temperature'::character varying
            WHEN t.parameter::text = ANY (ARRAY['dissolved_oxygen'::character varying::text, 'oxygen'::character varying::text]) THEN 'dissolved_oxygen'::character varying
            WHEN t.parameter::text = 'dissolved_oxygen_saturation'::text THEN 'do_saturation'::character varying
            WHEN t.parameter::text = ANY (ARRAY['phosphorus'::character varying::text, 'orthophosphate'::character varying::text]) THEN 'phosphorus'::character varying
            WHEN t.parameter::text ~~ 'nitrogen%'::text OR t.parameter::text = 'nitrate_+_nitrite'::text THEN 'nitrogen'::character varying
            WHEN t.parameter::text ~~ 'chlorophyll%'::text THEN 'chlorophyll_a'::character varying
            ELSE t.parameter
        END AS parameter,
        CASE
            WHEN t.unit::text = 'degF'::text THEN round(((t.value - 32::double precision) * 5.0::double precision / 9.0::double precision)::numeric, 2)
            ELSE round(t.value::numeric, 2)
        END AS value,
        CASE
            WHEN t.unit::text = 'degF'::text THEN 'degC'::character varying
            WHEN t.unit::text = ANY (ARRAY['deg C'::character varying::text, 'degC'::character varying::text]) THEN 'degC'::character varying
            WHEN t.unit::text = ANY (ARRAY['mg/L'::character varying::text, 'mg/l'::character varying::text]) THEN 'mg/L'::character varying
            WHEN t.unit::text = ANY (ARRAY['uS/cm'::character varying::text, 'uS/cm @25C'::character varying::text, 'umho/cm'::character varying::text]) THEN 'uS/cm'::character varying
            ELSE t.unit
        END AS unit,
    t.quality_flag,
        CASE
            WHEN t.parameter::text = ANY (ARRAY['temperature'::character varying::text, 'temperature_mean'::character varying::text, 'temperature_max'::character varying::text, 'temperature_min'::character varying::text, 'air_temperature'::character varying::text, 'air_temperature_avg'::character varying::text]) THEN 'temperature'::text
            WHEN t.parameter::text = ANY (ARRAY['discharge'::character varying::text, 'gage_height'::character varying::text]) THEN 'hydrology'::text
            WHEN t.parameter::text = ANY (ARRAY['dissolved_oxygen'::character varying::text, 'oxygen'::character varying::text, 'dissolved_oxygen_saturation'::character varying::text]) THEN 'oxygen'::text
            WHEN t.parameter::text = 'ph'::text THEN 'chemistry'::text
            WHEN t.parameter::text = ANY (ARRAY['phosphorus'::character varying::text, 'orthophosphate'::character varying::text, 'nitrogen'::character varying::text, 'chlorophyll_a'::character varying::text, 'turbidity'::character varying::text]) THEN 'nutrients'::text
            WHEN t.parameter::text = ANY (ARRAY['snow_water_equivalent'::character varying::text, 'snow_depth'::character varying::text, 'precipitation'::character varying::text, 'precipitation_cumulative'::character varying::text, 'soil_moisture'::character varying::text]) THEN 'climate'::text
            WHEN t.parameter::text ~~ 'sport_catch%'::text OR t.parameter::text = 'trout_stocked'::text THEN 'fishing'::text
            ELSE 'other'::text
        END AS parameter_category
   FROM time_series t
     JOIN sites s ON s.id = t.site_id
  WHERE t.value IS NOT NULL AND t.value > '-999998'::integer::double precision;;

-- silver.interventions_enriched
DROP MATERIALIZED VIEW IF EXISTS silver.interventions_enriched CASCADE;
CREATE MATERIALIZED VIEW silver.interventions_enriched AS
 SELECT i.id,
    i.site_id,
    s.watershed,
    s.name AS watershed_name,
    i.type AS raw_type,
        CASE
            WHEN i.type::text = 'Riparian'::text THEN 'Riparian Restoration'::text
            WHEN i.type::text = 'Instream'::text THEN 'Instream Habitat'::text
            WHEN i.type::text = 'Fish Passage'::text THEN 'Fish Passage'::text
            WHEN i.type::text = 'Fish Screening'::text THEN 'Fish Screening'::text
            WHEN i.type::text = 'Instream Flow'::text THEN 'Flow Restoration'::text
            WHEN i.type::text = 'Upland'::text THEN 'Upland Restoration'::text
            WHEN i.type::text = 'Road'::text THEN 'Road Improvement'::text
            WHEN i.type::text = 'Wetland'::text THEN 'Wetland Restoration'::text
            WHEN i.type::text ~~ 'Salmonid Habitat%'::text THEN 'Salmon Habitat'::text
            WHEN i.type::text ~~ 'Salmonid Restoration%'::text THEN 'Salmon Planning'::text
            WHEN i.type::text ~~ 'Salmonid Research%'::text THEN 'Salmon Monitoring'::text
            ELSE replace(initcap(COALESCE(i.type, 'Other'::character varying)::text), '_'::text, ' '::text)
        END AS intervention_category,
    i.started_at,
    i.completed_at,
    EXTRACT(year FROM COALESCE(i.completed_at, i.started_at))::integer AS intervention_year,
    i.description,
    i.location
   FROM interventions i
     JOIN sites s ON i.site_id = s.id;;

-- silver.geologic_context
DROP MATERIALIZED VIEW IF EXISTS silver.geologic_context CASCADE;
CREATE MATERIALIZED VIEW silver.geologic_context AS
 SELECT id,
    source,
    source_id,
    unit_name,
    formation,
    COALESCE(rock_type, 'unknown'::character varying) AS rock_type,
    lithology,
    age_min_ma,
    age_max_ma,
    COALESCE(period, 'Unknown'::character varying) AS period,
    description,
    geometry,
        CASE
            WHEN age_max_ma IS NOT NULL AND age_min_ma IS NOT NULL THEN round(((age_max_ma + age_min_ma) / 2::double precision)::numeric, 2)::double precision
            ELSE age_max_ma
        END AS age_midpoint_ma,
    ingested_at
   FROM geologic_units gu
  WHERE geometry IS NOT NULL;;

-- silver.fossil_records
DROP MATERIALIZED VIEW IF EXISTS silver.fossil_records CASCADE;
CREATE MATERIALIZED VIEW silver.fossil_records AS
 SELECT id,
    source,
    source_id,
    taxon_name,
    taxon_id,
    common_name,
    phylum,
    class_name,
    order_name,
    family,
    age_min_ma,
    age_max_ma,
    COALESCE(period, 'Unknown'::character varying) AS period,
    formation,
    location,
    latitude,
    longitude,
    collector,
    reference,
    museum,
        CASE
            WHEN age_max_ma IS NOT NULL AND age_min_ma IS NOT NULL THEN round(((age_max_ma + age_min_ma) / 2::double precision)::numeric, 2)::double precision
            ELSE age_max_ma
        END AS age_midpoint_ma,
    image_url,
    image_license,
    data_payload ->> 'morphosource_url'::text AS morphosource_url,
    ingested_at
   FROM fossil_occurrences
  WHERE taxon_name IS NOT NULL AND taxon_name::text <> ''::text;;

-- silver.land_access
DROP MATERIALIZED VIEW IF EXISTS silver.land_access CASCADE;
CREATE MATERIALIZED VIEW silver.land_access AS
 SELECT id,
    source,
    source_id,
    agency,
    designation,
    admin_unit,
    collecting_status,
    collecting_rules,
        CASE collecting_status
            WHEN 'permitted'::text THEN 'green'::text
            WHEN 'restricted'::text THEN 'yellow'::text
            WHEN 'prohibited'::text THEN 'red'::text
            ELSE 'gray'::text
        END AS status_color,
    geometry,
    ingested_at
   FROM land_ownership lo;;

-- silver.mineral_sites
DROP MATERIALIZED VIEW IF EXISTS silver.mineral_sites CASCADE;
CREATE MATERIALIZED VIEW silver.mineral_sites AS
 SELECT id,
    source,
    source_id,
    site_name,
    commodity,
    dev_status,
    location,
    latitude,
    longitude,
    image_url,
    image_license,
    image_source,
    ingested_at
   FROM mineral_deposits
  WHERE site_name IS NOT NULL AND site_name::text <> ''::text AND site_name::text !~~* 'Unnamed%'::text;;

-- gold.anomaly_flags
DROP MATERIALIZED VIEW IF EXISTS gold.anomaly_flags CASCADE;
CREATE MATERIALIZED VIEW gold.anomaly_flags AS
 SELECT 'temperature_exceedance'::text AS anomaly_type,
    w.site_id,
    w.watershed,
    w.station_id,
    w.obs_date AS detected_date,
    w.value AS measured_value,
    18.0 AS threshold,
    'degC'::text AS unit,
    'Water temperature exceeded 18C salmonid stress threshold'::text AS description
   FROM silver.water_conditions w
  WHERE w.parameter::text = 'water_temperature'::text AND w.value > 18::numeric AND w.obs_year >= 2024
UNION ALL
 SELECT 'low_dissolved_oxygen'::text AS anomaly_type,
    w.site_id,
    w.watershed,
    w.station_id,
    w.obs_date AS detected_date,
    w.value AS measured_value,
    6.0 AS threshold,
    'mg/L'::text AS unit,
    'Dissolved oxygen dropped below 6 mg/L fish survival threshold'::text AS description
   FROM silver.water_conditions w
  WHERE w.parameter::text = 'dissolved_oxygen'::text AND w.value < 6::numeric AND w.obs_year >= 2024;;

-- gold.cold_water_refuges
DROP MATERIALIZED VIEW IF EXISTS gold.cold_water_refuges CASCADE;
CREATE MATERIALIZED VIEW gold.cold_water_refuges AS
 WITH sst AS (
         SELECT w.site_id,
            w.watershed,
            w.station_id,
            w.source_type,
            w.obs_year,
            round(avg(
                CASE
                    WHEN w.obs_month >= 6 AND w.obs_month <= 8 THEN w.value
                    ELSE NULL::numeric
                END), 1) AS summer_avg_temp,
            round(max(
                CASE
                    WHEN w.obs_month >= 6 AND w.obs_month <= 8 THEN w.value
                    ELSE NULL::numeric
                END), 1) AS summer_max_temp,
            count(
                CASE
                    WHEN w.obs_month >= 6 AND w.obs_month <= 8 THEN 1
                    ELSE NULL::integer
                END) AS summer_readings,
            count(
                CASE
                    WHEN w.obs_month >= 6 AND w.obs_month <= 8 AND w.value > 18::numeric THEN 1
                    ELSE NULL::integer
                END) AS days_above_18c,
            count(
                CASE
                    WHEN w.obs_month >= 6 AND w.obs_month <= 8 AND w.value > 20::numeric THEN 1
                    ELSE NULL::integer
                END) AS days_above_20c
           FROM silver.water_conditions w
          WHERE w.parameter::text = 'water_temperature'::text AND (w.source_type::text = ANY (ARRAY['usgs'::character varying::text, 'owdp'::character varying::text]))
          GROUP BY w.site_id, w.watershed, w.station_id, w.source_type, w.obs_year
         HAVING count(
                CASE
                    WHEN w.obs_month >= 6 AND w.obs_month <= 8 THEN 1
                    ELSE NULL::integer
                END) >= 30
        )
 SELECT site_id,
    watershed,
    station_id,
    source_type,
    obs_year,
    summer_avg_temp,
    summer_max_temp,
    summer_readings,
    days_above_18c,
    days_above_20c,
        CASE
            WHEN summer_avg_temp < 12::numeric THEN 'cold_water_refuge'::text
            WHEN summer_avg_temp < 16::numeric THEN 'cool_water'::text
            WHEN summer_avg_temp < 20::numeric THEN 'warm_water'::text
            ELSE 'thermal_stress'::text
        END AS thermal_classification,
    round(avg(summer_avg_temp) OVER (PARTITION BY site_id, station_id), 1) AS multi_year_summer_avg,
    round(summer_avg_temp - lag(summer_avg_temp) OVER (PARTITION BY site_id, station_id ORDER BY obs_year), 1) AS yoy_temp_change
   FROM sst t;;

-- gold.fishing_conditions
DROP MATERIALIZED VIEW IF EXISTS gold.fishing_conditions CASCADE;
CREATE MATERIALIZED VIEW gold.fishing_conditions AS
 SELECT site_id,
    watershed,
    obs_year,
    obs_month,
    round(avg(
        CASE
            WHEN parameter::text = 'water_temperature'::text AND source_type::text = 'usgs'::text THEN value
            ELSE NULL::numeric
        END), 1) AS avg_water_temp_c,
    round(max(
        CASE
            WHEN parameter::text = 'water_temperature'::text AND source_type::text = 'usgs'::text THEN value
            ELSE NULL::numeric
        END), 1) AS max_water_temp_c,
    round(avg(
        CASE
            WHEN parameter::text = 'discharge'::text THEN value
            ELSE NULL::numeric
        END), 0) AS avg_discharge_cfs,
    round(avg(
        CASE
            WHEN parameter::text = 'dissolved_oxygen'::text THEN value
            ELSE NULL::numeric
        END), 1) AS avg_do_mg_l,
    sum(
        CASE
            WHEN parameter::text = 'sport_catch_steelhead'::text THEN value
            ELSE NULL::numeric
        END)::integer AS steelhead_harvest,
    sum(
        CASE
            WHEN parameter::text = 'sport_catch_chinook'::text THEN value
            ELSE NULL::numeric
        END)::integer AS chinook_harvest,
    sum(
        CASE
            WHEN parameter::text = 'sport_catch_coho'::text THEN value
            ELSE NULL::numeric
        END)::integer AS coho_harvest,
    sum(
        CASE
            WHEN parameter::text = 'trout_stocked'::text THEN value
            ELSE NULL::numeric
        END)::integer AS trout_stocked
   FROM silver.water_conditions w
  WHERE obs_year >= 2020
  GROUP BY site_id, watershed, obs_year, obs_month;;

-- gold.harvest_trends
DROP MATERIALIZED VIEW IF EXISTS gold.harvest_trends CASCADE;
CREATE MATERIALIZED VIEW gold.harvest_trends AS
 WITH yearly_harvest AS (
         SELECT t.site_id,
            s.watershed,
            t.station_id,
            replace(t.parameter::text, 'sport_catch_'::text, ''::text) AS species,
            EXTRACT(year FROM t."timestamp")::integer AS harvest_year,
            sum(t.value)::integer AS annual_harvest
           FROM time_series t
             JOIN sites s ON s.id = t.site_id
          WHERE t.source_type::text = 'sport_catch'::text
          GROUP BY t.site_id, s.watershed, t.station_id, t.parameter, (EXTRACT(year FROM t."timestamp")::integer)
        )
 SELECT site_id,
    watershed,
    station_id,
    species,
    harvest_year,
    annual_harvest,
    lag(annual_harvest) OVER (PARTITION BY site_id, station_id, species ORDER BY harvest_year) AS prev_year_harvest,
    annual_harvest - lag(annual_harvest) OVER (PARTITION BY site_id, station_id, species ORDER BY harvest_year) AS harvest_delta,
        CASE
            WHEN lag(annual_harvest) OVER (PARTITION BY site_id, station_id, species ORDER BY harvest_year) > 0 THEN round(((annual_harvest::double precision / lag(annual_harvest) OVER (PARTITION BY site_id, station_id, species ORDER BY harvest_year)::double precision - 1::double precision) * 100::double precision)::numeric, 1)
            ELSE NULL::numeric
        END AS harvest_pct_change
   FROM yearly_harvest y;;

-- gold.invasive_detections
DROP MATERIALIZED VIEW IF EXISTS gold.invasive_detections CASCADE;
CREATE MATERIALIZED VIEW gold.invasive_detections AS
 SELECT site_id,
    watershed,
    watershed_name,
    taxon_name,
    taxonomic_group,
    count(*) AS detection_count,
    min(observed_at)::date AS first_detected,
    max(observed_at)::date AS last_detected,
    count(DISTINCT obs_year) AS years_detected,
    count(
        CASE
            WHEN obs_year >= 2024 THEN 1
            ELSE NULL::integer
        END) AS recent_detections
   FROM silver.species_observations o
  WHERE taxon_name::text = ANY (ARRAY['Reynoutria japonica'::character varying, 'Fallopia japonica'::character varying, 'Phalaris arundinacea'::character varying, 'Myriophyllum spicatum'::character varying, 'Potamogeton crispus'::character varying, 'Cirsium arvense'::character varying, 'Cirsium vulgare'::character varying, 'Centaurea stoebe'::character varying, 'Cytisus scoparius'::character varying, 'Rubus armeniacus'::character varying, 'Hedera helix'::character varying, 'Lithobates catesbeianus'::character varying]::text[])
  GROUP BY site_id, watershed, watershed_name, taxon_name, taxonomic_group;;

-- gold.post_fire_recovery
DROP MATERIALIZED VIEW IF EXISTS gold.post_fire_recovery CASCADE;
CREATE MATERIALIZED VIEW gold.post_fire_recovery AS
 WITH fire_years AS (
         SELECT fp.site_id,
            fp.fire_name,
            fp.fire_year,
            fp.acres,
            fp.fire_year + gs.yr_delta AS obs_year,
            gs.yr_delta AS years_since_fire
           FROM fire_perimeters fp
             CROSS JOIN generate_series('-2'::integer, 6) gs(yr_delta)
          WHERE fp.fire_year >= 2015 AND fp.acres > 1000::double precision AND (fp.fire_year + gs.yr_delta) >= 2013 AND (fp.fire_year + gs.yr_delta) <= 2026
        )
 SELECT DISTINCT ON (fy.site_id, fy.fire_name, fy.obs_year) fy.site_id,
    s.watershed,
    fy.fire_name,
    fy.fire_year,
    fy.acres,
    fy.obs_year AS observation_year,
    fy.years_since_fire,
    ( SELECT count(DISTINCT o.taxon_name) AS count
           FROM observations o
          WHERE o.site_id = fy.site_id AND EXTRACT(year FROM o.observed_at) = fy.obs_year::numeric AND o.taxon_name IS NOT NULL) AS species_total_watershed,
    ( SELECT count(*) AS count
           FROM observations o
          WHERE o.site_id = fy.site_id AND EXTRACT(year FROM o.observed_at) = fy.obs_year::numeric AND o.taxon_name IS NOT NULL) AS total_obs_that_year
   FROM fire_years fy
     JOIN sites s ON s.id = fy.site_id
  ORDER BY fy.site_id, fy.fire_name, fy.obs_year;;

-- gold.restoration_outcomes
DROP MATERIALIZED VIEW IF EXISTS gold.restoration_outcomes CASCADE;
CREATE MATERIALIZED VIEW gold.restoration_outcomes AS
 SELECT site_id,
    watershed,
    intervention_category,
    intervention_year,
    count(*) AS intervention_count,
    ( SELECT count(DISTINCT o.taxon_name) AS count
           FROM silver.species_observations o
          WHERE o.site_id = i.site_id AND o.obs_year >= (i.intervention_year - 2) AND o.obs_year <= (i.intervention_year - 1) AND o.taxon_name IS NOT NULL) AS species_before,
    ( SELECT count(DISTINCT o.taxon_name) AS count
           FROM silver.species_observations o
          WHERE o.site_id = i.site_id AND o.obs_year >= (i.intervention_year + 1) AND o.obs_year <= (i.intervention_year + 2) AND o.taxon_name IS NOT NULL) AS species_after
   FROM silver.interventions_enriched i
  WHERE intervention_year IS NOT NULL AND intervention_year >= 2015 AND (intervention_category <> ALL (ARRAY['outreach'::text, 'salmon_planning'::text, 'salmon_monitoring'::text, 'other'::text]))
  GROUP BY site_id, watershed, intervention_category, intervention_year;;

-- gold.river_miles
DROP MATERIALIZED VIEW IF EXISTS gold.river_miles CASCADE;
CREATE MATERIALIZED VIEW gold.river_miles AS
 WITH ranked_segments AS (
         SELECT f.site_id,
            s.watershed,
            f.gnis_name AS river_name,
            f.reach_code,
            f.stream_order,
            f.length_km,
            (f.data_payload ->> 'hydroseq'::text)::double precision AS hydroseq,
            (f.data_payload ->> 'drainage_area_sqkm'::text)::double precision AS drainage_sqkm,
            (f.data_payload ->> 'fromnode'::text)::bigint AS fromnode,
            (f.data_payload ->> 'tonode'::text)::bigint AS tonode,
            f.flowline,
            row_number() OVER (PARTITION BY f.site_id, f.gnis_name, (f.data_payload ->> 'hydroseq'::text) ORDER BY f.id) AS rn
           FROM stream_flowlines f
             JOIN sites s ON s.id = f.site_id
          WHERE f.gnis_name IS NOT NULL AND f.gnis_name::text <> ''::text AND (f.data_payload ->> 'hydroseq'::text) IS NOT NULL
        ), deduped AS (
         SELECT ranked_segments.site_id,
            ranked_segments.watershed,
            ranked_segments.river_name,
            ranked_segments.reach_code,
            ranked_segments.stream_order,
            ranked_segments.length_km,
            ranked_segments.hydroseq,
            ranked_segments.drainage_sqkm,
            ranked_segments.fromnode,
            ranked_segments.tonode,
            ranked_segments.flowline,
            ranked_segments.rn
           FROM ranked_segments
          WHERE ranked_segments.rn = 1
        )
 SELECT site_id,
    watershed,
    river_name,
    reach_code,
    stream_order,
    length_km,
    hydroseq,
    drainage_sqkm,
    fromnode,
    tonode,
    flowline,
    sum(length_km) OVER (PARTITION BY site_id, river_name ORDER BY hydroseq DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS river_km_from_source,
    round((sum(length_km) OVER (PARTITION BY site_id, river_name ORDER BY hydroseq DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) * 0.621371::double precision)::numeric, 1) AS river_mile_from_source,
    round(((sum(length_km) OVER (PARTITION BY site_id, river_name ORDER BY hydroseq DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - length_km) * 0.621371::double precision)::numeric, 1) AS segment_start_mile,
    round((sum(length_km) OVER (PARTITION BY site_id, river_name ORDER BY hydroseq DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) * 0.621371::double precision)::numeric, 1) AS segment_end_mile,
    row_number() OVER (PARTITION BY site_id, river_name ORDER BY hydroseq DESC) AS segment_number,
    count(*) OVER (PARTITION BY site_id, river_name) AS total_segments
   FROM deduped;;

-- gold.seasonal_observation_patterns
DROP MATERIALIZED VIEW IF EXISTS gold.seasonal_observation_patterns CASCADE;
CREATE MATERIALIZED VIEW gold.seasonal_observation_patterns AS
 SELECT site_id,
    watershed,
    obs_month,
    taxonomic_group,
    count(*) AS observation_count,
    count(DISTINCT taxon_name) AS species_count,
    rank() OVER (PARTITION BY site_id, taxonomic_group ORDER BY (count(*)) DESC) AS month_rank,
        CASE
            WHEN rank() OVER (PARTITION BY site_id, taxonomic_group ORDER BY (count(*)) DESC) <= 3 THEN true
            ELSE false
        END AS is_peak_month,
        CASE
            WHEN obs_month = ANY (ARRAY[3, 4, 5]) THEN 'spring'::text
            WHEN obs_month = ANY (ARRAY[6, 7, 8]) THEN 'summer'::text
            WHEN obs_month = ANY (ARRAY[9, 10, 11]) THEN 'fall'::text
            ELSE 'winter'::text
        END AS season
   FROM silver.species_observations o
  WHERE taxon_name IS NOT NULL AND taxonomic_group IS NOT NULL
  GROUP BY site_id, watershed, obs_month, taxonomic_group;;

-- gold.site_ecological_summary
DROP MATERIALIZED VIEW IF EXISTS gold.site_ecological_summary CASCADE;
CREATE MATERIALIZED VIEW gold.site_ecological_summary AS
 SELECT site_id,
    watershed,
    watershed_name,
    obs_year,
    count(DISTINCT taxon_name) AS species_richness,
    count(DISTINCT
        CASE
            WHEN taxonomic_group::text = 'Plantae'::text THEN taxon_name
            ELSE NULL::character varying
        END) AS plant_species,
    count(DISTINCT
        CASE
            WHEN taxonomic_group::text = 'Aves'::text THEN taxon_name
            ELSE NULL::character varying
        END) AS bird_species,
    count(DISTINCT
        CASE
            WHEN taxonomic_group::text = 'Insecta'::text THEN taxon_name
            ELSE NULL::character varying
        END) AS insect_species,
    count(DISTINCT
        CASE
            WHEN taxonomic_group::text = 'Actinopterygii'::text THEN taxon_name
            ELSE NULL::character varying
        END) AS fish_species,
    count(DISTINCT
        CASE
            WHEN taxonomic_group::text = 'Amphibia'::text THEN taxon_name
            ELSE NULL::character varying
        END) AS amphibian_species,
    count(*) AS total_observations
   FROM silver.species_observations o
  WHERE obs_year >= 2019 AND taxon_name IS NOT NULL
  GROUP BY site_id, watershed, watershed_name, obs_year;;

-- gold.species_by_reach
DROP MATERIALIZED VIEW IF EXISTS gold.species_by_reach CASCADE;
CREATE MATERIALIZED VIEW gold.species_by_reach AS
 SELECT o.site_id,
    s.watershed,
    o.data_payload ->> 'stream'::text AS stream_name,
    o.taxon_name AS scientific_name,
    o.data_payload ->> 'species'::text AS common_name,
    o.data_payload ->> 'run'::text AS run_type,
    o.data_payload ->> 'use_type'::text AS use_type,
    o.data_payload ->> 'origin'::text AS origin,
    o.data_payload ->> 'life_history'::text AS life_history,
    o.data_payload ->> 'basis'::text AS data_basis,
    ( SELECT count(*) AS count
           FROM observations obs
          WHERE obs.site_id = o.site_id AND obs.source_type::text = 'inaturalist'::text AND obs.taxon_name::text = o.taxon_name::text) AS inat_observation_count,
    ( SELECT max(obs.observed_at)::date AS max
           FROM observations obs
          WHERE obs.site_id = o.site_id AND obs.source_type::text = 'inaturalist'::text AND obs.taxon_name::text = o.taxon_name::text) AS last_inat_observation
   FROM observations o
     JOIN sites s ON s.id = o.site_id
  WHERE o.source_type::text = 'fish_habitat'::text
UNION ALL
 SELECT w.site_id,
    s.watershed,
    w.stream_name,
    w.species AS scientific_name,
    w.species AS common_name,
    w.species_run AS run_type,
    w.use_type,
    NULL::text AS origin,
    w.life_history,
    w.distribution_type AS data_basis,
    0 AS inat_observation_count,
    NULL::date AS last_inat_observation
   FROM wa_salmonscape w
     JOIN sites s ON s.id = w.site_id;;

-- gold.species_trends
DROP MATERIALIZED VIEW IF EXISTS gold.species_trends CASCADE;
CREATE MATERIALIZED VIEW gold.species_trends AS
 WITH yearly AS (
         SELECT species_observations.site_id,
            species_observations.watershed,
            species_observations.obs_year,
            count(DISTINCT species_observations.taxon_name) AS species_count,
            count(*) AS obs_count
           FROM silver.species_observations
          WHERE species_observations.taxon_name IS NOT NULL AND species_observations.obs_year >= 2019
          GROUP BY species_observations.site_id, species_observations.watershed, species_observations.obs_year
        )
 SELECT site_id,
    watershed,
    obs_year,
    species_count,
    obs_count,
    lag(species_count) OVER (PARTITION BY site_id ORDER BY obs_year) AS prev_year_species,
    species_count - lag(species_count) OVER (PARTITION BY site_id ORDER BY obs_year) AS species_delta
   FROM yearly y;;

-- gold.stocking_schedule
DROP MATERIALIZED VIEW IF EXISTS gold.stocking_schedule CASCADE;
CREATE MATERIALIZED VIEW gold.stocking_schedule AS
 SELECT t.site_id,
    s.watershed,
    replace(replace(t.station_id::text, 'stocking_'::text, ''::text), '_'::text, ' '::text) AS waterbody,
    t."timestamp"::date AS stocking_date,
    t.value::integer AS total_fish,
    t.source_type
   FROM time_series t
     JOIN sites s ON s.id = t.site_id
  WHERE t.source_type::text = 'stocking'::text AND t.value > 0::double precision
  ORDER BY t."timestamp" DESC;;

-- gold.stewardship_opportunities
DROP MATERIALIZED VIEW IF EXISTS gold.stewardship_opportunities CASCADE;
CREATE MATERIALIZED VIEW gold.stewardship_opportunities AS
 SELECT site_id,
    watershed,
    watershed_name,
    intervention_category,
    raw_type,
    count(*) AS project_count,
    max(intervention_year) AS most_recent_year,
    string_agg(DISTINCT "left"(description, 200), ' | '::text ORDER BY ("left"(description, 200))) AS project_summaries
   FROM silver.interventions_enriched i
  WHERE intervention_category <> ALL (ARRAY['outreach'::text, 'other'::text])
  GROUP BY site_id, watershed, watershed_name, intervention_category, raw_type;;

-- gold.water_quality_monthly
DROP MATERIALIZED VIEW IF EXISTS gold.water_quality_monthly CASCADE;
CREATE MATERIALIZED VIEW gold.water_quality_monthly AS
 SELECT site_id,
    watershed,
    station_id,
    parameter,
    unit,
    parameter_category,
    obs_year,
    obs_month,
    round(avg(value), 2) AS avg_value,
    round(min(value), 2) AS min_value,
    round(max(value), 2) AS max_value,
    count(*) AS reading_count,
    count(
        CASE
            WHEN parameter::text = 'water_temperature'::text AND value > 18::numeric THEN 1
            ELSE NULL::integer
        END) AS temp_above_18c,
    count(
        CASE
            WHEN parameter::text = 'dissolved_oxygen'::text AND value < 6::numeric THEN 1
            ELSE NULL::integer
        END) AS do_below_6
   FROM silver.water_conditions w
  WHERE (parameter_category = ANY (ARRAY['temperature'::text, 'hydrology'::text, 'oxygen'::text, 'chemistry'::text, 'nutrients'::text])) AND obs_year >= 2020
  GROUP BY site_id, watershed, station_id, parameter, unit, parameter_category, obs_year, obs_month;;

-- gold.watershed_scorecard
DROP MATERIALIZED VIEW IF EXISTS gold.watershed_scorecard CASCADE;
CREATE MATERIALIZED VIEW gold.watershed_scorecard AS
 SELECT watershed,
    name AS watershed_name,
    ( SELECT count(*) AS count
           FROM observations o
          WHERE o.site_id = s.id) AS total_observations,
    ( SELECT count(*) AS count
           FROM time_series t
          WHERE t.site_id = s.id) AS total_time_series,
    ( SELECT count(*) AS count
           FROM interventions i
          WHERE i.site_id = s.id) AS total_interventions,
    ( SELECT count(DISTINCT o.taxon_name) AS count
           FROM observations o
          WHERE o.site_id = s.id AND o.taxon_name IS NOT NULL) AS total_species,
    ( SELECT count(DISTINCT o.taxon_name) AS count
           FROM observations o
          WHERE o.site_id = s.id AND o.iconic_taxon::text = 'Actinopterygii'::text) AS fish_species,
    ( SELECT count(DISTINCT o.taxon_name) AS count
           FROM observations o
          WHERE o.site_id = s.id AND o.iconic_taxon::text = 'Amphibia'::text) AS amphibian_species,
    ( SELECT count(DISTINCT t.station_id) AS count
           FROM time_series t
          WHERE t.site_id = s.id AND t.source_type::text = 'usgs'::text) AS usgs_stations,
    ( SELECT count(DISTINCT t.station_id) AS count
           FROM time_series t
          WHERE t.site_id = s.id AND t.source_type::text = 'snotel'::text) AS snotel_stations,
    ( SELECT count(*) AS count
           FROM stream_flowlines f
          WHERE f.site_id = s.id) AS stream_reaches,
    ( SELECT count(*) AS count
           FROM wetlands w
          WHERE w.site_id = s.id) AS wetland_polygons,
    ( SELECT count(*) AS count
           FROM fire_perimeters fp
          WHERE fp.site_id = s.id) AS fire_events,
    ( SELECT count(*) AS count
           FROM impaired_waters iw
          WHERE iw.site_id = s.id) AS impaired_segments,
    ( SELECT count(*) AS count
           FROM watershed_boundaries wb
          WHERE wb.site_id = s.id) AS huc12_count
   FROM sites s;;

-- gold.indicator_species_status
DROP MATERIALIZED VIEW IF EXISTS gold.indicator_species_status CASCADE;
CREATE MATERIALIZED VIEW gold.indicator_species_status AS
 WITH ic AS (
         SELECT unnest(ARRAY['Oncorhynchus tshawytscha'::text, 'Oncorhynchus kisutch'::text, 'Oncorhynchus mykiss'::text, 'Oncorhynchus clarkii'::text, 'Salvelinus confluentus'::text, 'Ascaphus truei'::text, 'Rana cascadae'::text, 'Pseudacris regilla'::text, 'Taricha granulosa'::text, 'Lithobates catesbeianus'::text, 'Cytisus scoparius'::text, 'Phalaris arundinacea'::text]) AS taxon_name,
            unnest(ARRAY['Chinook salmon'::text, 'Coho salmon'::text, 'Steelhead'::text, 'Cutthroat trout'::text, 'Bull trout'::text, 'Tailed frog'::text, 'Cascades frog'::text, 'Pacific treefrog'::text, 'Rough-skinned newt'::text, 'Bullfrog (invasive)'::text, 'Scotch broom (invasive)'::text, 'Reed canarygrass (invasive)'::text]) AS common_name,
            unnest(ARRAY['positive'::text, 'positive'::text, 'positive'::text, 'positive'::text, 'positive'::text, 'positive'::text, 'positive'::text, 'positive'::text, 'positive'::text, 'negative'::text, 'negative'::text, 'negative'::text]) AS indicator_direction
        )
 SELECT s.id AS site_id,
    s.watershed,
    ic.taxon_name,
    ic.common_name,
    ic.indicator_direction,
        CASE
            WHEN count(o.id) > 0 THEN 'detected'::text
            ELSE 'not_detected'::text
        END AS status,
    count(o.id) AS total_detections,
    max(o.observed_at)::date AS last_detected
   FROM sites s
     CROSS JOIN ic
     LEFT JOIN observations o ON o.site_id = s.id AND o.taxon_name::text = ic.taxon_name
  GROUP BY s.id, s.watershed, ic.taxon_name, ic.common_name, ic.indicator_direction;;

-- gold.river_health_score
DROP MATERIALIZED VIEW IF EXISTS gold.river_health_score CASCADE;
CREATE MATERIALIZED VIEW gold.river_health_score AS
 SELECT s.id AS site_id,
    s.watershed,
    s.name AS watershed_name,
    wc.obs_year,
    wc.obs_month,
    count(DISTINCT so.taxon_name) AS monthly_species,
    round(avg(
        CASE
            WHEN wc.parameter::text = 'water_temperature'::text AND wc.source_type::text = 'usgs'::text THEN wc.value
            ELSE NULL::numeric
        END), 1) AS avg_water_temp,
    round(avg(
        CASE
            WHEN wc.parameter::text = 'dissolved_oxygen'::text THEN wc.value
            ELSE NULL::numeric
        END), 1) AS avg_do,
    30 +
        CASE
            WHEN avg(
            CASE
                WHEN wc.parameter::text = 'water_temperature'::text AND wc.source_type::text = 'usgs'::text THEN wc.value
                ELSE NULL::numeric
            END) < 16::numeric THEN 20
            ELSE 10
        END +
        CASE
            WHEN avg(
            CASE
                WHEN wc.parameter::text = 'dissolved_oxygen'::text THEN wc.value
                ELSE NULL::numeric
            END) > 8::numeric THEN 20
            ELSE 10
        END AS health_score
   FROM sites s
     JOIN silver.water_conditions wc ON wc.site_id = s.id
     LEFT JOIN silver.species_observations so ON so.site_id = s.id AND so.obs_year = wc.obs_year AND so.obs_month = wc.obs_month AND so.taxon_name IS NOT NULL
  WHERE wc.obs_year >= 2024 AND (wc.parameter::text = ANY (ARRAY['water_temperature'::character varying::text, 'dissolved_oxygen'::character varying::text, 'discharge'::character varying::text]))
  GROUP BY s.id, s.watershed, s.name, wc.obs_year, wc.obs_month;;

-- gold.whats_alive_now
DROP MATERIALIZED VIEW IF EXISTS gold.whats_alive_now CASCADE;
CREATE MATERIALIZED VIEW gold.whats_alive_now AS
 SELECT site_id,
    watershed,
    watershed_name,
    taxonomic_group,
    count(DISTINCT taxon_name) AS species_active,
    count(*) AS recent_observations
   FROM silver.species_observations o
  WHERE obs_year = EXTRACT(year FROM now())::integer AND obs_month = EXTRACT(month FROM now())::integer AND taxon_name IS NOT NULL AND taxonomic_group IS NOT NULL
  GROUP BY site_id, watershed, watershed_name, taxonomic_group;;

-- gold.swim_safety
DROP MATERIALIZED VIEW IF EXISTS gold.swim_safety CASCADE;
CREATE MATERIALIZED VIEW gold.swim_safety AS
 SELECT site_id,
    watershed,
    station_id,
    obs_year,
    obs_month,
    round(avg(
        CASE
            WHEN parameter::text = 'water_temperature'::text THEN value
            ELSE NULL::numeric
        END), 1) AS avg_temp_c,
    round(avg(
        CASE
            WHEN parameter::text = 'discharge'::text THEN value
            ELSE NULL::numeric
        END), 0) AS avg_flow_cfs,
        CASE
            WHEN avg(
            CASE
                WHEN parameter::text = 'water_temperature'::text THEN value
                ELSE NULL::numeric
            END) < 10::numeric THEN 'very_cold'::text
            WHEN avg(
            CASE
                WHEN parameter::text = 'water_temperature'::text THEN value
                ELSE NULL::numeric
            END) < 15::numeric THEN 'cold'::text
            WHEN avg(
            CASE
                WHEN parameter::text = 'water_temperature'::text THEN value
                ELSE NULL::numeric
            END) < 20::numeric THEN 'refreshing'::text
            ELSE 'comfortable'::text
        END AS temp_comfort,
        CASE
            WHEN avg(
            CASE
                WHEN parameter::text = 'discharge'::text THEN value
                ELSE NULL::numeric
            END) > 5000::numeric THEN 'red'::text
            WHEN avg(
            CASE
                WHEN parameter::text = 'discharge'::text THEN value
                ELSE NULL::numeric
            END) > 2000::numeric THEN 'yellow'::text
            ELSE 'green'::text
        END AS safety_rating
   FROM silver.water_conditions w
  WHERE source_type::text = 'usgs'::text AND (parameter::text = ANY (ARRAY['water_temperature'::character varying::text, 'discharge'::character varying::text])) AND obs_year >= 2024
  GROUP BY site_id, watershed, station_id, obs_year, obs_month;;

-- gold.river_story_timeline
DROP MATERIALIZED VIEW IF EXISTS gold.river_story_timeline CASCADE;
CREATE MATERIALIZED VIEW gold.river_story_timeline AS
 SELECT fp.site_id,
    s.watershed,
    fp.fire_year AS event_year,
    'fire'::text AS event_type,
    fp.fire_name AS event_name,
    ('Wildfire burned '::text || round(fp.acres)) || ' acres'::text AS description,
    fp.acres AS magnitude
   FROM fire_perimeters fp
     JOIN sites s ON s.id = fp.site_id
  WHERE fp.fire_year IS NOT NULL AND fp.acres > 100::double precision
UNION ALL
 SELECT i.site_id,
    i.watershed,
    i.intervention_year AS event_year,
    'restoration'::text AS event_type,
    i.intervention_category AS event_name,
    ((count(*) || ' '::text) || i.intervention_category) || ' projects'::text AS description,
    count(*)::double precision AS magnitude
   FROM silver.interventions_enriched i
  WHERE i.intervention_year IS NOT NULL
  GROUP BY i.site_id, i.watershed, i.intervention_year, i.intervention_category
UNION ALL
 SELECT iw.site_id,
    s.watershed,
    iw.listing_year AS event_year,
    'regulatory'::text AS event_type,
    iw.water_name AS event_name,
    'Listed as impaired: '::text || COALESCE(iw.parameter, iw.category)::text AS description,
    1.0 AS magnitude
   FROM impaired_waters iw
     JOIN sites s ON s.id = iw.site_id
  WHERE iw.listing_year IS NOT NULL
  ORDER BY 3 DESC;;

-- gold.species_gallery
DROP MATERIALIZED VIEW IF EXISTS gold.species_gallery CASCADE;
CREATE MATERIALIZED VIEW gold.species_gallery AS
 SELECT DISTINCT ON (s.watershed, o.taxon_name) o.site_id,
    s.watershed,
    o.taxon_name,
    o.iconic_taxon AS taxonomic_group,
    o.data_payload ->> 'common_name'::text AS common_name,
    o.data_payload ->> 'photo_url'::text AS photo_url,
    o.data_payload ->> 'photo_license'::text AS photo_license,
    o.data_payload ->> 'user'::text AS observer,
    o.data_payload ->> 'conservation_status'::text AS conservation_status,
    o.quality_grade,
    o.observed_at::date AS photo_date
   FROM observations o
     JOIN sites s ON s.id = o.site_id
  WHERE o.source_type::text = 'inaturalist'::text AND o.taxon_name IS NOT NULL AND (o.data_payload ->> 'photo_url'::text) IS NOT NULL AND (o.data_payload ->> 'photo_license'::text) IS NOT NULL
  ORDER BY s.watershed, o.taxon_name, (
        CASE
            WHEN o.quality_grade::text = 'research'::text THEN 0
            ELSE 1
        END), o.observed_at DESC;;

-- gold.hatch_chart
DROP MATERIALIZED VIEW IF EXISTS gold.hatch_chart CASCADE;
CREATE MATERIALIZED VIEW gold.hatch_chart AS
 SELECT site_id,
    watershed,
    taxon_name,
    common_name,
    obs_month,
    count(*) AS observation_count,
    count(DISTINCT obs_year) AS years_observed,
    rank() OVER (PARTITION BY site_id, taxon_name ORDER BY (count(*)) DESC) AS month_rank,
        CASE
            WHEN rank() OVER (PARTITION BY site_id, taxon_name ORDER BY (count(*)) DESC) <= 2 THEN 'peak'::text
            ELSE 'present'::text
        END AS activity_level,
    ( SELECT g.photo_url
           FROM gold.species_gallery g
          WHERE g.taxon_name::text = o.taxon_name::text AND g.watershed::text = o.watershed::text
         LIMIT 1) AS photo_url
   FROM silver.species_observations o
  WHERE taxonomic_group::text = 'Insecta'::text AND taxon_name IS NOT NULL AND (taxon_rank::text = ANY (ARRAY['species'::character varying, 'genus'::character varying, 'subfamily'::character varying]::text[]))
  GROUP BY site_id, watershed, taxon_name, common_name, obs_month
 HAVING count(*) >= 3;;

-- gold.species_by_river_mile
DROP MATERIALIZED VIEW IF EXISTS gold.species_by_river_mile CASCADE;
CREATE MATERIALIZED VIEW gold.species_by_river_mile AS
 WITH named_rivers AS (
         SELECT DISTINCT river_miles.river_name
           FROM gold.river_miles
          WHERE river_miles.river_name IS NOT NULL AND river_miles.length_km > 0.5::double precision
        ), river_obs AS (
         SELECT rm.watershed,
            rm.river_name,
            (floor(rm.segment_start_mile / 5::numeric) * 5::numeric)::integer AS mile_section_start,
            (floor(rm.segment_start_mile / 5::numeric) * 5::numeric + 5::numeric)::integer AS mile_section_end,
            o.taxon_name,
            o.iconic_taxon,
            o.data_payload ->> 'common_name'::text AS common_name,
            o.observed_at,
            o.quality_grade
           FROM gold.river_miles rm
             JOIN named_rivers nr ON nr.river_name::text = rm.river_name::text
             JOIN observations o ON st_dwithin(o.location, rm.flowline, 0.005::double precision)
          WHERE o.taxon_name IS NOT NULL AND o.source_type::text = 'inaturalist'::text
        )
 SELECT watershed,
    river_name,
    mile_section_start,
    mile_section_end,
    taxon_name,
    common_name,
    iconic_taxon AS taxonomic_group,
    count(*) AS observation_count,
    count(
        CASE
            WHEN quality_grade::text = 'research'::text THEN 1
            ELSE NULL::integer
        END) AS research_grade_count,
    min(observed_at)::date AS first_seen,
    max(observed_at)::date AS last_seen,
    ( SELECT g.photo_url
           FROM gold.species_gallery g
          WHERE g.taxon_name::text = ro.taxon_name::text AND g.watershed::text = ro.watershed::text
         LIMIT 1) AS photo_url
   FROM river_obs ro
  GROUP BY watershed, river_name, mile_section_start, mile_section_end, taxon_name, common_name, iconic_taxon
 HAVING count(*) >= 2;;

-- gold.geologic_age_at_location
DROP MATERIALIZED VIEW IF EXISTS gold.geologic_age_at_location CASCADE;
CREATE MATERIALIZED VIEW gold.geologic_age_at_location AS
 SELECT id,
    unit_name,
    formation,
    rock_type,
    lithology,
    age_min_ma,
    age_max_ma,
    age_midpoint_ma,
    period,
    description,
    geometry
   FROM silver.geologic_context gc;;

-- gold.fossils_nearby
DROP MATERIALIZED VIEW IF EXISTS gold.fossils_nearby CASCADE;
CREATE MATERIALIZED VIEW gold.fossils_nearby AS
 SELECT id,
    source_id,
    taxon_name,
    common_name,
    phylum,
    class_name,
    order_name,
    family,
    age_min_ma,
    age_max_ma,
    age_midpoint_ma,
    period,
    formation,
    latitude,
    longitude,
    location,
    collector,
    reference,
    museum,
    image_url,
    image_license,
    morphosource_url
   FROM silver.fossil_records;;

-- gold.legal_collecting_sites
DROP MATERIALIZED VIEW IF EXISTS gold.legal_collecting_sites CASCADE;
CREATE MATERIALIZED VIEW gold.legal_collecting_sites AS
 SELECT id,
    agency,
    designation,
    admin_unit,
    collecting_status,
    collecting_rules,
    status_color,
    geometry
   FROM silver.land_access la
  WHERE collecting_status::text = ANY (ARRAY['permitted'::character varying, 'restricted'::character varying]::text[]);;

-- gold.deep_time_story
DROP MATERIALIZED VIEW IF EXISTS gold.deep_time_story CASCADE;
CREATE MATERIALIZED VIEW gold.deep_time_story AS
 SELECT id AS geologic_unit_id,
    unit_name,
    formation,
    rock_type,
    lithology,
    period,
    age_min_ma,
    age_max_ma,
    description
   FROM silver.geologic_context gc
  ORDER BY age_max_ma DESC NULLS LAST;;

-- gold.formation_species_history
DROP MATERIALIZED VIEW IF EXISTS gold.formation_species_history CASCADE;
CREATE MATERIALIZED VIEW gold.formation_species_history AS
 SELECT gc.formation,
    gc.period,
    gc.rock_type,
    gc.age_min_ma,
    gc.age_max_ma,
    fr.taxon_name,
    fr.phylum,
    fr.class_name,
    fr.order_name,
    fr.family,
    fr.age_midpoint_ma,
    fr.period AS fossil_period,
    count(*) AS occurrence_count
   FROM silver.geologic_context gc
     JOIN silver.fossil_records fr ON fr.period::text = gc.period::text
  WHERE gc.formation IS NOT NULL AND gc.formation::text <> ''::text
  GROUP BY gc.formation, gc.period, gc.rock_type, gc.age_min_ma, gc.age_max_ma, fr.taxon_name, fr.phylum, fr.class_name, fr.order_name, fr.family, fr.age_midpoint_ma, fr.period
  ORDER BY gc.age_max_ma DESC NULLS LAST, (count(*)) DESC;;

-- gold.geology_watershed_link
DROP MATERIALIZED VIEW IF EXISTS gold.geology_watershed_link CASCADE;
CREATE MATERIALIZED VIEW gold.geology_watershed_link AS
 SELECT s.watershed,
    gc.unit_name,
    gc.formation,
    gc.rock_type,
    gc.lithology,
    gc.period,
    gc.age_min_ma,
    gc.age_max_ma,
    gc.description,
    count(DISTINCT gc.id) AS unit_count
   FROM silver.geologic_context gc
     JOIN sites s ON gc.geometry && st_makeenvelope((s.bbox ->> 'west'::text)::double precision, (s.bbox ->> 'south'::text)::double precision, (s.bbox ->> 'east'::text)::double precision, (s.bbox ->> 'north'::text)::double precision, 4326)
  GROUP BY s.watershed, gc.unit_name, gc.formation, gc.rock_type, gc.lithology, gc.period, gc.age_min_ma, gc.age_max_ma, gc.description
  ORDER BY s.watershed, gc.age_max_ma DESC NULLS LAST;;

-- gold.mineral_sites_nearby
DROP MATERIALIZED VIEW IF EXISTS gold.mineral_sites_nearby CASCADE;
CREATE MATERIALIZED VIEW gold.mineral_sites_nearby AS
 SELECT id,
    source_id,
    site_name,
    commodity,
    dev_status,
    latitude,
    longitude,
    location,
    image_url,
    image_license
   FROM silver.mineral_sites;;

-- gold.hatch_fly_recommendations
DROP MATERIALIZED VIEW IF EXISTS gold.hatch_fly_recommendations CASCADE;
CREATE MATERIALIZED VIEW gold.hatch_fly_recommendations AS
 SELECT s.watershed,
    o.taxon_name AS insect_taxon,
    o.data_payload ->> 'common_name'::text AS insect_common_name,
    EXTRACT(month FROM o.observed_at)::integer AS obs_month,
    count(*) AS observation_count,
    max(o.data_payload ->> 'photo_url'::text) AS insect_photo_url,
    fp.fly_pattern_name,
    fp.fly_size,
    fp.fly_type,
    fp.fly_image_url,
    fp.life_stage,
    fp.time_of_day,
    fp.water_type,
    fp.notes AS fly_notes,
    fp.insect_common_name AS pattern_insect_name,
    fp.oregon_rivers
   FROM observations o
     JOIN sites s ON o.site_id = s.id
     CROSS JOIN silver.insect_fly_patterns fp
  WHERE o.iconic_taxon::text = 'Insecta'::text AND fp.season_start::numeric <= EXTRACT(month FROM o.observed_at) AND fp.season_end::numeric >= EXTRACT(month FROM o.observed_at) AND (fp.insect_genus IS NOT NULL AND o.taxon_name::text ~~* (fp.insect_genus::text || '%'::text) OR fp.insect_family IS NOT NULL AND o.taxon_name::text ~~* (fp.insect_family::text || '%'::text) OR fp.insect_order IS NOT NULL AND fp.insect_genus IS NULL AND fp.insect_family IS NULL AND o.taxon_name::text ~~* (fp.insect_order::text || '%'::text) OR fp.insect_common_name IS NOT NULL AND (o.data_payload ->> 'common_name'::text) ~~* (('%'::text || fp.insect_common_name::text) || '%'::text))
  GROUP BY s.watershed, o.taxon_name, (o.data_payload ->> 'common_name'::text), (EXTRACT(month FROM o.observed_at)), fp.fly_pattern_name, fp.fly_size, fp.fly_type, fp.fly_image_url, fp.life_stage, fp.time_of_day, fp.water_type, fp.notes, fp.insect_common_name, fp.oregon_rivers
  ORDER BY s.watershed, (EXTRACT(month FROM o.observed_at)::integer), (count(*)) DESC;;

