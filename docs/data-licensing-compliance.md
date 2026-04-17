# Data Licensing & Copyright Compliance

Review of terms of use, licensing, and attribution requirements for all 28 data sources ingested into the RiverSignal/RiverPath/DeepTrail platform.

## Summary Table

| # | Source | License | Commercial OK? | Attribution Required? | Image Rights | Key Restriction |
|---|--------|---------|---------------|----------------------|--------------|-----------------|
| 1 | **iNaturalist** | CC BY-NC (default) | **No** (NC = non-commercial) | Yes — credit observer + iNaturalist | Per-photo license (CC BY-NC default, varies) | Cannot use for commercial AI training. Photos are individually licensed by each observer. |
| 2 | **USGS NWIS** | Public domain | Yes | Acknowledge USGS | N/A | Don't claim as your own or imply USGS endorsement |
| 3 | **Water Quality Portal** | Public domain | Yes | Acknowledge WQP/USGS/EPA | N/A | Same as USGS |
| 4 | **SNOTEL (USDA)** | Public domain | Yes | Acknowledge USDA NRCS | N/A | Federal data, freely usable |
| 5 | **BioData (USGS)** | Public domain | Yes | Acknowledge USGS | N/A | Federal data |
| 6 | **WQP Bugs** | Public domain | Yes | Acknowledge WQP | N/A | Aggregated federal/state data |
| 7 | **StreamNet** | Public domain | Yes | Acknowledge StreamNet/PSMFC | N/A | Funded by BPA, data is public |
| 8 | **MTBS** | Public domain | Yes | Acknowledge USGS/USFS | N/A | Federal data |
| 9 | **NHDPlus HR** | Public domain | Yes | Acknowledge USGS | N/A | Federal data |
| 10 | **OWRI (Oregon)** | Public records | Yes | Acknowledge OWRI/OWEB | N/A | Oregon state public records |
| 11 | **NOAA Restoration** | Public domain | Yes | Acknowledge NOAA | N/A | Federal data |
| 12 | **PCSRF** | Public domain | Yes | Acknowledge NOAA | N/A | Federal data |
| 13 | **Fish Passage** | Public domain/state | Yes | Acknowledge ODFW | N/A | Oregon state data |
| 14 | **ODFW Fishing** | Public records | Yes | Acknowledge ODFW | N/A | Oregon public records, may have agency copyright |
| 15 | **PRISM** | Academic use free | **Check** | Cite PRISM Climate Group, Oregon State University | N/A | Free for non-profit/research; commercial use may require license from OSU |
| 16 | **EPA ATTAINS** | Public domain | Yes | Acknowledge EPA | N/A | Federal data |
| 17 | **NWI (Wetlands)** | Public domain | Yes | Acknowledge USFWS | N/A | Federal data |
| 18 | **USGS WBD** | Public domain | Yes | Acknowledge USGS | N/A | Federal data |
| 19 | **Macrostrat** | CC BY 4.0 | Yes | Cite Peters et al. 2018 + original sources | N/A | Must attribute, cite paper in publications |
| 20 | **PBDB** | CC BY 4.0 | Yes | Cite PBDB + original references + contributors | N/A | Full attribution required including original data contributors |
| 21 | **iDigBio** | Varies per provider | **Check per record** | Cite per GBIF guidelines | Varies per museum | Each museum sets its own license; iDigBio encourages open access |
| 22 | **GBIF** | CC0, CC BY, or CC BY-NC per dataset | **Varies** | Cite download DOI + dataset DOIs | Per-record license from publisher | Must comply with each publisher's chosen license |
| 23 | **BLM SMA** | Public domain | Yes | Acknowledge BLM | N/A | Federal data |
| 24 | **DOGAMI** | State public records | Yes | Acknowledge DOGAMI | N/A | Oregon state data |
| 25 | **MRDS** | Public domain | Yes | Acknowledge USGS | N/A | Federal data |
| 26 | **USFS Recreation** | Public domain | Yes | Acknowledge USFS | N/A | Federal data |
| 27 | **OSMB Boating** | State public records | Yes | Acknowledge Oregon State Marine Board | N/A | Oregon state data |
| 28 | **NWS Weather** | Public domain | Yes | Don't imply NWS endorsement | N/A | Can't use NWS logo without permission |

