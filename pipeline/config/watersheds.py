"""Watershed configurations.

Each watershed defines a bounding box and metadata used by ingestion adapters.
Bounding boxes are designed to capture the full drainage — main stem, major
tributaries, headwater lakes, and the river's mouth where applicable — with a
small buffer beyond the most-extreme reach centroid.

Updated 2026-05-14: expanded several bboxes after auditing reach centroids
and curated stocking entries against the prior values. See
plan-2026-05-14-tqs-forecast-history.md for context.
"""

WATERSHEDS = {
    "klamath": {
        "name": "Upper Klamath Basin",
        "description": (
            "Upper Klamath Lake, Williamson River, Sprague River, "
            "and Agency Lake in southern Oregon"
        ),
        # Expanded west to cover Lake of the Woods and Fourmile Lk; east to
        # cover Sprague R tributaries; south for a small buffer.
        "bbox": {
            "north": 43.20,
            "south": 42.10,
            "east": -120.70,
            "west": -122.30,
        },
    },
    "mckenzie": {
        "name": "McKenzie River",
        "description": (
            "McKenzie River watershed from headwaters to confluence "
            "with Willamette, including Blue River and South Fork"
        ),
        # Expanded west to cover the Willamette confluence; north for a
        # small buffer past Clear Lake.
        "bbox": {
            "north": 44.45,
            "south": 43.85,
            "east": -121.70,
            "west": -123.10,
        },
    },
    "deschutes": {
        "name": "Deschutes River",
        "description": (
            "Deschutes River from Wickiup Reservoir and the upper Cascade "
            "headwaters through Bend and Madras to Sherars Falls and the "
            "Columbia confluence — full main stem plus Crooked River and "
            "Tumalo Creek tributaries."
        ),
        # Significant expansion: north to Columbia mouth (~45.62°N), south
        # to Davis Lake / Wickiup, east to upper Crooked R basin, west to
        # full Cascades headwaters.
        "bbox": {
            "north": 45.70,
            "south": 43.55,
            "east": -120.30,
            "west": -121.95,
        },
    },
    "metolius": {
        "name": "Metolius River",
        "description": (
            "Metolius River basin near Sisters, Oregon, from headwaters "
            "to Lake Billy Chinook including Lake Creek and Spring Creek"
        ),
        # Expanded north to cover Lake Billy Chinook (where Metolius drains
        # in) and Olallie Lk; minor west/east buffers.
        "bbox": {
            "north": 44.85,
            "south": 44.30,
            "east": -121.30,
            "west": -121.90,
        },
    },
    "johnday": {
        "name": "John Day River",
        "description": (
            "John Day River basin in central-eastern Oregon, from Prairie City "
            "through Picture Gorge and Service Creek to the Columbia confluence "
            "near The Dalles. 284 miles of undammed mainstem — Wild & Scenic, "
            "rangeland ecology, fossil beds, steelhead and Chinook habitat."
        ),
        # Significant westward expansion to cover Service Creek and the
        # lower mainstem all the way to the Columbia mouth.
        "bbox": {
            "north": 45.80,
            "south": 44.10,
            "east": -118.30,
            "west": -120.80,
        },
    },
    "skagit": {
        "name": "Skagit River",
        "description": (
            "Skagit River watershed in northwest Washington, from North Cascades "
            "through Skagit Valley to Puget Sound. Largest river system in the "
            "Puget Sound basin — all five Pacific salmon species, bald eagle "
            "wintering grounds, and critical estuary habitat."
        ),
        # Expanded south to cover Snohomish-county stocking surfaces that
        # appear on this watershed's stocking section (Lk Loma, Silver Lk
        # SNOH, Chain Lk SNOH). This is wider than the strict Skagit
        # drainage; documented as a deliberate product choice.
        "bbox": {
            "north": 48.95,
            "south": 47.75,
            "east": -120.95,
            "west": -122.65,
        },
    },
    "green_river": {
        "name": "Green River",
        "description": (
            "Green River from Wind River Range headwaters (WY) through "
            "Flaming Gorge, Dinosaur National Monument, Desolation Canyon, "
            "to confluence with Colorado River in Canyonlands (UT). "
            "Endangered Colorado pikeminnow and razorback sucker habitat, "
            "world-famous Green River Formation fossil fish, major "
            "recreation destination."
        ),
        # Expanded east to cover Lodore Canyon reach centroid (-108.95).
        "bbox": {
            "north": 43.50,
            "south": 38.10,
            "east": -108.75,
            "west": -111.50,
        },
    },
    "shenandoah": {
        "name": "Shenandoah River",
        "description": (
            "Shenandoah River from North Fork (Bergton, VA) and South "
            "Fork (Sherando, VA) headwaters in the Blue Ridge / Allegheny "
            "foothills, through the Shenandoah Valley between the Blue "
            "Ridge and Massanutten Mountain, to confluence with the "
            "Potomac River at Harpers Ferry, WV. First Atlantic-slope "
            "watershed on the platform. Smallmouth bass dominant on the "
            "warm-water main stem; wild brook trout in cold Blue Ridge "
            "tributaries; brown trout in limestone-spring streams "
            "(Mossy Creek, Beaver Creek)."
        ),
        # HUC8s 02070005 (South Fork), 02070006 (North Fork), 02070007
        # (main stem) + 0.05° buffer. North bound clears the Potomac
        # confluence at Harpers Ferry; south bound covers Augusta County
        # headwater springs.
        "bbox": {
            "north": 39.35,
            "south": 37.70,
            "east": -77.65,
            "west": -79.40,
        },
    },
}
