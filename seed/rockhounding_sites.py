"""
Oregon Rockhounding Sites — curated seed data for RiverSignal.

Well-documented public collecting locations across Oregon, with emphasis on
sites within or near the 5 tracked watersheds (mckenzie, deschutes, metolius,
klamath, johnday) plus major destination sites elsewhere in the state.

Each entry carries coordinates, land ownership, collecting rules, and
watershed proximity tags for spatial filtering.

Usage:
    from seed.rockhounding_sites import ROCKHOUNDING_SITES
    # Insert into DB, generate GeoJSON, etc.
"""

ROCKHOUNDING_SITES = [
    # -------------------------------------------------------------------------
    # 1. Glass Buttes — world-class obsidian
    # -------------------------------------------------------------------------
    {
        "name": "Glass Buttes",
        "rock_type": "obsidian, fire obsidian, rainbow obsidian, mahogany obsidian",
        "latitude": 43.5683,
        "longitude": -120.0600,
        "land_owner": "BLM",
        "collecting_rules": (
            "Free collecting on BLM land. Surface collecting and hand tools "
            "only. No motorized digging. 25 lb/day limit per federal "
            "regulations for personal-use mineral collecting on BLM land."
        ),
        "nearest_town": "Hampton, OR",
        "description": (
            "Premier obsidian collecting destination in the western US. A "
            "complex of volcanic domes in the high desert east of Bend. "
            "Multiple distinct areas yield different obsidian varieties "
            "including prized fire obsidian with internal iridescence, "
            "rainbow, midnight lace, silver sheen, and mahogany obsidian. "
            "High clearance vehicle recommended. Best visited May-October."
        ),
        "watersheds": ["deschutes"],
    },
    # -------------------------------------------------------------------------
    # 2. Richardson's Rock Ranch — thundereggs
    # -------------------------------------------------------------------------
    {
        "name": "Richardson's Rock Ranch",
        "rock_type": "thundereggs, jasper, agate",
        "latitude": 44.6314,
        "longitude": -121.1728,
        "land_owner": "Private",
        "collecting_rules": (
            "Fee dig site. Pay per pound for thundereggs you dig. Open "
            "seasonally (typically spring through fall). Tools provided. "
            "Check website or call ahead for current hours and fees."
        ),
        "nearest_town": "Madras, OR",
        "description": (
            "Famous fee-dig thunderegg ranch north of Madras. Oregon's "
            "state rock, the thunderegg, is abundant here in welded tuff "
            "beds. Cut specimens reveal stunning agate, jasper, and opal "
            "interiors. Family-friendly. Located near the Deschutes/Metolius "
            "confluence at Lake Billy Chinook."
        ),
        "watersheds": ["deschutes", "metolius"],
    },
    # -------------------------------------------------------------------------
    # 3. Succor Creek — thundereggs, picture jasper
    # -------------------------------------------------------------------------
    {
        "name": "Succor Creek State Natural Area",
        "rock_type": "thundereggs, picture jasper, agate, petrified wood",
        "latitude": 43.5100,
        "longitude": -117.1000,
        "land_owner": "State / BLM",
        "collecting_rules": (
            "Collecting permitted in the BLM-managed areas along Succor "
            "Creek. No collecting within the State Natural Area itself. "
            "Surface collecting and hand digging. 25 lb/day limit on BLM "
            "land. Remote area; bring water, fuel, and spare tire."
        ),
        "nearest_town": "Adrian, OR",
        "description": (
            "Remote canyon in far southeastern Oregon near the Idaho border. "
            "Renowned for high-quality thundereggs in rhyolite ash beds and "
            "colorful picture jasper. The volcanic tuff canyon walls are "
            "studded with thunderegg nodules. One of Oregon's classic "
            "rockhounding destinations. Rough gravel roads."
        ),
        "watersheds": [],
    },
    # -------------------------------------------------------------------------
    # 4. Oregon Sunstone Public Collection Area (Plush)
    # -------------------------------------------------------------------------
    {
        "name": "Oregon Sunstone Public Collection Area",
        "rock_type": "sunstone, feldspar",
        "latitude": 42.7472,
        "longitude": -119.9822,
        "land_owner": "BLM",
        "collecting_rules": (
            "Free collecting on the BLM-designated public collection area. "
            "Hand tools only. Surface collecting and shallow digging. "
            "No motorized equipment. Personal use amounts. The site is "
            "clearly signed. Nearby private fee-dig mines offer guided "
            "experiences (Dust Devil, Spectrum, Double Eagle)."
        ),
        "nearest_town": "Plush, OR",
        "description": (
            "The only locality in the world where gem-quality Oregon "
            "sunstone (a copper-bearing labradorite feldspar) is found in "
            "basalt lava flows. Stones range from straw-yellow to "
            "intense red, green, and bicolor. Oregon's official state "
            "gemstone. Very remote high desert — bring everything you need. "
            "Best collecting June-October."
        ),
        "watersheds": ["klamath"],
    },
    # -------------------------------------------------------------------------
    # 5. Hampton Butte — petrified wood
    # -------------------------------------------------------------------------
    {
        "name": "Hampton Butte",
        "rock_type": "petrified wood, agate, jasper",
        "latitude": 43.7650,
        "longitude": -120.2750,
        "land_owner": "BLM",
        "collecting_rules": (
            "Free collecting on BLM land. Surface collecting and hand tools. "
            "25 lb/day or 250 lb/year limit for petrified wood on BLM land "
            "per federal regulation. No commercial collecting without permit."
        ),
        "nearest_town": "Hampton, OR",
        "description": (
            "High desert area south of the Bend-Burns highway (US 20) known "
            "for scattered petrified wood on the desert floor. The ancient "
            "wood comes from Miocene-era forests buried by volcanic ash. "
            "Also produces agate and jasper. Vast open BLM land with "
            "multiple access points. High clearance helpful."
        ),
        "watersheds": ["deschutes"],
    },
    # -------------------------------------------------------------------------
    # 6. Biggs Junction — Biggs jasper, agates
    # -------------------------------------------------------------------------
    {
        "name": "Biggs Junction Area",
        "rock_type": "picture jasper (Biggs jasper), agate, petrified wood",
        "latitude": 45.6200,
        "longitude": -120.8350,
        "land_owner": "BLM / Private",
        "collecting_rules": (
            "Mixed land ownership — verify BLM vs private parcels before "
            "collecting. Classic Biggs jasper localities are largely on "
            "private ranch land (permission required). Some BLM parcels "
            "accessible. Surface collecting on public land."
        ),
        "nearest_town": "Biggs Junction, OR",
        "description": (
            "The type locality for Biggs jasper (also called Biggs picture "
            "jasper), a cream-to-tan jasper with striking landscape-like "
            "dendritic patterns. Found in basalt flows along the Columbia "
            "River. Highly prized by lapidary artists. Also produces "
            "Columbia River agates. Much of the best ground is private."
        ),
        "watersheds": [],
    },
    # -------------------------------------------------------------------------
    # 7. Priday Agate Beds / Madras area
    # -------------------------------------------------------------------------
    {
        "name": "Priday Agate Beds (Madras)",
        "rock_type": "plume agate, thundereggs, moss agate, Priday plume agate",
        "latitude": 44.6800,
        "longitude": -121.1400,
        "land_owner": "Private / BLM",
        "collecting_rules": (
            "The original Priday ranch beds are on private land and no longer "
            "open to public collecting. Richardson's Rock Ranch (nearby) "
            "offers fee-dig access to similar beds. Some BLM parcels in the "
            "greater Madras area still produce thundereggs and agates."
        ),
        "nearest_town": "Madras, OR",
        "description": (
            "Historic source of the world-famous Priday plume agate, a "
            "translucent agate with delicate red, black, and yellow plume "
            "inclusions. While the original Priday beds are closed, the "
            "Madras area remains one of Oregon's top rockhounding regions. "
            "The welded tuffs and rhyolite formations around Madras are "
            "prolific thunderegg producers."
        ),
        "watersheds": ["deschutes", "metolius"],
    },
    # -------------------------------------------------------------------------
    # 8. Ochoco National Forest / Whistler Springs — thundereggs
    # -------------------------------------------------------------------------
    {
        "name": "Whistler Springs (Ochoco NF)",
        "rock_type": "thundereggs, agate, jasper",
        "latitude": 44.3500,
        "longitude": -120.1300,
        "land_owner": "USFS (Ochoco National Forest)",
        "collecting_rules": (
            "Collecting for personal use is generally permitted on National "
            "Forest land. Hand tools only. Reasonable quantities for personal "
            "use. No commercial collecting. Check with Ochoco NF ranger "
            "district for current restrictions. Some areas may be seasonally "
            "closed."
        ),
        "nearest_town": "Prineville, OR",
        "description": (
            "Collecting area in the Ochoco National Forest east of "
            "Prineville. The Ochoco Mountains are a thunderegg hotspot — "
            "the rhyolitic volcanic tuffs here produce thundereggs with "
            "agate, jasper, and occasional opal interiors. Whistler Springs "
            "is one of several documented sites in the Ochocos. Forest roads "
            "provide access. Check conditions in spring (snow/mud)."
        ),
        "watersheds": ["deschutes", "johnday"],
    },
    # -------------------------------------------------------------------------
    # 9. Graveyard Point — plume agate
    # -------------------------------------------------------------------------
    {
        "name": "Graveyard Point",
        "rock_type": "plume agate, moss agate, jasper",
        "latitude": 43.6300,
        "longitude": -117.0400,
        "land_owner": "BLM",
        "collecting_rules": (
            "Free collecting on BLM land. Surface collecting and hand tools. "
            "25 lb/day limit. Located on the Oregon-Idaho border; ensure "
            "you are on the Oregon (BLM) side. Remote area."
        ),
        "nearest_town": "Adrian, OR",
        "description": (
            "Located on the Oregon-Idaho border near the Owyhee River, "
            "Graveyard Point is famous for spectacular plume agate with "
            "delicate feathery plume inclusions in clear to translucent "
            "chalcedony. One of the premier plume agate localities in "
            "North America. The agates weather out of volcanic ash beds. "
            "Remote Owyhee country — prepare for self-sufficiency."
        ),
        "watersheds": [],
    },
    # -------------------------------------------------------------------------
    # 10. Opal Butte
    # -------------------------------------------------------------------------
    {
        "name": "Opal Butte",
        "rock_type": "precious opal, fire opal, crystal opal, hyalite opal",
        "latitude": 44.8100,
        "longitude": -119.3900,
        "land_owner": "Private",
        "collecting_rules": (
            "Private mining claim. No public collecting without permission. "
            "Opal Butte Mine operates as a commercial mine and occasionally "
            "offers guided experiences. Contact the mine owners. Do not "
            "trespass on active mining claims."
        ),
        "nearest_town": "Heppner, OR",
        "description": (
            "Source of some of the finest precious opal in North America. "
            "Contra luz opal, crystal opal, and hydrophane opal from "
            "rhyolite host rock. Specimens are museum-quality. The mine is "
            "privately operated and not generally open to the public, but it "
            "is an important Oregon mineral locality. Located in the Blue "
            "Mountains of northeastern Oregon."
        ),
        "watersheds": ["johnday"],
    },
    # -------------------------------------------------------------------------
    # 11. Blue Basin / John Day Fossil Beds (Sheep Rock Unit)
    # -------------------------------------------------------------------------
    {
        "name": "Blue Basin (John Day Fossil Beds NM)",
        "rock_type": "fossils (viewing only), blue-green claystone",
        "latitude": 44.6614,
        "longitude": -119.6386,
        "land_owner": "NPS (National Park Service)",
        "collecting_rules": (
            "NO COLLECTING. National Monument — all rocks, minerals, fossils, "
            "and natural features are fully protected. Removal of any "
            "material is a federal offense. Enjoy the hiking trails and "
            "interpretive exhibits. The Thomas Condon Paleontology Center "
            "has excellent fossil displays."
        ),
        "nearest_town": "Dayville, OR",
        "description": (
            "Spectacular blue-green badlands formed from volcanic ash "
            "(John Day Formation, ~29 million years old). World-famous "
            "Oligocene mammal fossils including oreodonts, early horses, "
            "and saber-toothed cats. No collecting allowed, but an "
            "essential stop for understanding Oregon's geologic story. "
            "The Island in Time trail winds through the amphitheater. "
            "Important context site for nearby collecting areas."
        ),
        "watersheds": ["johnday"],
    },
    # -------------------------------------------------------------------------
    # 12. Newberry Volcanic Monument — obsidian
    # -------------------------------------------------------------------------
    {
        "name": "Newberry Volcanic Monument (Big Obsidian Flow)",
        "rock_type": "obsidian",
        "latitude": 43.6942,
        "longitude": -121.2308,
        "land_owner": "USFS (Newberry National Volcanic Monument)",
        "collecting_rules": (
            "NO COLLECTING within the National Volcanic Monument. The Big "
            "Obsidian Flow is a protected geological feature. Enjoy the "
            "interpretive trail across the 1,300-year-old lava flow. "
            "Northwest Forest Pass required for parking. Collecting "
            "obsidian is available at Glass Buttes (BLM) to the southeast."
        ),
        "nearest_town": "La Pine, OR",
        "description": (
            "Oregon's youngest lava flow (~1,300 years old), a massive "
            "obsidian and pumice flow within Newberry Caldera. The "
            "interpretive trail crosses the flow and obsidian is visible "
            "everywhere. No collecting allowed, but it is the best place "
            "to understand obsidian formation in Oregon. Paulina and East "
            "Lakes inside the caldera are scenic. Day-use fee area."
        ),
        "watersheds": ["deschutes"],
    },
    # -------------------------------------------------------------------------
    # 13. Hart Mountain area — sunstone
    # -------------------------------------------------------------------------
    {
        "name": "Hart Mountain / Warner Valley Sunstone Area",
        "rock_type": "sunstone, feldspar crystals",
        "latitude": 42.6500,
        "longitude": -119.7000,
        "land_owner": "BLM / USFWS",
        "collecting_rules": (
            "The BLM Sunstone Public Collection Area is the primary legal "
            "collecting site (see separate entry). Hart Mountain National "
            "Antelope Refuge is USFWS land — collecting not permitted "
            "within the Refuge. Private fee-dig mines in the area offer "
            "additional access."
        ),
        "nearest_town": "Plush, OR",
        "description": (
            "The broader Warner Valley / Hart Mountain region of Lake "
            "County is the heart of Oregon sunstone country. Gem-quality "
            "copper-bearing labradorite feldspar is found in basalt flows "
            "across the area. The BLM public site and several private mines "
            "(Dust Devil, Spectrum, Double Eagle) are concentrated north "
            "of Plush. Very remote — nearest services in Lakeview (80 mi)."
        ),
        "watersheds": ["klamath"],
    },
    # -------------------------------------------------------------------------
    # 14. Lucky Strike Mine (thundereggs)
    # -------------------------------------------------------------------------
    {
        "name": "Lucky Strike Mine / Thunderegg Mine",
        "rock_type": "thundereggs, agate, jasper",
        "latitude": 44.4300,
        "longitude": -120.2800,
        "land_owner": "Private (mining claim on USFS land)",
        "collecting_rules": (
            "Private mining claim. Check current status — historically "
            "operated as a fee-dig site. Contact owners for permission "
            "and current hours/fees. Located in the Ochoco Mountains. "
            "Do not dig without confirming the claim is open to visitors."
        ),
        "nearest_town": "Prineville, OR",
        "description": (
            "Historic thunderegg collecting site in the Ochoco Mountains "
            "east of Prineville. Produces thundereggs with colorful agate "
            "and jasper interiors from rhyolitic tuff. One of several "
            "named thunderegg localities in the Ochocos (along with "
            "Whistler Springs, White Fir Springs, and Steins Pillar area). "
            "Access via USFS roads — verify claim status before visiting."
        ),
        "watersheds": ["deschutes", "johnday"],
    },
    # -------------------------------------------------------------------------
    # 15. Steins Pillar area — thundereggs, agate
    # -------------------------------------------------------------------------
    {
        "name": "Steins Pillar Area (Ochoco NF)",
        "rock_type": "thundereggs, agate, jasper, geodes",
        "latitude": 44.3700,
        "longitude": -120.4000,
        "land_owner": "USFS (Ochoco National Forest)",
        "collecting_rules": (
            "Personal-use collecting generally permitted on National Forest "
            "land. Hand tools only. Reasonable quantities. Check with "
            "Lookout Mountain Ranger District. The pillar itself is a "
            "protected geologic feature — do not collect from the formation."
        ),
        "nearest_town": "Prineville, OR",
        "description": (
            "Area surrounding Steins Pillar, a dramatic 350-foot volcanic "
            "spire in the Ochocos. The welded tuffs in this area produce "
            "thundereggs and agates. The pillar itself is an eroded remnant "
            "of a 25-million-year-old ash flow. Good thunderegg hunting in "
            "the surrounding forest. Scenic hike to the base of the pillar."
        ),
        "watersheds": ["deschutes"],
    },
    # -------------------------------------------------------------------------
    # 16. White Fir Springs (Ochoco NF) — thundereggs
    # -------------------------------------------------------------------------
    {
        "name": "White Fir Springs (Ochoco NF)",
        "rock_type": "thundereggs, blue agate, moss agate",
        "latitude": 44.3100,
        "longitude": -120.2500,
        "land_owner": "USFS (Ochoco National Forest)",
        "collecting_rules": (
            "Personal-use collecting on National Forest land. Hand tools "
            "only. Reasonable quantities. Historically a popular dig site "
            "with organized group digs. Check current access with Ochoco "
            "NF ranger district."
        ),
        "nearest_town": "Prineville, OR",
        "description": (
            "Another well-known Ochoco thunderegg locality. Produces "
            "thundereggs with blue agate and moss agate interiors. The "
            "Blue Mountain province of central Oregon has extensive "
            "rhyolitic tuff deposits that formed thundereggs during "
            "Oligocene volcanic events. Located south of Prineville on "
            "forest roads."
        ),
        "watersheds": ["deschutes", "johnday"],
    },
    # -------------------------------------------------------------------------
    # 17. Madras Deschutes River Gravels — agates
    # -------------------------------------------------------------------------
    {
        "name": "Deschutes River Gravels (Madras area)",
        "rock_type": "agate, jasper, petrified wood, chalcedony",
        "latitude": 44.6330,
        "longitude": -121.1290,
        "land_owner": "BLM / State",
        "collecting_rules": (
            "Surface collecting of loose river-tumbled stones on public "
            "land along the Deschutes River. Do not disturb riverbanks or "
            "riparian areas. Check specific land ownership at each access "
            "point. BLM 25 lb/day limit applies."
        ),
        "nearest_town": "Madras, OR",
        "description": (
            "The Deschutes River and its tributaries have tumbled agates, "
            "jasper, and petrified wood from upstream volcanic sources for "
            "millennia. Gravel bars and exposed terraces near Madras yield "
            "water-polished agates and jasper. A good casual collecting "
            "area combined with other Madras-area attractions."
        ),
        "watersheds": ["deschutes", "metolius"],
    },
    # -------------------------------------------------------------------------
    # 18. Dust Devil Mine — sunstone (fee dig)
    # -------------------------------------------------------------------------
    {
        "name": "Dust Devil Mine",
        "rock_type": "sunstone, gem-quality labradorite",
        "latitude": 42.7800,
        "longitude": -120.0100,
        "land_owner": "Private",
        "collecting_rules": (
            "Fee dig site. Daily fee for digging; keep what you find. "
            "Open seasonally (approximately May-October, weather permitting). "
            "Tools and screening equipment provided. Reservations "
            "recommended. Check website for current season dates and rates."
        ),
        "nearest_town": "Plush, OR",
        "description": (
            "One of the premier private sunstone mines in Lake County. "
            "Produces gem-quality Oregon sunstone including red, green, "
            "and rare bicolor/tricolor stones with copper schiller. "
            "Operated as a fee-dig experience. Well-run operation with "
            "good success rates for diggers. Very remote — plan for "
            "primitive camping or stay in Lakeview."
        ),
        "watersheds": ["klamath"],
    },
    # -------------------------------------------------------------------------
    # 19. Spectrum Mine — sunstone (fee dig)
    # -------------------------------------------------------------------------
    {
        "name": "Spectrum Sunstone Mine",
        "rock_type": "sunstone, gem-quality labradorite",
        "latitude": 42.7600,
        "longitude": -119.9600,
        "land_owner": "Private",
        "collecting_rules": (
            "Fee dig site. Daily digging fees; keep what you find. Open "
            "seasonally. Contact mine for current hours and availability. "
            "Known for producing large gem-quality stones."
        ),
        "nearest_town": "Plush, OR",
        "description": (
            "Private fee-dig sunstone mine in the Plush sunstone district. "
            "Known for producing some of the largest and finest Oregon "
            "sunstones, including rare green and bicolor specimens. "
            "Experienced miners and gem buyers on site. A destination for "
            "serious sunstone collectors."
        ),
        "watersheds": ["klamath"],
    },
    # -------------------------------------------------------------------------
    # 20. Painted Hills Unit (John Day Fossil Beds)
    # -------------------------------------------------------------------------
    {
        "name": "Painted Hills (John Day Fossil Beds NM)",
        "rock_type": "fossils (viewing only), leaf fossils in area",
        "latitude": 44.6620,
        "longitude": -120.2490,
        "land_owner": "NPS (National Park Service)",
        "collecting_rules": (
            "NO COLLECTING. National Monument — all materials protected. "
            "Outstanding geology interpretive site. Leaf fossil exhibits. "
            "Stay on trails to protect fragile clay formations."
        ),
        "nearest_town": "Mitchell, OR",
        "description": (
            "Brilliantly colored striped hills of red, gold, and black "
            "claystone from 33-million-year-old volcanic ash deposits. "
            "Contains important Eocene plant fossils. While no collecting "
            "is allowed, the Painted Hills are essential geological context "
            "for the surrounding rockhounding region. The Bridge Creek "
            "Flora leaf fossils preserved here are world-famous."
        ),
        "watersheds": ["johnday"],
    },
    # -------------------------------------------------------------------------
    # 21. Clarno Unit (John Day Fossil Beds)
    # -------------------------------------------------------------------------
    {
        "name": "Clarno Unit (John Day Fossil Beds NM)",
        "rock_type": "fossils (viewing only), petrified wood (viewing only)",
        "latitude": 44.9200,
        "longitude": -120.4240,
        "land_owner": "NPS (National Park Service)",
        "collecting_rules": (
            "NO COLLECTING. National Monument — all materials protected. "
            "The Clarno Palisades and Trail of Fossils offer close-up "
            "views of 44-million-year-old fossils embedded in mudflow "
            "deposits."
        ),
        "nearest_town": "Fossil, OR",
        "description": (
            "Oldest unit of John Day Fossil Beds (Eocene, ~44 Ma). The "
            "Clarno Palisades are towering mudflow deposits containing "
            "tropical plant and animal fossils from when Oregon had a "
            "subtropical climate. Petrified logs visible in the cliff "
            "faces. Another no-collecting context site that illuminates "
            "the geology of central Oregon's collecting areas."
        ),
        "watersheds": ["johnday"],
    },
    # -------------------------------------------------------------------------
    # 22. Crooked River (Prineville area) — agates
    # -------------------------------------------------------------------------
    {
        "name": "Crooked River Gravels (Prineville area)",
        "rock_type": "agate, jasper, thundereggs, petrified wood",
        "latitude": 44.3000,
        "longitude": -120.7300,
        "land_owner": "BLM / State",
        "collecting_rules": (
            "Surface collecting on public land along the Crooked River. "
            "BLM gravel deposits accessible at various pull-offs. Stay on "
            "public land — check ownership. 25 lb/day limit on BLM land."
        ),
        "nearest_town": "Prineville, OR",
        "description": (
            "The Crooked River, a tributary of the Deschutes, carries "
            "agate, jasper, and thunderegg fragments from the Ochoco "
            "Mountains. Gravel bars and road cuts near Prineville produce "
            "tumbled specimens. The Prineville area is the gateway to "
            "Oregon's thunderegg country. Combine with visits to Ochoco "
            "NF sites for a full rockhounding trip."
        ),
        "watersheds": ["deschutes"],
    },
    # -------------------------------------------------------------------------
    # 23. Eagle Creek (Ochoco area) — thundereggs, fossils
    # -------------------------------------------------------------------------
    {
        "name": "Eagle Creek Area (Ochoco NF)",
        "rock_type": "thundereggs, petrified wood, plant fossils",
        "latitude": 44.4100,
        "longitude": -120.0800,
        "land_owner": "USFS (Ochoco National Forest)",
        "collecting_rules": (
            "Personal-use collecting on National Forest land. Hand tools "
            "only. Reasonable quantities. Some petrified wood localities "
            "near Eagle Creek. Forest roads; check conditions."
        ),
        "nearest_town": "Prineville, OR",
        "description": (
            "Eastern Ochoco Mountains area accessible via Eagle Creek "
            "road. Scattered thunderegg and petrified wood occurrences "
            "in volcanic tuffs and sedimentary beds. The Ochoco NF "
            "contains dozens of documented thunderegg localities across "
            "its extent. Less visited than sites closer to Prineville."
        ),
        "watersheds": ["johnday"],
    },
    # -------------------------------------------------------------------------
    # 24. McKenzie Pass Lava Fields
    # -------------------------------------------------------------------------
    {
        "name": "McKenzie Pass Lava Fields",
        "rock_type": "obsidian (in basalt), volcanic glass, lava rock (viewing only)",
        "latitude": 44.2570,
        "longitude": -121.8000,
        "land_owner": "USFS (Willamette / Deschutes National Forest)",
        "collecting_rules": (
            "The lava flows along McKenzie Pass (Hwy 242) are within "
            "designated Wilderness (Three Sisters) — NO COLLECTING in "
            "Wilderness areas. The Dee Wright Observatory area is day-use. "
            "Enjoy the geology but leave everything in place. Nearby "
            "non-Wilderness NF land may allow limited personal collecting."
        ),
        "nearest_town": "Sisters, OR",
        "description": (
            "Dramatic 1,500-year-old lava flows crossing the Cascade "
            "crest between Eugene and Sisters. Basaltic lava with "
            "occasional obsidian inclusions visible at road cuts. The "
            "Dee Wright Observatory at the pass summit provides 360-degree "
            "views of Cascade volcanoes. Seasonal road (closed in winter). "
            "Important geologic context for the McKenzie watershed."
        ),
        "watersheds": ["mckenzie", "deschutes"],
    },
    # -------------------------------------------------------------------------
    # 25. Prineville Reservoir area — agate, jasper
    # -------------------------------------------------------------------------
    {
        "name": "Prineville Reservoir Area",
        "rock_type": "agate, jasper, petrified wood, thundereggs",
        "latitude": 44.1500,
        "longitude": -120.7200,
        "land_owner": "BLM / State Parks",
        "collecting_rules": (
            "Collecting permitted on surrounding BLM land. No collecting "
            "within State Park boundaries. Agates and jasper can be found "
            "in exposed gravel deposits and road cuts around the reservoir. "
            "Surface collecting; 25 lb/day on BLM land."
        ),
        "nearest_town": "Prineville, OR",
        "description": (
            "Prineville Reservoir on the Crooked River is surrounded by "
            "BLM land that produces agates, jasper, and occasional "
            "thunderegg fragments. The canyon walls expose volcanic "
            "formations. A good area for casual collecting combined with "
            "camping and recreation at the reservoir. State Park campground "
            "provides a convenient base."
        ),
        "watersheds": ["deschutes"],
    },
    # -------------------------------------------------------------------------
    # 26. Horse Heaven Mining District — opal, thundereggs
    # -------------------------------------------------------------------------
    {
        "name": "Horse Heaven Mining District",
        "rock_type": "opal, fire opal, thundereggs, agate",
        "latitude": 44.4550,
        "longitude": -117.6200,
        "land_owner": "BLM / Private (mining claims)",
        "collecting_rules": (
            "Mixed ownership with active mining claims. Respect claim "
            "markers. BLM land open for personal-use collecting where "
            "not claimed. Some areas produce precious opal in rhyolite. "
            "Remote area — verify land status before collecting."
        ),
        "nearest_town": "Westfall, OR",
        "description": (
            "Historic mining district in Malheur County known for precious "
            "opal in rhyolite (similar to Opal Butte material). "
            "Thundereggs also occur in the area. Remote eastern Oregon "
            "location. The district has been mined intermittently since "
            "the early 1900s. Some spectacular fire opal has come from "
            "this area."
        ),
        "watersheds": [],
    },
    # -------------------------------------------------------------------------
    # 27. Lakeview area — sunstone, obsidian, petrified wood
    # -------------------------------------------------------------------------
    {
        "name": "Lakeview / Goose Lake Area",
        "rock_type": "sunstone, obsidian, petrified wood, agate",
        "latitude": 42.1900,
        "longitude": -120.3450,
        "land_owner": "BLM / USFS",
        "collecting_rules": (
            "BLM and Fremont-Winema NF lands in the area allow personal-use "
            "collecting. Hand tools only. The sunstone public collecting "
            "area is north of Lakeview near Plush. Obsidian and petrified "
            "wood found in various BLM parcels."
        ),
        "nearest_town": "Lakeview, OR",
        "description": (
            "Gateway town for Oregon's sunstone district and the "
            "Basin and Range province. Various collecting opportunities "
            "on public land in the surrounding high desert. Obsidian from "
            "nearby volcanic sources, petrified wood in Tertiary "
            "sediments, and agates in gravel deposits. Lakeview provides "
            "the nearest services for sunstone area visits."
        ),
        "watersheds": ["klamath"],
    },
    # -------------------------------------------------------------------------
    # 28. Bend / Tumalo area — obsidian, lava
    # -------------------------------------------------------------------------
    {
        "name": "Bend / Tumalo Volcanic Area",
        "rock_type": "obsidian, pumice, volcanic glass, scoria",
        "latitude": 44.0582,
        "longitude": -121.3153,
        "land_owner": "USFS (Deschutes National Forest) / BLM",
        "collecting_rules": (
            "Limited collecting of common volcanic materials may be "
            "permitted on Deschutes NF land outside of Wilderness and "
            "special management areas. Check with Bend-Fort Rock Ranger "
            "District. Newberry Monument and Wilderness areas are "
            "off-limits. Small obsidian chips found casually in some areas."
        ),
        "nearest_town": "Bend, OR",
        "description": (
            "The Bend area sits on the edge of an immense volcanic "
            "landscape. Obsidian, pumice, and volcanic glass are "
            "common in the soils and gravel. While most significant "
            "sites require going to Glass Buttes or Newberry, casual "
            "volcanic rock finds are everywhere in this region. The area "
            "provides good base-camp access to multiple collecting sites."
        ),
        "watersheds": ["deschutes"],
    },
    # -------------------------------------------------------------------------
    # 29. Carey Act Plume Agate area (Friday/Madras)
    # -------------------------------------------------------------------------
    {
        "name": "Ashwood / Trout Creek Area",
        "rock_type": "thundereggs, agate, jasper, zeolites",
        "latitude": 44.7300,
        "longitude": -120.7200,
        "land_owner": "BLM / Private",
        "collecting_rules": (
            "Mixed land ownership. BLM parcels allow personal-use "
            "collecting. Private ranch land requires permission. The "
            "Ashwood area has historically produced fine thundereggs. "
            "Verify land status before collecting."
        ),
        "nearest_town": "Ashwood, OR",
        "description": (
            "The Ashwood area along Trout Creek is a classic Oregon "
            "rockhounding district. Thundereggs and agates in welded "
            "tuffs and rhyolites of the Clarno and John Day Formations. "
            "Some zeolite minerals in the volcanic rocks. Historic "
            "collecting area that has produced fine specimens for decades. "
            "Between Madras and the Painted Hills."
        ),
        "watersheds": ["deschutes", "johnday"],
    },
    # -------------------------------------------------------------------------
    # 30. Maury Mountains — thundereggs, agate
    # -------------------------------------------------------------------------
    {
        "name": "Maury Mountains",
        "rock_type": "thundereggs, agate, jasper, petrified wood",
        "latitude": 44.1200,
        "longitude": -120.3500,
        "land_owner": "BLM / USFS",
        "collecting_rules": (
            "Mixed BLM and Ochoco NF land. Personal-use collecting "
            "permitted on public land. Hand tools only. The Maury "
            "Mountains are less visited than the Ochocos proper but "
            "produce similar material. Check land ownership."
        ),
        "nearest_town": "Paulina, OR",
        "description": (
            "A smaller mountain range south of the Ochocos with similar "
            "volcanic geology. Thundereggs, agates, and petrified wood "
            "occur in the Tertiary volcanic formations. Less trafficked "
            "than the Prineville-area sites. Rough forest roads provide "
            "access to scattered collecting areas. The nearby town of "
            "Paulina is a very small ranching community."
        ),
        "watersheds": ["deschutes"],
    },
    # -------------------------------------------------------------------------
    # 31. Carey / Pony Butte area — thundereggs
    # -------------------------------------------------------------------------
    {
        "name": "Pony Butte (near Madras)",
        "rock_type": "thundereggs, agate",
        "latitude": 44.5800,
        "longitude": -121.0800,
        "land_owner": "BLM / Private",
        "collecting_rules": (
            "Some BLM parcels accessible. Much of the area is private "
            "ranch land — do not trespass. The BLM parcels in the area "
            "allow personal-use collecting. Surface collecting and hand "
            "tools. 25 lb/day limit."
        ),
        "nearest_town": "Madras, OR",
        "description": (
            "Low butte south of Madras that has produced thundereggs "
            "from welded tuff deposits. Part of the broader Madras "
            "thunderegg district that includes Richardson's Ranch and "
            "the Priday beds. Mixed land ownership — identify BLM "
            "parcels before collecting."
        ),
        "watersheds": ["deschutes"],
    },
    # -------------------------------------------------------------------------
    # 32. Mitchell area — leaf fossils, thundereggs
    # -------------------------------------------------------------------------
    {
        "name": "Mitchell / Bridge Creek Area",
        "rock_type": "leaf fossils, petrified wood, thundereggs, agate",
        "latitude": 44.5700,
        "longitude": -120.1500,
        "land_owner": "BLM / Private",
        "collecting_rules": (
            "Fossil collecting on BLM land is permitted for personal use "
            "(invertebrates and plant fossils; vertebrate fossils require "
            "permits). Mixed land ownership near Mitchell. The Painted "
            "Hills NM nearby is off-limits. BLM parcels along Bridge "
            "Creek may produce leaf fossils and petrified wood."
        ),
        "nearest_town": "Mitchell, OR",
        "description": (
            "The Mitchell area sits within the John Day Formation, one of "
            "the world's most important Tertiary fossil assemblages. The "
            "Bridge Creek Flora (plant fossils) is found in shales and "
            "tuffs around Mitchell. Leaf impressions of ancient oaks, "
            "maples, and metasequoia are common. Also produces "
            "thundereggs and petrified wood in surrounding volcanic beds."
        ),
        "watersheds": ["johnday"],
    },
    # -------------------------------------------------------------------------
    # 33. Klamath Falls / Hogback Mountain area
    # -------------------------------------------------------------------------
    {
        "name": "Hogback Mountain / Klamath Falls Area",
        "rock_type": "obsidian, petrified wood, agate",
        "latitude": 42.2500,
        "longitude": -121.7500,
        "land_owner": "BLM / USFS",
        "collecting_rules": (
            "BLM and Fremont-Winema NF lands in the Klamath Basin allow "
            "personal-use collecting. Check specific land ownership. "
            "Obsidian and volcanic materials found in various locations "
            "around the basin."
        ),
        "nearest_town": "Klamath Falls, OR",
        "description": (
            "The Klamath Basin has scattered rockhounding opportunities "
            "in the volcanic terrain surrounding Upper Klamath Lake. "
            "Obsidian from local volcanic sources, petrified wood in "
            "Tertiary sediments, and agates in gravel deposits. Less "
            "well-known than central Oregon sites but accessible from "
            "Klamath Falls. Good combined with sunstone area trips."
        ),
        "watersheds": ["klamath"],
    },
    # -------------------------------------------------------------------------
    # 34. Cove Palisades / Lake Billy Chinook area
    # -------------------------------------------------------------------------
    {
        "name": "Cove Palisades State Park Area",
        "rock_type": "agate, jasper, petrified wood, zeolites",
        "latitude": 44.5372,
        "longitude": -121.2700,
        "land_owner": "State Parks / BLM",
        "collecting_rules": (
            "No collecting within State Park boundaries. Surrounding BLM "
            "land may allow limited surface collecting. The canyon walls "
            "expose spectacular volcanic stratigraphy but are protected. "
            "Collect only on BLM land outside the park."
        ),
        "nearest_town": "Culver, OR",
        "description": (
            "Lake Billy Chinook reservoir at the confluence of the "
            "Deschutes, Crooked, and Metolius rivers. The canyon walls "
            "expose millions of years of volcanic stratigraphy including "
            "the Deschutes Formation and intracanyon basalt flows. "
            "Zeolites, agates, and jasper occur in the volcanic rocks. "
            "A geologically spectacular area with camping and recreation."
        ),
        "watersheds": ["deschutes", "metolius"],
    },
    # -------------------------------------------------------------------------
    # 35. Fields / Alvord Desert area — obsidian, agate, geodes
    # -------------------------------------------------------------------------
    {
        "name": "Fields / Alvord Desert Area",
        "rock_type": "obsidian, agate, geodes, petrified wood, sunstone",
        "latitude": 42.2700,
        "longitude": -118.6800,
        "land_owner": "BLM",
        "collecting_rules": (
            "Free collecting on BLM land. Vast open BLM land in the "
            "Alvord Desert region. Surface collecting and hand tools. "
            "25 lb/day limit. Extremely remote — bring all supplies. "
            "No services for many miles."
        ),
        "nearest_town": "Fields, OR",
        "description": (
            "The Alvord Desert and Steens Mountain region in far "
            "southeastern Oregon offers diverse rockhounding on BLM "
            "land. Obsidian from local volcanic sources, geodes in "
            "rhyolite, and agate in gravel deposits. Some areas produce "
            "sunstone. This is Oregon's most remote rockhounding terrain "
            "— absolute self-sufficiency required. Stunning scenery."
        ),
        "watersheds": [],
    },
    # -------------------------------------------------------------------------
    # 36. Fossil, Oregon area — plant fossils
    # -------------------------------------------------------------------------
    {
        "name": "Fossil, Oregon / Wheeler High School Fossil Beds",
        "rock_type": "leaf fossils, plant fossils",
        "latitude": 44.8700,
        "longitude": -120.2100,
        "land_owner": "City / Public",
        "collecting_rules": (
            "The Wheeler High School fossil beds behind the school are "
            "open to the public for collecting. Small fee or free (check "
            "locally). Bring your own hand tools. Keep reasonable amounts. "
            "One of the few places in Oregon where you can legally collect "
            "fossils from a designated public site."
        ),
        "nearest_town": "Fossil, OR",
        "description": (
            "The tiny town of Fossil, Oregon is aptly named — the hillside "
            "behind Wheeler High School is a public fossil collecting site "
            "where visitors can dig Eocene-era leaf and plant fossils from "
            "the John Day Formation. Impressions of ancient leaves, seeds, "
            "and insects in fine-grained tuff. Family-friendly and unique. "
            "One of the only designated public fossil collecting sites in "
            "the region."
        ),
        "watersheds": ["johnday"],
    },
    # -------------------------------------------------------------------------
    # 37. Ochoco Lake / Mill Creek area
    # -------------------------------------------------------------------------
    {
        "name": "Ochoco Lake / Mill Creek Area",
        "rock_type": "agate, jasper, thundereggs, petrified wood",
        "latitude": 44.2800,
        "longitude": -120.6300,
        "land_owner": "USFS / BLM / State",
        "collecting_rules": (
            "Collecting on USFS and BLM land for personal use. Ochoco "
            "Lake area has limited State Park land (no collecting). "
            "Mill Creek Wilderness is off-limits for collecting. Stay "
            "on non-Wilderness NF and BLM land."
        ),
        "nearest_town": "Prineville, OR",
        "description": (
            "The area east of Prineville around Ochoco Lake and Mill Creek "
            "is the western gateway to Ochoco thunderegg country. Agates, "
            "jasper, and petrified wood can be found in exposed volcanic "
            "deposits on public land. Good camping at Ochoco Lake and along "
            "Mill Creek. Scenic Ochoco Mountains backdrop."
        ),
        "watersheds": ["deschutes"],
    },
    # -------------------------------------------------------------------------
    # 38. Juniper Ridge / Brothers area — petrified wood
    # -------------------------------------------------------------------------
    {
        "name": "Brothers / Juniper Ridge Area",
        "rock_type": "petrified wood, agate, obsidian, jasper",
        "latitude": 43.8100,
        "longitude": -120.6000,
        "land_owner": "BLM",
        "collecting_rules": (
            "Free collecting on BLM land. The high desert around Brothers "
            "is largely BLM-managed. Surface collecting and hand tools. "
            "25 lb/day limit for petrified wood. Very remote — bring "
            "fuel and water."
        ),
        "nearest_town": "Brothers, OR",
        "description": (
            "The tiny community of Brothers sits in Oregon's high desert "
            "between Bend and Burns. The surrounding BLM land produces "
            "petrified wood, agates, and occasional obsidian. A transition "
            "zone between Cascade volcanic terrain and Basin and Range "
            "geology. Wide-open desert collecting with long views. "
            "Near the route to Glass Buttes."
        ),
        "watersheds": ["deschutes"],
    },
    # -------------------------------------------------------------------------
    # 39. Summer Lake area — fossils, obsidian
    # -------------------------------------------------------------------------
    {
        "name": "Summer Lake / Paisley Area",
        "rock_type": "obsidian, fossils, petrified wood, agate",
        "latitude": 42.9700,
        "longitude": -120.7700,
        "land_owner": "BLM / USFWS / State",
        "collecting_rules": (
            "BLM land allows personal-use collecting. Summer Lake Wildlife "
            "Refuge (USFWS) and Summer Lake State Natural Area are "
            "protected — no collecting. Verify land ownership. Important "
            "archaeological area — do not disturb any artifacts."
        ),
        "nearest_town": "Paisley, OR",
        "description": (
            "Summer Lake basin in south-central Oregon is a large pluvial "
            "lake basin with exposed Tertiary volcanic and sedimentary "
            "rocks. Obsidian and petrified wood found on BLM land. The "
            "Fort Rock / Christmas Valley area to the north also produces "
            "obsidian. The Paisley Caves (nearby) are an important "
            "archaeological site — respect all cultural resources."
        ),
        "watersheds": ["klamath"],
    },
    # -------------------------------------------------------------------------
    # 40. Sisters / Whychus Creek area
    # -------------------------------------------------------------------------
    {
        "name": "Sisters / Whychus Creek Volcanic Area",
        "rock_type": "obsidian, volcanic glass, agate, jasper",
        "latitude": 44.2910,
        "longitude": -121.5490,
        "land_owner": "USFS (Deschutes National Forest)",
        "collecting_rules": (
            "Limited personal-use collecting on Deschutes NF land outside "
            "designated Wilderness. Many areas near Sisters are within "
            "Three Sisters or Mt. Washington Wilderness — no collecting. "
            "Check with Sisters Ranger District for open areas."
        ),
        "nearest_town": "Sisters, OR",
        "description": (
            "The Sisters area straddles the Cascade volcanic zone with "
            "obsidian and volcanic glass in young lava flows. Whychus "
            "Creek (formerly Squaw Creek) drains volcanic terrain with "
            "tumbled agates and jasper in its gravels. Most prime volcanic "
            "terrain is in Wilderness. The town of Sisters is a good "
            "base camp for Metolius, McKenzie, and Deschutes area sites."
        ),
        "watersheds": ["deschutes", "metolius", "mckenzie"],
    },
]
