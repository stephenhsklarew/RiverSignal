"""
Green River Watershed (UT/WY) — curated seed data for RiverSignal.

Fly shops, guide services, mineral shops, rockhounding sites, and hatch chart
data for the Green River corridor from its headwaters in Wyoming's Wind River
Range through Flaming Gorge and down into eastern Utah.

Usage:
    from seed.green_river_curated import (
        FLY_SHOPS_GUIDES,
        MINERAL_SHOPS,
        ROCKHOUNDING_SITES,
        HATCH_CHART,
    )
"""

# =============================================================================
# 1. FLY_SHOPS_GUIDES — Fly fishing shops and guide services
# =============================================================================

FLY_SHOPS_GUIDES = [
    # -------------------------------------------------------------------------
    # Dutch John, UT — Green River below Flaming Gorge Dam
    # -------------------------------------------------------------------------
    {
        "name": "Trout Creek Flies",
        "type": "both",
        "watersheds": ["green_river"],
        "city": "Dutch John, UT",
        "address": "1155 Little Hole Rd, Dutch John, UT 84023",
        "lat": 40.9323,
        "lon": -109.3930,
        "phone": "435-885-3355",
        "website": "https://www.fishgreenriver.com",
        "description": (
            "The premier fly shop on the Green River below Flaming Gorge Dam. "
            "Full-service shop with daily fishing reports, extensive fly "
            "selection tied for local hatches, gear, and guided drift boat and "
            "walk-wade trips on sections A, B, and C. The go-to source for "
            "current conditions and flows."
        ),
    },
    {
        "name": "Flaming Gorge Resort",
        "type": "both",
        "watersheds": ["green_river"],
        "city": "Dutch John, UT",
        "address": "1100 E Flaming Gorge Resort, Dutch John, UT 84023",
        "lat": 40.9156,
        "lon": -109.3917,
        "phone": "435-889-3773",
        "website": "https://www.flaminggorgeresort.com",
        "description": (
            "Full-service resort near the dam offering lodging, raft rentals, "
            "fly shop, and guided fishing trips on the Green River. Convenient "
            "base camp for accessing the tailwater. Also offers Flaming Gorge "
            "Reservoir fishing and scenic raft trips."
        ),
    },
    {
        "name": "Old Moe Guide Service",
        "type": "guide_service",
        "watersheds": ["green_river"],
        "city": "Dutch John, UT",
        "address": "Dutch John, UT 84023",
        "lat": 40.9323,
        "lon": -109.3930,
        "phone": "435-885-3342",
        "website": "https://www.oldmoe.com",
        "description": (
            "Experienced guide service specializing in drift boat trips on "
            "the Green River below Flaming Gorge Dam. Known for patient, "
            "knowledgeable guides and consistent results on the A and B "
            "sections of the river."
        ),
    },
    {
        "name": "Green River Drifters",
        "type": "guide_service",
        "watersheds": ["green_river"],
        "city": "Dutch John, UT",
        "address": "Dutch John, UT 84023",
        "lat": 40.9323,
        "lon": -109.3930,
        "phone": "435-885-3338",
        "website": "https://www.greenriverdrifters.com",
        "description": (
            "Guide service offering drift boat fly fishing trips on the "
            "Green River tailwater. Full-day and half-day trips through the "
            "scenic red rock canyon below Flaming Gorge Dam. Also provides "
            "shuttle services and lodging packages."
        ),
    },
    {
        "name": "Spinner Fall Guide Service",
        "type": "guide_service",
        "watersheds": ["green_river"],
        "city": "Dutch John, UT",
        "address": "Dutch John, UT 84023",
        "lat": 40.9323,
        "lon": -109.3930,
        "phone": "435-885-3359",
        "website": "https://www.spinnerfall.com",
        "description": (
            "Full-service guide operation on the Green River below Flaming "
            "Gorge. Offers drift boat and walk-wade trips year-round. Known "
            "for technical dry fly fishing during summer hatches and expert "
            "nymphing instruction during winter months."
        ),
    },
    {
        "name": "Reel Fly Fishing Adventures",
        "type": "guide_service",
        "watersheds": ["green_river"],
        "city": "Dutch John, UT",
        "address": "Dutch John, UT 84023",
        "lat": 40.9323,
        "lon": -109.3930,
        "phone": "435-885-3291",
        "website": "https://www.reelflyfishing.com",
        "description": (
            "Guide service offering drift boat trips on the Green River "
            "tailwater below Flaming Gorge Dam. Specializes in both "
            "beginner-friendly instruction and technical fishing for "
            "experienced anglers targeting large browns and rainbows."
        ),
    },
    # -------------------------------------------------------------------------
    # Vernal, UT
    # -------------------------------------------------------------------------
    {
        "name": "Vernal Anglers",
        "type": "fly_shop",
        "watersheds": ["green_river"],
        "city": "Vernal, UT",
        "address": "73 E Main St, Vernal, UT 84078",
        "lat": 40.4555,
        "lon": -109.5287,
        "phone": "435-789-1702",
        "website": "",
        "description": (
            "Local fly and tackle shop in Vernal serving anglers heading to "
            "the Green River tailwater, Steinaker Reservoir, and other Uinta "
            "Basin waters. Supplies, local intel, and fishing licenses."
        ),
    },
    # -------------------------------------------------------------------------
    # Salt Lake City area — shops running Green River trips
    # -------------------------------------------------------------------------
    {
        "name": "Western Rivers Flyfisher",
        "type": "both",
        "watersheds": ["green_river", "provo_river", "weber_river"],
        "city": "Salt Lake City, UT",
        "address": "1071 E 900 S, Salt Lake City, UT 84105",
        "lat": 40.7478,
        "lon": -111.8614,
        "phone": "801-521-6424",
        "website": "https://www.westernriversflyfisher.com",
        "description": (
            "Premier Salt Lake City fly shop offering guided trips to the "
            "Green River below Flaming Gorge, Provo River, and other Utah "
            "waters. Full retail shop with extensive fly selection, gear, and "
            "expert advice. Runs multi-day Green River packages."
        ),
    },
    {
        "name": "Park City Anglers",
        "type": "both",
        "watersheds": ["green_river", "provo_river", "weber_river"],
        "city": "Park City, UT",
        "address": "1612 W Ute Blvd #112, Park City, UT 84098",
        "lat": 40.6849,
        "lon": -111.5070,
        "phone": "435-200-8038",
        "website": "https://www.parkcityanglers.com",
        "description": (
            "Park City-based fly shop and guide service running trips to the "
            "Green River tailwater, Provo River, and Weber River. Specializes "
            "in multi-day Green River float trips with lodging in Dutch John."
        ),
    },
    # -------------------------------------------------------------------------
    # Wyoming — Upper Green River
    # -------------------------------------------------------------------------
    {
        "name": "Two Rivers Emporium",
        "type": "both",
        "watersheds": ["green_river"],
        "city": "Pinedale, WY",
        "address": "211 W Pine St, Pinedale, WY 82941",
        "lat": 42.8666,
        "lon": -109.8608,
        "phone": "307-367-4131",
        "website": "https://www.2rivers.net",
        "description": (
            "Full-service fly shop in Pinedale serving the upper Green River "
            "and New Fork River drainages. Guided float and wade trips on the "
            "upper Green from its headwaters in the Wind River Range. Local "
            "expertise on Green River Lakes, New Fork, and area alpine lakes."
        ),
    },
    {
        "name": "Lakeside Lodge Resort & Marina",
        "type": "guide_service",
        "watersheds": ["green_river"],
        "city": "Pinedale, WY",
        "address": "99 S Fremont Lake Rd, Pinedale, WY 82941",
        "lat": 42.8298,
        "lon": -109.8158,
        "phone": "307-367-2221",
        "website": "https://www.lakesidelodge.com",
        "description": (
            "Resort and marina near Pinedale offering guided fishing on "
            "Fremont Lake and the upper Green River drainage. Access to "
            "Wind River Range backcountry fishing and float trips on the "
            "upper Green River."
        ),
    },
    {
        "name": "Bootjack Sports",
        "type": "fly_shop",
        "watersheds": ["green_river"],
        "city": "Pinedale, WY",
        "address": "40 S Franklin Ave, Pinedale, WY 82941",
        "lat": 42.8663,
        "lon": -109.8621,
        "phone": "307-367-2549",
        "website": "",
        "description": (
            "Sporting goods and fly shop in Pinedale with tackle, flies, and "
            "local knowledge for fishing the upper Green River, New Fork "
            "River, and Wind River Range alpine lakes. Fishing licenses "
            "available."
        ),
    },
]