### Live APIs

| Source | License | Notes |
|--------|---------|-------|
| **NWS Forecast API** | Public domain | NOAA encourages commercial use. Don't claim as own or imply endorsement. |
| **USGS Instantaneous Values** | Public domain | Same as USGS above. |

### Curated Data

| Source | License | Notes |
|--------|---------|-------|
| **Curated Hatch Chart** | Our creation | Based on published fly fishing literature (fair use for factual data). Not copyrightable — hatch timing is factual. |
| **Fly Tying Videos** | Links only | We link to YouTube searches, not embed. No copyright issue — URLs are facts. |
| **Fly Shops & Guides** | Our creation | Publicly available business information. |
| **Fossil Common Names** | Our creation | Factual translations of Latin taxonomy. |

### Cached Images

| Image Source | License | Count | Compliance Action |
|-------------|---------|-------|-------------------|
| **iNaturalist photos** | CC BY-NC (mostly) | 21,368 | Must display observer attribution. Cannot use commercially. |
| **GBIF specimen photos** | Varies per museum | 890 | Check license per image. Most are CC BY or CC BY-NC. |
| **Wikipedia/Wikimedia** | CC BY-SA or Public Domain | ~81 | Must attribute author + link to license. SA = share-alike. |

---

## Risk Assessment

### HIGH RISK — Action Required

**1. iNaturalist (CC BY-NC)**
- **Issue:** Default license is CC BY-NC (non-commercial). If RiverPath charges subscriptions or shows ads, this may violate the NC clause.
- **Photos:** Each photo has its own license set by the observer. Some are CC0, some CC BY, most CC BY-NC, some All Rights Reserved.
- **AI Training:** iNaturalist explicitly prohibits using data for commercial AI training.
- **Action Required:**
  - Display photographer attribution on every species photo (observer name + license)
  - Filter species gallery to only show photos with compatible licenses for your use case
  - If commercial: only display CC0, CC BY, or CC BY licensed photos (exclude CC BY-NC)
  - Add "Photo © [observer] via iNaturalist" credit line
  - Do NOT use observation data to train commercial AI models

**2. PRISM Climate Data**
- **Issue:** PRISM data from Oregon State University is free for non-profit/research use. Commercial use may require a license agreement.
- **Action Required:**
  - Contact PRISM Climate Group (prism.oregonstate.edu) to clarify commercial use terms
  - If commercial license needed, budget for it or replace with NWS/NOAA data (public domain)

**3. GBIF / iDigBio (mixed licenses)**
- **Issue:** Each occurrence record may have a different license from its publishing institution. Some are CC0, some CC BY, some CC BY-NC.
- **Action Required:**
  - Store and display the license per record
  - Filter commercial use to CC0 and CC BY records only
  - Cite the GBIF download DOI
  - Include data publisher attribution

### MEDIUM RISK — Attribution Needed

**4. Macrostrat / PBDB (CC BY 4.0)**
- Both require clear attribution. PBDB requires citing original references.
- **Action Required:**
  - Add "Geologic data from Macrostrat (Peters et al., 2018)" to geology pages
  - Add "Fossil data from the Paleobiology Database" to fossil pages
  - Include original reference links on fossil detail cards (already done — PBDB/GBIF links)

**5. iNaturalist observation data**
- Observation metadata (taxon, location, date) may be factual and not copyrightable, but iNaturalist ToS still apply.
- **Action Required:**
  - Display "Species data from iNaturalist" attribution
  - Comply with API rate limits (100 req/min)
  - Don't present the data as your own

### LOW RISK — Standard Attribution

**6. All federal sources (USGS, EPA, NOAA, BLM, USFS, NWS, NWI, MTBS)**
- All public domain. Free for any use.
- **Action Required:**
  - Acknowledge each agency as a data source
  - Don't imply government endorsement
  - Already handled by our /status page listing all sources

