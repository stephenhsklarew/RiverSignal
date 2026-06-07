"""seed fly_tying_videos for marquee Meramec/Chattahoochee hatch patterns

Revision ID: nc13a1b2c3d4
Revises: nb12a1b2c3d4
Create Date: 2026-06-07 00:00:00.000000

The "Tie it" link uses a curated fly_tying_videos row when the fly name matches,
else a YouTube-search fallback (_enrich_patterns). This seeds specific,
hand-picked tutorials for the signature Ozark-smallmouth + Eastern-trout
patterns so those get a real video instead of a search. fly_pattern matches the
curated_hatch_chart.fly_patterns names exactly (case-insensitive lookup).
Videos sourced 2026-06-07 from established tying channels (Tightline Productions
/ Tim Flagler, Holsinger's, Trident). Idempotent (NOT EXISTS by fly_pattern).
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'nc13a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'nb12a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (fly_pattern, video_title, youtube_url)
VIDEOS = [
    ('Clouser Crayfish', 'Tying the Clouser Crayfish (Tightline Productions)',
     'https://www.youtube.com/watch?v=PFh8kEvqgCk'),
    ('Clouser Minnow', 'Tying the Clouser Minnow (Tightline Productions)',
     'https://www.youtube.com/watch?v=BtIZN5Low9Q'),
    ('Black Wooly Bugger', 'Building a Better Woolly Bugger (Tightline Productions)',
     'https://www.youtube.com/watch?v=dwUWGMuHkWE'),
    ('Olive Wooly Bugger', 'Building a Better Woolly Bugger (Tightline Productions)',
     'https://www.youtube.com/watch?v=dwUWGMuHkWE'),
    ('Hellgrammite Pattern', 'Hellgrammite Fly Pattern — Fly Tying Tutorial',
     'https://www.youtube.com/watch?v=RUcTfgaHQHs'),
    ('Prince Nymph', 'Prince Nymph Fly Pattern — Tying Tutorial (Trident)',
     'https://www.youtube.com/watch?v=SN1oA6FWtHQ'),
    ('Isonychia Nymph', 'Slate Drake (Isonychia) Nymph — Fly Tying',
     'https://www.youtube.com/watch?v=Mq_NON0U8OI'),
    ('Hendrickson Dry', 'Catskill-Style Hendrickson Dry (Tightline Productions)',
     'https://www.youtube.com/watch?v=nRjmHzmvFKQ'),
    ('Sulphur Parachute', 'Tying the Sulphur Parachute (Tightline Productions)',
     'https://www.youtube.com/watch?v=ob-m5XXhdJY'),
    ('Sulphur Sparkle Dun', 'Tying the Sulphur Comparadun (Tightline Productions)',
     'https://www.youtube.com/watch?v=Gp4rV1PYPHM'),
    ('Chernobyl Ant', 'Tying the Chernobyl Ant (Tightline Productions)',
     'https://www.youtube.com/watch?v=oK167pJZF1I'),
]


def upgrade() -> None:
    conn = op.get_bind()
    for fly_pattern, title, url in VIDEOS:
        conn.execute(
            text("""
                INSERT INTO fly_tying_videos (fly_pattern, video_title, youtube_url, source)
                SELECT CAST(:fp AS varchar), CAST(:title AS varchar), CAST(:url AS varchar),
                       'curated marquee 2026-06-07'
                WHERE NOT EXISTS (
                    SELECT 1 FROM fly_tying_videos WHERE lower(fly_pattern) = lower(CAST(:fp AS varchar))
                )
            """),
            {"fp": fly_pattern, "title": title, "url": url},
        )


def downgrade() -> None:
    op.execute("DELETE FROM fly_tying_videos WHERE source = 'curated marquee 2026-06-07'")