# =============================================================================
# 2. MINERAL_SHOPS — Rock, gem, and fossil shops
# =============================================================================

MINERAL_SHOPS = [
    {
        "name": "Utah Field House of Natural History State Park Museum",
        "city": "Vernal, UT",
        "address": "496 E Main St, Vernal, UT 84078",
        "lat": 40.4555,
        "lon": -109.5214,
        "phone": "435-789-3799",
        "website": "https://stateparks.utah.gov/parks/utah-field-house/",
        "description": (
            "State park museum featuring Utah's paleontology and geology. "
            "Dinosaur galleries, fluorescent mineral room, fossil displays, "
            "and outdoor Dinosaur Garden with life-size replicas. Gift shop "
            "sells fossils, minerals, and geological books. Gateway museum "
            "for Dinosaur National Monument area."
        ),
        "watersheds": ["green_river"],
    },
    {
        "name": "Ulrich's Fossil Gallery",
        "city": "Kemmerer, WY",
        "address": "100 Pine Ave, Fossil Station, Kemmerer, WY 83101",
        "lat": 41.7816,
        "lon": -110.5266,
        "phone": "307-877-6466",
        "website": "https://www.ulrichsfossilgallery.com",
        "description": (
            "Premier fossil fish gallery and fee-dig quarry in the Green "
            "River Formation near Kemmerer. Retail gallery selling museum-"
            "quality Eocene fossil fish (Knightia, Diplomystus, Priscacara, "
            "Mioplosus), stingrays, palm fronds, and other specimens. "
            "Also operates a fee-dig quarry where visitors split their own "
            "50-million-year-old fossil fish."
        ),
        "watersheds": ["green_river"],
    },
    {
        "name": "Warfield Fossils",
        "city": "Kemmerer, WY",
        "address": "Warfield Creek Rd, Kemmerer, WY 83101",
        "lat": 41.7930,
        "lon": -110.5100,
        "phone": "307-877-6885",
        "website": "https://www.warfieldfossils.com",
        "description": (
            "Family-operated fossil quarry and gallery near Kemmerer in the "
            "Green River Formation. Fee-dig site where visitors can quarry "
            "their own Eocene fossil fish. Gallery sells prepared specimens "
            "including rare multi-plate compositions and large Diplomystus. "
            "Operating since the 1940s."
        ),
        "watersheds": ["green_river"],
    },
    {
        "name": "Tynsky's Rock Shop",
        "city": "Kemmerer, WY",
        "address": "912 Pine Ave, Kemmerer, WY 83101",
        "lat": 41.7925,
        "lon": -110.5375,
        "phone": "307-877-6958",
        "website": "",
        "description": (
            "Rock and fossil shop in Kemmerer selling Green River Formation "
            "fossil fish, local agates, jade, and other Wyoming minerals. "
            "Also carries lapidary supplies and polished specimens."
        ),
        "watersheds": ["green_river"],
    },
    {
        "name": "Sweetwater County Historical Museum",
        "city": "Green River, WY",
        "address": "3 E Flaming Gorge Way, Green River, WY 82935",
        "lat": 41.5285,
        "lon": -109.4660,
        "phone": "307-872-6435",
        "website": "https://www.sweetwatermuseum.org",
        "description": (
            "County museum in Green River, WY with geological and "
            "paleontological exhibits including Green River Formation fossil "
            "fish, Eocene-era displays, and regional mining history. Small "
            "gift shop with fossil replicas and mineral specimens."
        ),
        "watersheds": ["green_river"],
    },
    {
        "name": "Fossil Butte National Monument Visitor Center",
        "city": "Kemmerer, WY",
        "address": "864 Chicken Creek Rd, Kemmerer, WY 83101",
        "lat": 41.8617,
        "lon": -110.7633,
        "phone": "307-877-4455",
        "website": "https://www.nps.gov/fobu/",
        "description": (
            "National monument preserving the world's finest fossil fish "
            "deposits from Eocene Fossil Lake. Visitor center displays "
            "exceptional Green River Formation specimens including fish, "
            "crocodiles, turtles, bats, and plants. Research quarry "
            "demonstrations in summer. No collecting within monument — "
            "nearby private quarries offer fee digs."
        ),
        "watersheds": ["green_river"],
    },
    {
        "name": "Rock Springs Rock & Gem",
        "city": "Rock Springs, WY",
        "address": "Rock Springs, WY 82901",
        "lat": 41.5875,
        "lon": -109.2029,
        "phone": "",
        "website": "",
        "description": (
            "Rock and mineral shop in Rock Springs selling Wyoming jade, "
            "agates, petrified wood, and Green River Formation fossil fish. "
            "Located near extensive BLM collecting areas. Coordinates are "
            "approximate city center."
        ),
        "watersheds": ["green_river"],
    },
]