**7. Oregon state sources (ODFW, OSMB, DOGAMI, OWRI)**
- Public records. Generally free for reuse.
- **Action Required:**
  - Acknowledge each agency
  - Oregon state copyright policy allows agencies to assert copyright in some cases — monitor for policy changes

---

## Recommended Compliance Actions

### Immediate (Before Public Launch)

1. **Add attribution footer/page** — Create a `/attribution` or `/about/data` page listing every data source with links and credit lines. Link to it from every product footer.

2. **Photo attribution overlay** — On every iNaturalist species photo, show "© [observer] / iNaturalist" in small text. Already have `observer` field in species gallery data.

3. **License filtering** — Add a `photo_license` filter to the species API. For commercial use, exclude CC BY-NC photos. For non-commercial use (free app), all CC licenses are fine.

4. **GBIF citation** — Add GBIF download DOI to the fossils attribution section. Request a formal download DOI from GBIF for our query.

5. **Clarify PRISM terms** — Email PRISM Climate Group about commercial use. If restricted, we already have NWS (public domain) as a weather alternative and USGS for water data.

### Before Monetization

6. **iNaturalist commercial review** — If charging for subscriptions or showing ads:
   - Review which features use iNaturalist data directly vs. our own aggregations
   - Consider whether the app qualifies as "educational/conservation" use (NC licenses often have carve-outs)
   - Contact iNaturalist about a commercial data agreement if needed
   - Alternative: use only CC0/CC BY licensed observations (subset of data)

7. **Image license audit** — Run a query to categorize all cached images by license type. Ensure only properly licensed images are shown in commercial contexts.

### Ongoing

8. **License field in API responses** — Already returning `photo_license` for species and `image_license` for fossils/minerals. Ensure UI displays this.

9. **Annual review** — Re-check ToS for all sources annually. Data providers occasionally change terms.

10. **DMCA process** — Have a process to remove images if a photographer requests takedown.

---

## Attribution Text Templates

**App footer:**
> Data from iNaturalist, USGS, NOAA, EPA, ODFW, BLM, USFS, Oregon DEQ, PRISM Climate Group, Paleobiology Database, GBIF, iDigBio, Macrostrat, and Oregon State Marine Board. Species photos © individual observers via iNaturalist (CC BY-NC). Geologic data from Macrostrat (Peters et al., 2018). Fossil data from PBDB (CC BY 4.0) and GBIF.

**Species photo credit:**
> Photo: [observer_name] / iNaturalist ([license])

**Fossil specimen credit:**
> Specimen: [museum] via [PBDB|GBIF|iDigBio]

**Weather:**
> Forecast: National Weather Service (NOAA)

**Water data:**
> Stream data: U.S. Geological Survey

---

## Sources

- [iNaturalist Terms of Use](https://www.inaturalist.org/pages/terms)
- [iNaturalist Licensing Help](https://help.inaturalist.org/en/support/solutions/articles/151000173511)
- [USGS Copyrights and Credits](https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits)
- [USGS Data Licensing](https://www.usgs.gov/data-management/data-licensing)
- [GBIF Data User Agreement](https://www.gbif.org/terms/data-user)
- [GBIF Citation Guidelines](https://www.gbif.org/citation-guidelines)
- [PBDB CC BY License](https://creativecommons.org/2013/12/19/paleobiology-database-now-cc-by/)
- [iDigBio Terms of Use](https://www.idigbio.org/content/idigbio-terms-use-policy)
- [iDigBio Intellectual Property Policy](https://www.idigbio.org/content/idigbio-intellectual-property-policy)
- [NWS Disclaimer / Terms](https://www.weather.gov/disclaimer)
- [EPA Data License](https://edg.epa.gov/epa_data_license.html)
- [BLM Disclaimer Policy](https://www.blm.gov/policy/im-2014-029)
- [Macrostrat (Peters et al., 2018)](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2018GC007467)
- [PRISM Climate Group](https://prism.oregonstate.edu/)
