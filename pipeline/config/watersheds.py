"""Watershed configurations for Pacific Northwest watersheds.

Each watershed defines a bounding box and metadata used by ingestion adapters.
Bounding boxes are approximate and designed to capture the main stem and
major tributaries of each system.
"""

WATERSHEDS = {
    "klamath": {
        "name": "Upper Klamath Basin",
        "description": (
            "Upper Klamath Lake, Williamson River, Sprague River, "
            "and Agency Lake in southern Oregon"
        ),
        "bbox": {
            "north": 43.10,
            "south": 42.20,
            "east": -121.00,
            "west": -122.10,
        },
    },
    "mckenzie": {
        "name": "McKenzie River",
        "description": (
            "McKenzie River watershed from headwaters to confluence "
            "with Willamette, including Blue River and South Fork"
        ),
        "bbox": {
            "north": 44.30,
            "south": 43.85,
            "east": -121.70,
            "west": -122.90,
        },
    },
    "deschutes": {
        "name": "Deschutes River",
        "description": (
            "Deschutes River from Bend through Madras to Lower Deschutes, "
            "including Crooked River and Tumalo Creek"
        ),
        "bbox": {
            "north": 44.80,
            "south": 43.85,
            "east": -120.60,
            "west": -121.85,
        },
    },
    "metolius": {
        "name": "Metolius River",
        "description": (
            "Metolius River basin near Sisters, Oregon, from headwaters "
            "to Lake Billy Chinook including Lake Creek and Spring Creek"
        ),
        "bbox": {
            "north": 44.65,
            "south": 44.35,
            "east": -121.35,
            "west": -121.80,
        },
    },
    "johnday": {
        "name": "John Day River",
        "description": (
            "John Day River basin in central-eastern Oregon, from Prairie City "
            "through Picture Gorge to the Columbia. Wild & Scenic, rangeland "
            "ecology, fossil beds, steelhead and Chinook habitat."
        ),
        "bbox": {
            "north": 45.05,
            "south": 44.15,
            "east": -118.40,
            "west": -119.90,
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
        "bbox": {
            "north": 48.90,
            "south": 48.20,
            "east": -121.00,
            "west": -122.60,
        },
    },
}