# =============================================================================
# 3. ROCKHOUNDING_SITES — Collecting locations
# =============================================================================

ROCKHOUNDING_SITES = [
    # -------------------------------------------------------------------------
    # Green River Formation fossil fish — Kemmerer, WY area
    # -------------------------------------------------------------------------
    {
        "name": "Ulrich's Fossil Quarry (Fee Dig)",
        "rock_type": "Eocene fossil fish (Knightia, Diplomystus, Priscacara)",
        "latitude": 41.7816,
        "longitude": -110.5266,
        "land_owner": "Private",
        "collecting_rules": (
            "Fee-dig operation. Pay per day to quarry your own fossil fish. "
            "All tools and instruction provided. Keep everything you find. "
            "Open seasonally, typically June through September. Reservations "
            "recommended."
        ),
        "nearest_town": "Kemmerer, WY",
        "description": (
            "Commercial fee-dig quarry in the Green River Formation near "
            "Kemmerer. Visitors split 50-million-year-old limestone layers "
            "to uncover beautifully preserved Eocene fish. Most common find "
            "is Knightia (herring relative); Diplomystus and Priscacara are "
            "rarer and more prized. One of the best hands-on fossil "
            "experiences in the world."
        ),
        "watersheds": ["green_river"],
    },
    {
        "name": "Warfield Fossils Quarry (Fee Dig)",
        "rock_type": "Eocene fossil fish (Knightia, Diplomystus)",
        "latitude": 41.7930,
        "longitude": -110.5100,
        "land_owner": "Private",
        "collecting_rules": (
            "Fee-dig operation. Daily fee includes tools, instruction, and "
            "all fossils found. Family-friendly. Open summer months. Call or "
            "check website for dates and rates."
        ),
        "nearest_town": "Kemmerer, WY",
        "description": (
            "Family-run fee-dig quarry in the Green River Formation operating "
            "since the 1940s. Excellent for families and beginners. Knightia "
            "are common; exceptional specimens of Diplomystus and other "
            "Eocene fauna occasionally found."
        ),
        "watersheds": ["green_river"],
    },
    {
        "name": "Fossil Butte National Monument",
        "rock_type": "Eocene fossil fish, plants, insects (viewing only)",
        "latitude": 41.8617,
        "longitude": -110.7633,
        "land_owner": "NPS",
        "collecting_rules": (
            "NO COLLECTING. National monument — all fossil and mineral "
            "collecting is strictly prohibited by federal law. Viewing and "
            "photography only. Attend ranger-led quarry demonstrations in "
            "summer to watch research preparation."
        ),
        "nearest_town": "Kemmerer, WY",
        "description": (
            "Preserves the finest Eocene fossil deposits from ancient "
            "Fossil Lake. Extraordinary specimens in the visitor center "
            "including complete fish, crocodiles, turtles, bats, birds, "
            "and palm fronds. Two hiking trails lead to fossil exposures. "
            "No collecting — but nearby private quarries offer fee digs."
        ),
        "watersheds": ["green_river"],
    },
    # -------------------------------------------------------------------------
    # BLM fossil fish areas — Green River, WY vicinity
    # -------------------------------------------------------------------------
    {
        "name": "Blue Forest Petrified Wood Area",
        "rock_type": "petrified wood, blue-grey agatized wood",
        "latitude": 41.6500,
        "longitude": -108.8500,
        "land_owner": "BLM",
        "collecting_rules": (
            "Free surface collecting on BLM land. 25 lb/day personal use "
            "limit per BLM regulations. Hand tools only. No commercial "
            "collecting without permit. High-clearance vehicle recommended."
        ),
        "nearest_town": "Eden, WY",
        "description": (
            "Famous collecting area in the Farson/Eden area of Wyoming's "
            "Red Desert. Blue-grey agatized petrified wood from Eocene "
            "forests. Some of the most unique petrified wood in the US with "
            "its distinctive blue-grey coloring. Large and small pieces "
            "found on the surface. Remote and arid — bring water and GPS."
        ),
        "watersheds": ["green_river"],
    },
    {
        "name": "Green River Formation BLM Areas (Kemmerer)",
        "rock_type": "Eocene fossil fish (Knightia), leaf impressions",
        "latitude": 41.7900,
        "longitude": -110.5400,
        "land_owner": "BLM",
        "collecting_rules": (
            "Surface collecting of common invertebrate fossils and "
            "reasonable amounts of common plant fossils is allowed on BLM "
            "land for personal use. Vertebrate fossils (fish, reptiles, "
            "mammals) require a paleontological resources use permit from "
            "the BLM for collection. Do not collect vertebrate fossils "
            "without a permit."
        ),
        "nearest_town": "Kemmerer, WY",
        "description": (
            "BLM-managed Green River Formation exposures near Kemmerer. "
            "Leaf impressions and invertebrate trace fossils can be surface "
            "collected. Vertebrate fossils including fish are protected "
            "under PRPA (Paleontological Resources Preservation Act) on "
            "federal land — a permit is required. Fee-dig quarries on "
            "private land nearby are the legal way to collect fossil fish."
        ),
        "watersheds": ["green_river"],
    },
    # -------------------------------------------------------------------------
    # Flaming Gorge area
    # -------------------------------------------------------------------------
    {
        "name": "Flaming Gorge Agate Beds",
        "rock_type": "agate, jasper, chert",
        "latitude": 40.9500,
        "longitude": -109.5000,
        "land_owner": "BLM / USFS (Ashley National Forest)",
        "collecting_rules": (
            "Free surface collecting on BLM land. Check land status — some "
            "areas are National Forest or National Recreation Area with "
            "different rules. 25 lb/day limit on BLM land. Collect only "
            "from the surface."
        ),
        "nearest_town": "Dutch John, UT",
        "description": (
            "Scattered agate, jasper, and colorful chert found in gravels "
            "and washes around the Flaming Gorge area. Red, brown, and "
            "banded agates in creek beds and road cuts. Best collecting in "
            "areas outside the National Recreation Area on BLM parcels. "
            "Combine with a fishing trip on the Green River."
        ),
        "watersheds": ["green_river"],
    },
    {
        "name": "Sheep Creek Geological Area",
        "rock_type": "geological formations, fossils (viewing only in USFS area)",
        "latitude": 40.9400,
        "longitude": -109.6500,
        "land_owner": "USFS (Ashley National Forest)",
        "collecting_rules": (
            "Geological Area within Ashley National Forest. Casual rock "
            "collecting of small amounts of common rocks and minerals is "
            "generally permitted on National Forest land, but check with "
            "the local ranger district for current rules. Do not collect "
            "fossils without a permit."
        ),
        "nearest_town": "Manila, UT",
        "description": (
            "Scenic geological area with dramatically upturned and folded "
            "sedimentary layers spanning over a billion years. The Uinta "
            "Crest Fault exposes Precambrian to Tertiary rocks. Excellent "
            "geological education site. Some rockhounding possible on "
            "adjacent BLM land."
        ),
        "watersheds": ["green_river"],
    },
    # -------------------------------------------------------------------------
    # Uinta Mountains / Uinta Basin
    # -------------------------------------------------------------------------
    {
        "name": "Uinta Mountains Quartzite and Minerals",
        "rock_type": "quartzite, jasper, smoky quartz crystals",
        "latitude": 40.7800,
        "longitude": -110.4000,
        "land_owner": "USFS (Ashley National Forest / Uinta-Wasatch-Cache NF)",
        "collecting_rules": (
            "Casual mineral collecting of reasonable amounts for personal "
            "use is generally allowed on National Forest land. No "
            "commercial collecting. Check with local ranger district. "
            "Wilderness areas have stricter rules — no mechanized tools."
        ),
        "nearest_town": "Vernal, UT",
        "description": (
            "The Uinta Mountains, the only major east-west trending range "
            "in the lower 48, are composed primarily of Precambrian "
            "quartzite (Uinta Mountain Group). Scattered quartz crystals, "
            "jasper, and other minerals in drainages. Alpine scenery and "
            "remote access. Best accessed July-September due to snow."
        ),
        "watersheds": ["green_river"],
    },
    # -------------------------------------------------------------------------
    # Dinosaur National Monument area
    # -------------------------------------------------------------------------
    {
        "name": "Dinosaur National Monument — Quarry Exhibit Hall",
        "rock_type": "Jurassic dinosaur bones, Morrison Formation (viewing only)",
        "latitude": 40.4383,
        "longitude": -109.3046,
        "land_owner": "NPS",
        "collecting_rules": (
            "NO COLLECTING. National monument — all fossil, mineral, and "
            "rock collecting is strictly prohibited by federal law (36 CFR "
            "2.1). Fines up to $5,000 and imprisonment. Viewing and "
            "photography only."
        ),
        "nearest_town": "Jensen, UT",
        "description": (
            "World-famous dinosaur quarry with over 1,500 Jurassic-age "
            "dinosaur bones exposed in a tilted sandstone wall inside the "
            "Quarry Exhibit Hall. Species include Allosaurus, Diplodocus, "
            "Stegosaurus, Camarasaurus, and others from the Morrison "
            "Formation (~149 million years old). The Green River flows "
            "through the monument. No collecting permitted."
        ),
        "watersheds": ["green_river"],
    },
    # -------------------------------------------------------------------------
    # Wyoming jade
    # -------------------------------------------------------------------------
    {
        "name": "Jade Collecting Areas (Wind River Range Foothills)",
        "rock_type": "nephrite jade, serpentine",
        "latitude": 42.5000,
        "longitude": -109.3000,
        "land_owner": "BLM / State",
        "collecting_rules": (
            "Surface collecting on BLM land is allowed under casual use "
            "rules. 25 lb/day limit. Wyoming jade is the state gemstone. "
            "Some areas are on state trust land — check with Wyoming State "
            "Lands for access. No collecting on private land without "
            "permission."
        ),
        "nearest_town": "Farson, WY",
        "description": (
            "Wyoming is famous for high-quality nephrite jade, and the "
            "Green River drainage west of South Pass has historically "
            "produced fine jade in dark green, olive, and black colors. "
            "Most surface jade has been collected, but small pieces can "
            "still be found. The area around Farson and the Wind River "
            "foothills is the classic jade country."
        ),
        "watersheds": ["green_river"],
    },
    {
        "name": "Eden Valley Petrified Wood",
        "rock_type": "petrified wood, agatized wood, jasper",
        "latitude": 42.0600,
        "longitude": -109.4100,
        "land_owner": "BLM",
        "collecting_rules": (
            "Free surface collecting on BLM land. 25 lb/day personal use "
            "limit. Hand tools only. No mechanized equipment."
        ),
        "nearest_town": "Farson, WY",
        "description": (
            "BLM land in the Eden Valley / Big Sandy area with scattered "
            "petrified wood and agate. Part of the larger Green River Basin "
            "collecting area. Less visited than Blue Forest but still "
            "productive for surface collecting. High-clearance vehicle "
            "recommended for side roads."
        ),
        "watersheds": ["green_river"],
    },
    # -------------------------------------------------------------------------
    # Topaz Mountain (nearby, popular destination)
    # -------------------------------------------------------------------------
    {
        "name": "Topaz Mountain",
        "rock_type": "topaz crystals, red beryl (rare), rhyolite",
        "latitude": 39.6840,
        "longitude": -113.1230,
        "land_owner": "BLM",
        "collecting_rules": (
            "Free collecting on BLM land. Surface collecting and hand "
            "digging allowed. No mechanized equipment. 25 lb/day limit. "
            "Popular site — best collecting requires digging in rhyolite "
            "cavities."
        ),
        "nearest_town": "Delta, UT",
        "description": (
            "Famous topaz collecting site in western Utah's Thomas Range. "
            "Amber-colored topaz crystals found in gas cavities in "
            "Tertiary rhyolite flows. While not in the Green River "
            "watershed, it is a popular destination for mineral collectors "
            "visiting the region. Best visited spring or fall — very hot "
            "in summer."
        ),
        "watersheds": [],
    },
    # -------------------------------------------------------------------------
    # Granger / Green River WY area
    # -------------------------------------------------------------------------
    {
        "name": "Granger Agate and Fossil Area",
        "rock_type": "agate, petrified wood, leaf fossils",
        "latitude": 41.5900,
        "longitude": -109.9600,
        "land_owner": "BLM",
        "collecting_rules": (
            "Free surface collecting on BLM land. 25 lb/day personal use "
            "limit. Check for active oil and gas leases — some areas may "
            "have restricted access."
        ),
        "nearest_town": "Granger, WY",
        "description": (
            "BLM land west of Green River, WY with scattered agate, "
            "petrified wood, and plant fossil impressions in Tertiary "
            "sediments. Relatively easy access from I-80. Good for casual "
            "collecting while passing through."
        ),
        "watersheds": ["green_river"],
    },
    {
        "name": "Delaney Rim Petrified Forest",
        "rock_type": "petrified wood, opalized wood",
        "latitude": 41.7000,
        "longitude": -108.3500,
        "land_owner": "BLM",
        "collecting_rules": (
            "Free surface collecting on BLM land. 25 lb/day personal use "
            "limit. Some areas have been designated as special management "
            "areas — check current BLM Rock Springs Field Office "
            "regulations. No commercial collecting."
        ),
        "nearest_town": "Rawlins, WY",
        "description": (
            "Large area of petrified wood in the Red Desert of Wyoming, "
            "including some opalized specimens. Scattered logs and fragments "
            "from Eocene forests. Remote area — high-clearance vehicle "
            "essential. Bring water, GPS, and spare tire. On the eastern "
            "edge of the Green River Basin."
        ),
        "watersheds": ["green_river"],
    },
    {
        "name": "Cedar Mountain Fossil Area",
        "rock_type": "Cretaceous fossils, petrified wood, agate",
        "latitude": 39.2500,
        "longitude": -110.2500,
        "land_owner": "BLM",
        "collecting_rules": (
            "Surface collecting of common invertebrate fossils and "
            "reasonable amounts of petrified wood on BLM land. Vertebrate "
            "fossils are protected under PRPA. Check with BLM Price Field "
            "Office for current rules."
        ),
        "nearest_town": "Green River, UT",
        "description": (
            "BLM land near the town of Green River, UT with Cedar Mountain "
            "Formation and Morrison Formation exposures. Petrified wood, "
            "agate, and invertebrate fossils. The area is also known for "
            "important dinosaur fossil discoveries (professional sites — "
            "do not disturb). Casual rockhounding for non-vertebrate "
            "material is permitted."
        ),
        "watersheds": ["green_river"],
    },
]


# =============================================================================
# 4. HATCH_CHART — Monthly insect emergence, Green River below Flaming Gorge
# =============================================================================

HATCH_CHART = [
    # =========================================================================
    # JANUARY
    # =========================================================================
    {
        "watershed": "green_river",
        "month": 1,
        "insect_order": "Diptera",
        "family": "Chironomidae",
        "common_name": "Midges",
        "scientific_name": "Chironomidae spp.",
        "life_stage": "larva/pupa",
        "activity_level": "high",
        "fly_pattern": "Zebra Midge, Juju Bee, Mercury Midge",
        "fly_size": "18-24",
        "notes": (
            "Primary food source in winter. Fish subsurface midge clusters "
            "in slow runs and eddies. Size 20-22 most productive. Morning "
            "emergence can bring fish to the surface on warm days."
        ),
    },
    {
        "watershed": "green_river",
        "month": 1,
        "insect_order": "Amphipoda",
        "family": "Gammaridae",
        "common_name": "Scuds",
        "scientific_name": "Gammarus lacustris",
        "life_stage": "nymph",
        "activity_level": "high",
        "fly_pattern": "Ray Charles Scud, Orange Scud, Sow Bug",
        "fly_size": "14-18",
        "notes": (
            "Year-round food source. The Green River has enormous scud "
            "populations. Dead-drift along the bottom in riffles and runs. "
            "Orange and pink colors imitate dead/drifting scuds."
        ),
    },
    # =========================================================================
    # FEBRUARY
    # =========================================================================
    {
        "watershed": "green_river",
        "month": 2,
        "insect_order": "Diptera",
        "family": "Chironomidae",
        "common_name": "Midges",
        "scientific_name": "Chironomidae spp.",
        "life_stage": "larva/pupa",
        "activity_level": "high",
        "fly_pattern": "Zebra Midge, Top Secret Midge, Disco Midge",
        "fly_size": "18-24",
        "notes": (
            "Peak winter midge activity. Cluster midges can produce "
            "excellent dry fly fishing on calm afternoons. Look for rising "
            "fish in slower water along banks and in eddies."
        ),
    },
    {
        "watershed": "green_river",
        "month": 2,
        "insect_order": "Amphipoda",
        "family": "Gammaridae",
        "common_name": "Scuds",
        "scientific_name": "Gammarus lacustris",
        "life_stage": "nymph",
        "activity_level": "high",
        "fly_pattern": "Pink Scud, Sow Bug, Ray Charles",
        "fly_size": "14-18",
        "notes": (
            "Scuds remain a primary food source. Trout actively feed on "
            "drifting scuds. Trail a scud behind a midge in a two-fly rig."
        ),
    },
    # =========================================================================
    # MARCH
    # =========================================================================
    {
        "watershed": "green_river",
        "month": 3,
        "insect_order": "Diptera",
        "family": "Chironomidae",
        "common_name": "Midges",
        "scientific_name": "Chironomidae spp.",
        "life_stage": "adult",
        "activity_level": "high",
        "fly_pattern": "Griffith's Gnat, Palomino Midge, Adams",
        "fly_size": "18-22",
        "notes": (
            "Strong midge hatches continue. Adult clusters on the surface "
            "draw aggressive feeding. Griffith's Gnat imitates midge "
            "clusters effectively."
        ),
    },
    {
        "watershed": "green_river",
        "month": 3,
        "insect_order": "Ephemeroptera",
        "family": "Baetidae",
        "common_name": "Blue-Winged Olives (BWO)",
        "scientific_name": "Baetis tricaudatus",
        "life_stage": "nymph/emerger",
        "activity_level": "medium",
        "fly_pattern": "Pheasant Tail, RS2, Flashback BWO",
        "fly_size": "18-22",
        "notes": (
            "Early BWO activity begins in March. Nymphs become active "
            "before full emergence starts. Overcast days produce the best "
            "hatches. Fish emerger patterns in film on cloudy afternoons."
        ),
    },
    # =========================================================================
    # APRIL
    # =========================================================================
    {
        "watershed": "green_river",
        "month": 4,
        "insect_order": "Ephemeroptera",
        "family": "Baetidae",
        "common_name": "Blue-Winged Olives (BWO)",
        "scientific_name": "Baetis tricaudatus",
        "life_stage": "adult",
        "activity_level": "high",
        "fly_pattern": "Parachute BWO, Sparkle Dun, Comparadun",
        "fly_size": "18-22",
        "notes": (
            "Peak spring BWO hatch. Cloudy, drizzly days produce blanket "
            "hatches with fish rising everywhere. Size 20 is the most "
            "productive. One of the best dry fly months on the Green."
        ),
    },
    {
        "watershed": "green_river",
        "month": 4,
        "insect_order": "Ephemeroptera",
        "family": "Ephemerellidae",
        "common_name": "Red Quills",
        "scientific_name": "Ephemerella spp.",
        "life_stage": "nymph/emerger",
        "activity_level": "medium",
        "fly_pattern": "Pheasant Tail, Hare's Ear, Red Quill Nymph",
        "fly_size": "14-16",
        "notes": (
            "Red quill nymphs become active in April. Pre-emergence "
            "nymphing can be very productive. Larger profile than BWOs — "
            "trout key on them eagerly."
        ),
    },
    {
        "watershed": "green_river",
        "month": 4,
        "insect_order": "Diptera",
        "family": "Chironomidae",
        "common_name": "Midges",
        "scientific_name": "Chironomidae spp.",
        "life_stage": "adult",
        "activity_level": "medium",
        "fly_pattern": "Griffith's Gnat, Parachute Midge",
        "fly_size": "20-24",
        "notes": (
            "Midge activity continues but is overshadowed by BWO hatches. "
            "Still a reliable fallback pattern, especially in morning hours."
        ),
    },
    # =========================================================================
    # MAY
    # =========================================================================
    {
        "watershed": "green_river",
        "month": 5,
        "insect_order": "Ephemeroptera",
        "family": "Baetidae",
        "common_name": "Blue-Winged Olives (BWO)",
        "scientific_name": "Baetis tricaudatus",
        "life_stage": "adult",
        "activity_level": "high",
        "fly_pattern": "Parachute BWO, CDC BWO, Vis-A-Dun",
        "fly_size": "18-22",
        "notes": (
            "Spring BWO hatch continues strong through May. Afternoon "
            "hatches on overcast days remain excellent. Spinner falls in "
            "the evening provide additional dry fly opportunities."
        ),
    },
    {
        "watershed": "green_river",
        "month": 5,
        "insect_order": "Ephemeroptera",
        "family": "Ephemerellidae",
        "common_name": "Red Quills",
        "scientific_name": "Ephemerella spp.",
        "life_stage": "adult",
        "activity_level": "medium",
        "fly_pattern": "Red Quill Dry, Quill Gordon, Parachute Hare's Ear",
        "fly_size": "14-16",
        "notes": (
            "Red quill adults emerge in May. Slightly larger than BWOs, "
            "these reddish-brown mayflies bring up bigger fish. Fish in "
            "riffles and runs during afternoon emergence."
        ),
    },
    {
        "watershed": "green_river",
        "month": 5,
        "insect_order": "Trichoptera",
        "family": "Various",
        "common_name": "Caddis",
        "scientific_name": "Brachycentrus spp., Hydropsyche spp.",
        "life_stage": "pupa/emerger",
        "activity_level": "medium",
        "fly_pattern": "Elk Hair Caddis, Soft Hackle, LaFontaine Sparkle Pupa",
        "fly_size": "14-18",
        "notes": (
            "Caddis activity begins in May. Pupae rising to the surface "
            "trigger aggressive feeding. Soft hackle wet flies swung through "
            "runs are very effective during emergence."
        ),
    },
    # =========================================================================
    # JUNE
    # =========================================================================
    {
        "watershed": "green_river",
        "month": 6,
        "insect_order": "Ephemeroptera",
        "family": "Ephemerellidae",
        "common_name": "Pale Morning Duns (PMD)",
        "scientific_name": "Ephemerella infrequens",
        "life_stage": "adult",
        "activity_level": "high",
        "fly_pattern": "Parachute PMD, Sparkle Dun PMD, PMD Cripple",
        "fly_size": "16-18",
        "notes": (
            "The PMD hatch begins in June and is one of the Green River's "
            "most important hatches. Dense afternoon emergences on the A "
            "and B sections. Fish become very selective — match size and "
            "color precisely. Cripple patterns are deadly."
        ),
    },
    {
        "watershed": "green_river",
        "month": 6,
        "insect_order": "Trichoptera",
        "family": "Various",
        "common_name": "Caddis",
        "scientific_name": "Brachycentrus spp., Hydropsyche spp.",
        "life_stage": "adult",
        "activity_level": "high",
        "fly_pattern": "Elk Hair Caddis, Goddard Caddis, X-Caddis",
        "fly_size": "14-18",
        "notes": (
            "Peak caddis activity in June. Evening egg-laying flights "
            "produce excellent dry fly fishing. Skittering an Elk Hair "
            "Caddis across the surface can draw explosive strikes."
        ),
    },
    {
        "watershed": "green_river",
        "month": 6,
        "insect_order": "Plecoptera",
        "family": "Perlodidae",
        "common_name": "Yellow Sallies",
        "scientific_name": "Isoperla spp.",
        "life_stage": "adult",
        "activity_level": "medium",
        "fly_pattern": "Yellow Sally, Yellow Stimulator, Yellow Humpy",
        "fly_size": "14-16",
        "notes": (
            "Small yellow stoneflies emerge in June. Not as dense as "
            "mayfly hatches but trout eat them readily. Fish along banks "
            "and riffles where stoneflies crawl out to emerge."
        ),
    },
    {
        "watershed": "green_river",
        "month": 6,
        "insect_order": "Ephemeroptera",
        "family": "Ephemeridae",
        "common_name": "Green Drakes",
        "scientific_name": "Drunella grandis",
        "life_stage": "nymph/emerger",
        "activity_level": "low",
        "fly_pattern": "Green Drake Nymph, Hare's Ear (olive)",
        "fly_size": "10-12",
        "notes": (
            "Green drake nymphs become active in late June. The full "
            "hatch peaks in July, but early activity can produce good "
            "nymphing. These are the largest mayflies on the Green River."
        ),
    },
    # =========================================================================
    # JULY
    # =========================================================================
    {
        "watershed": "green_river",
        "month": 7,
        "insect_order": "Ephemeroptera",
        "family": "Ephemerellidae",
        "common_name": "Pale Morning Duns (PMD)",
        "scientific_name": "Ephemerella infrequens",
        "life_stage": "adult/spinner",
        "activity_level": "high",
        "fly_pattern": "PMD Spinner, Rusty Spinner, PMD Cripple",
        "fly_size": "16-18",
        "notes": (
            "PMD hatch remains strong through July. Spinner falls in the "
            "evening can be phenomenal. Rusty spinner patterns in size 16 "
            "fished flush in the film are essential."
        ),
    },
    {
        "watershed": "green_river",
        "month": 7,
        "insect_order": "Hemiptera",
        "family": "Cicadidae",
        "common_name": "Cicadas",
        "scientific_name": "Platypedia spp.",
        "life_stage": "adult",
        "activity_level": "high",
        "fly_pattern": "Rainy's Cicada, Morrish Cicada, Club Sandwich",
        "fly_size": "6-10",
        "notes": (
            "The famous Green River cicada hatch. Large cicadas fall into "
            "the river from bankside vegetation, triggering explosive "
            "surface strikes from the largest trout. Fish tight to "
            "overhanging willows and cottonwoods. One of the most exciting "
            "dry fly experiences in the West. Peak late June through July."
        ),
    },
    {
        "watershed": "green_river",
        "month": 7,
        "insect_order": "Ephemeroptera",
        "family": "Ephemeridae",
        "common_name": "Green Drakes",
        "scientific_name": "Drunella grandis",
        "life_stage": "adult",
        "activity_level": "medium",
        "fly_pattern": "Parachute Green Drake, Extended Body Drake, Comparadun",
        "fly_size": "10-12",
        "notes": (
            "Green drake emergence in July. These large, dark-bodied "
            "mayflies bring up the biggest fish. Hatches are sporadic and "
            "localized — when you find them, the fishing is outstanding. "
            "Best on overcast afternoons."
        ),
    },
    {
        "watershed": "green_river",
        "month": 7,
        "insect_order": "Trichoptera",
        "family": "Various",
        "common_name": "Caddis",
        "scientific_name": "Brachycentrus spp.",
        "life_stage": "adult",
        "activity_level": "medium",
        "fly_pattern": "Elk Hair Caddis, Henryville Special",
        "fly_size": "14-18",
        "notes": (
            "Caddis remain active through July. Evening flights continue "
            "to provide dry fly opportunities. Effective as a searching "
            "pattern between mayfly hatches."
        ),
    },
    {
        "watershed": "green_river",
        "month": 7,
        "insect_order": "Orthoptera",
        "family": "Acrididae",
        "common_name": "Grasshoppers",
        "scientific_name": "Various spp.",
        "life_stage": "adult",
        "activity_level": "medium",
        "fly_pattern": "Chernobyl Ant, Dave's Hopper, Parachute Hopper",
        "fly_size": "8-12",
        "notes": (
            "Hopper fishing begins in July as grasshoppers mature in "
            "bankside meadows. Fish tight to grassy banks, especially on "
            "windy afternoons when hoppers get blown into the water. "
            "Hopper-dropper rigs are very productive."
        ),
    },
    {
        "watershed": "green_river",
        "month": 7,
        "insect_order": "Plecoptera",
        "family": "Perlodidae",
        "common_name": "Yellow Sallies",
        "scientific_name": "Isoperla spp.",
        "life_stage": "adult",
        "activity_level": "medium",
        "fly_pattern": "Yellow Sally, Yellow Stimulator",
        "fly_size": "14-16",
        "notes": (
            "Yellow sally emergence continues into July. Good searching "
            "pattern fished along banks and in riffles."
        ),
    },
    # =========================================================================
    # AUGUST
    # =========================================================================
    {
        "watershed": "green_river",
        "month": 8,
        "insect_order": "Ephemeroptera",
        "family": "Ephemerellidae",
        "common_name": "Pale Morning Duns (PMD)",
        "scientific_name": "Ephemerella infrequens",
        "life_stage": "adult/spinner",
        "activity_level": "medium",
        "fly_pattern": "Parachute PMD, PMD Spinner, Rusty Spinner",
        "fly_size": "16-20",
        "notes": (
            "Late-season PMDs continue but hatches thin out in August. "
            "Smaller sizes (18-20) become more productive as the hatch "
            "wanes. Spinner falls remain good in the evening."
        ),
    },
    {
        "watershed": "green_river",
        "month": 8,
        "insect_order": "Orthoptera",
        "family": "Acrididae",
        "common_name": "Grasshoppers",
        "scientific_name": "Various spp.",
        "life_stage": "adult",
        "activity_level": "high",
        "fly_pattern": "Chernobyl Ant, Morrish Hopper, Parachute Hopper",
        "fly_size": "8-12",
        "notes": (
            "Peak hopper season. August is prime time for terrestrial "
            "fishing on the Green. Windy afternoons produce the best "
            "action. Hopper-dropper with a Pheasant Tail or scud below "
            "is a deadly combo."
        ),
    },
    {
        "watershed": "green_river",
        "month": 8,
        "insect_order": "Hymenoptera",
        "family": "Formicidae",
        "common_name": "Ants",
        "scientific_name": "Various spp.",
        "life_stage": "adult",
        "activity_level": "medium",
        "fly_pattern": "Fur Ant, Parachute Ant, Cinnamon Ant",
        "fly_size": "14-18",
        "notes": (
            "Flying ant falls can produce excellent fishing in August. "
            "When ants are on the water, trout feed on them selectively. "
            "Small black or cinnamon ant patterns are effective."
        ),
    },
    {
        "watershed": "green_river",
        "month": 8,
        "insect_order": "Coleoptera",
        "family": "Various",
        "common_name": "Beetles",
        "scientific_name": "Various spp.",
        "life_stage": "adult",
        "activity_level": "medium",
        "fly_pattern": "Foam Beetle, Hi-Vis Beetle",
        "fly_size": "14-18",
        "notes": (
            "Beetles are a consistent terrestrial food source in August. "
            "Small foam beetle patterns fished along overhanging vegetation "
            "produce steady takes."
        ),
    },
    {
        "watershed": "green_river",
        "month": 8,
        "insect_order": "Trichoptera",
        "family": "Various",
        "common_name": "Caddis",
        "scientific_name": "Hydropsyche spp.",
        "life_stage": "adult",
        "activity_level": "medium",
        "fly_pattern": "Elk Hair Caddis, X-Caddis",
        "fly_size": "14-18",
        "notes": (
            "Late-season caddis remain active, particularly in the evening. "
            "Good option when terrestrial activity is slow."
        ),
    },
    # =========================================================================
    # SEPTEMBER
    # =========================================================================
    {
        "watershed": "green_river",
        "month": 9,
        "insect_order": "Ephemeroptera",
        "family": "Baetidae",
        "common_name": "Blue-Winged Olives (BWO)",
        "scientific_name": "Baetis tricaudatus",
        "life_stage": "adult",
        "activity_level": "high",
        "fly_pattern": "Parachute BWO, CDC BWO, Sparkle Dun",
        "fly_size": "18-22",
        "notes": (
            "Fall BWO hatch begins in September. As weather cools and "
            "days shorten, Baetis return in force. Overcast afternoons "
            "produce the best hatches. One of the premier fall dry fly "
            "periods on the Green."
        ),
    },
    {
        "watershed": "green_river",
        "month": 9,
        "insect_order": "Orthoptera",
        "family": "Acrididae",
        "common_name": "Grasshoppers",
        "scientific_name": "Various spp.",
        "life_stage": "adult",
        "activity_level": "medium",
        "fly_pattern": "Chernobyl Ant, Dave's Hopper",
        "fly_size": "8-12",
        "notes": (
            "Hopper fishing continues into September, especially in the "
            "first half of the month. Mornings may be too cool — best "
            "action midday to afternoon when hoppers are active."
        ),
    },
    {
        "watershed": "green_river",
        "month": 9,
        "insect_order": "Trichoptera",
        "family": "Various",
        "common_name": "Caddis",
        "scientific_name": "Various spp.",
        "life_stage": "adult",
        "activity_level": "low",
        "fly_pattern": "Elk Hair Caddis, October Caddis",
        "fly_size": "12-16",
        "notes": (
            "Late-season caddis including larger October caddis species. "
            "Fish see fewer caddis and can be less wary of larger patterns."
        ),
    },
    {
        "watershed": "green_river",
        "month": 9,
        "insect_order": "Amphipoda",
        "family": "Gammaridae",
        "common_name": "Scuds",
        "scientific_name": "Gammarus lacustris",
        "life_stage": "nymph",
        "activity_level": "high",
        "fly_pattern": "Ray Charles Scud, Orange Scud",
        "fly_size": "14-18",
        "notes": (
            "As hatches transition from summer to fall, scud patterns "
            "become increasingly reliable. Dead-drift in runs and "
            "riffles below weed beds."
        ),
    },
    # =========================================================================
    # OCTOBER
    # =========================================================================
    {
        "watershed": "green_river",
        "month": 10,
        "insect_order": "Ephemeroptera",
        "family": "Baetidae",
        "common_name": "Blue-Winged Olives (BWO)",
        "scientific_name": "Baetis tricaudatus",
        "life_stage": "adult",
        "activity_level": "high",
        "fly_pattern": "Parachute BWO, RS2, CDC BWO Emerger",
        "fly_size": "20-24",
        "notes": (
            "Peak fall BWO fishing. October often produces the densest "
            "BWO hatches of the year. Fish can be extremely selective — "
            "size down to 22-24 if refusals persist. Overcast, drizzly "
            "days are magical."
        ),
    },
    {
        "watershed": "green_river",
        "month": 10,
        "insect_order": "Diptera",
        "family": "Chironomidae",
        "common_name": "Midges",
        "scientific_name": "Chironomidae spp.",
        "life_stage": "pupa",
        "activity_level": "medium",
        "fly_pattern": "Zebra Midge, Mercury Midge, Thread Midge",
        "fly_size": "20-24",
        "notes": (
            "Midge activity picks up as temperatures cool. Fish midge "
            "pupae below BWO dries in a dry-dropper setup."
        ),
    },
    {
        "watershed": "green_river",
        "month": 10,
        "insect_order": "Amphipoda",
        "family": "Gammaridae",
        "common_name": "Scuds",
        "scientific_name": "Gammarus lacustris",
        "life_stage": "nymph",
        "activity_level": "high",
        "fly_pattern": "Pink Scud, Sow Bug, Ray Charles",
        "fly_size": "14-18",
        "notes": (
            "Excellent scud fishing in October. Brown trout become "
            "aggressive pre-spawn, feeding heavily on scuds to build "
            "energy reserves."
        ),
    },
    # =========================================================================
    # NOVEMBER
    # =========================================================================
    {
        "watershed": "green_river",
        "month": 11,
        "insect_order": "Ephemeroptera",
        "family": "Baetidae",
        "common_name": "Blue-Winged Olives (BWO)",
        "scientific_name": "Baetis tricaudatus",
        "life_stage": "adult",
        "activity_level": "medium",
        "fly_pattern": "Parachute BWO, Comparadun, CDC Emerger",
        "fly_size": "20-24",
        "notes": (
            "Late fall BWOs continue into November. Shorter hatching "
            "windows (often just 1-2 hours midday) but can still produce "
            "excellent fishing when conditions align. Dress warm."
        ),
    },
    {
        "watershed": "green_river",
        "month": 11,
        "insect_order": "Diptera",
        "family": "Chironomidae",
        "common_name": "Midges",
        "scientific_name": "Chironomidae spp.",
        "life_stage": "larva/pupa",
        "activity_level": "high",
        "fly_pattern": "Zebra Midge, Juju Bee, Black Beauty",
        "fly_size": "18-24",
        "notes": (
            "Midges become the dominant food source again as fall "
            "transitions to winter. Subsurface midge fishing in slow "
            "water is consistently productive."
        ),
    },
    {
        "watershed": "green_river",
        "month": 11,
        "insect_order": "Amphipoda",
        "family": "Gammaridae",
        "common_name": "Scuds",
        "scientific_name": "Gammarus lacustris",
        "life_stage": "nymph",
        "activity_level": "high",
        "fly_pattern": "Orange Scud, Sow Bug, Ray Charles Scud",
        "fly_size": "14-18",
        "notes": (
            "Scud and sow bug patterns are reliable throughout November. "
            "Brown trout may be on spawning redds — avoid wading through "
            "gravel beds with visible redds."
        ),
    },
    # =========================================================================
    # DECEMBER
    # =========================================================================
    {
        "watershed": "green_river",
        "month": 12,
        "insect_order": "Diptera",
        "family": "Chironomidae",
        "common_name": "Midges",
        "scientific_name": "Chironomidae spp.",
        "life_stage": "larva/pupa",
        "activity_level": "high",
        "fly_pattern": "Zebra Midge, Top Secret Midge, Mercury Midge",
        "fly_size": "18-24",
        "notes": (
            "Winter midge fishing on the Green is world-class. The "
            "tailwater stays open and fishable year-round thanks to "
            "consistent dam releases. Focus on slow runs and eddies. "
            "Afternoon midge emergences on sunny days can produce "
            "surface feeding."
        ),
    },
    {
        "watershed": "green_river",
        "month": 12,
        "insect_order": "Amphipoda",
        "family": "Gammaridae",
        "common_name": "Scuds",
        "scientific_name": "Gammarus lacustris",
        "life_stage": "nymph",
        "activity_level": "high",
        "fly_pattern": "Pink Scud, Orange Scud, Sow Bug",
        "fly_size": "14-18",
        "notes": (
            "Scuds and sow bugs remain the subsurface staple in winter. "
            "Double-nymph rigs with a midge and scud cover both primary "
            "food sources. Fish the A section for consistent winter "
            "access and productive water."
        ),
    },
]
