"""seed silver.insect_fly_patterns with East Coast / Mid-Atlantic hatches

Revision ID: ss19n0o1p2q3
Revises: rr18m9n0o1p2
Create Date: 2026-05-16 00:00:00.000000

`silver.insect_fly_patterns` was originally seeded with West-Coast hatches
(Pale Morning Dun, Salmonfly, October Caddis, etc). The fly-recommendations
endpoint (gold.hatch_fly_recommendations → /sites/<ws>/fishing/fly-
recommendations) joins curated_hatch_chart entries to this table by
insect_common_name. For Shenandoah's 10 curated hatches, only ~4 matched
(Blue-winged Olive, Midges, Grannom = generic caddis, Little Yellow
Stonefly). The other 6 — Quill Gordon, Hendrickson, Sulphur, Light Cahill,
Trico, Hellgrammite, Little Black Stonefly — had no fly patterns, so the
"Flies to Tie" surface on /path/hatch/<ws> rendered empty for those
months.

This migration adds canonical fly patterns for those 6 hatches plus a
couple extra Mid-Atlantic standards. Patterns sourced from Orvis Fly Box,
Catskill regional guides (Beaverkill, Schoharie), and Trout Unlimited's
hatch-matching primers. Sizes follow standard Catskill/Cumberland
practice. Each pattern has an image_url pointing at the existing
/images/flies/*.jpg assets the West Coast rows already use, falling back
to the most-visually-similar pattern when no East Coast asset exists.

Idempotent — INSERTs are guarded by NOT EXISTS on
(insect_common_name, fly_pattern_name, life_stage).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'tt20o1p2q3r4'
down_revision: Union[str, Sequence[str], None] = 'ss19n0o1p2q3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (insect_common_name, insect_order, insect_genus,
#  fly_pattern_name, fly_size, fly_type, life_stage,
#  season_start, season_end, fly_image_url, notes)
ROWS = [
    # ── Quill Gordon (Epeorus pleuralis) — early-season Mid-Atlantic mayfly ──
    ('Quill Gordon', 'Ephemeroptera', 'Epeorus',
     'Quill Gordon Dry', '#12-14', 'dry fly', 'adult',
     3, 4, '/images/flies/parachute-adams.jpg',
     'Catskill-style dry; fish midday on overcast days when duns emerge.'),
    ('Quill Gordon', 'Ephemeroptera', 'Epeorus',
     'Pheasant Tail Nymph', '#14-16', 'nymph', 'nymph',
     3, 4, '/images/flies/pheasant-tail-nymph.jpg',
     'Standard searching nymph; dead-drift in riffles before emergence.'),

    # ── Hendrickson (Ephemerella subvaria) — mid-April Catskill staple ──
    ('Hendrickson', 'Ephemeroptera', 'Ephemerella',
     'Hendrickson Dry', '#12-14', 'dry fly', 'adult',
     4, 5, '/images/flies/parachute-adams.jpg',
     'Pinkish-tan body; afternoon hatch on the Beaverkill / Mossy Creek.'),
    ('Hendrickson', 'Ephemeroptera', 'Ephemerella',
     'Hendrickson Sparkle Dun', '#12-14', 'emerger', 'emerger',
     4, 5, '/images/flies/parachute-adams.jpg',
     'Trailing-shuck emerger; deadly on selective Heritage water fish.'),
    ('Hendrickson', 'Ephemeroptera', 'Ephemerella',
     'Pheasant Tail Nymph', '#14-16', 'nymph', 'nymph',
     3, 5, '/images/flies/pheasant-tail-nymph.jpg',
     'Pre-hatch dropper; fish in slow tail-outs.'),

    # ── Sulphur (Ephemerella invaria) — May/June showcase hatch ──
    ('Sulphur', 'Ephemeroptera', 'Ephemerella',
     'Sulphur Parachute', '#16-18', 'dry fly', 'adult',
     5, 7, '/images/flies/parachute-adams.jpg',
     'Lemon-yellow body; evening hatch on South Fork limestoners.'),
    ('Sulphur', 'Ephemeroptera', 'Ephemerella',
     'Sulphur Sparkle Dun', '#16-18', 'emerger', 'emerger',
     5, 7, '/images/flies/parachute-adams.jpg',
     'Match emergers when fish ignore duns.'),
    ('Sulphur', 'Ephemeroptera', 'Ephemerella',
     'Pheasant Tail Nymph', '#16-18', 'nymph', 'nymph',
     4, 7, '/images/flies/pheasant-tail-nymph.jpg',
     'Drift through riffles 30 min before hatch peak.'),

    # ── Light Cahill (Stenacron interpunctatum) — summer evening mayfly ──
    ('Light Cahill', 'Ephemeroptera', 'Stenacron',
     'Light Cahill Dry', '#12-16', 'dry fly', 'adult',
     6, 8, '/images/flies/parachute-adams.jpg',
     'Cream / pale yellow; fish last hour of daylight.'),
    ('Light Cahill', 'Ephemeroptera', 'Stenacron',
     'Hare''s Ear Nymph', '#14-16', 'nymph', 'nymph',
     5, 8, '/images/flies/pheasant-tail-nymph.jpg',
     'Classic Catskill nymph; dropper beneath a Cahill dry.'),

    # ── Trico (Tricorythodes) — late-summer micro-mayfly spinner falls ──
    ('Trico', 'Ephemeroptera', 'Tricorythodes',
     'Trico Spinner', '#20-24', 'dry fly', 'spinner',
     7, 9, '/images/flies/parachute-adams.jpg',
     'White-winged spinner falls 8-10 AM on Mossy Creek-type streams.'),
    ('Trico', 'Ephemeroptera', 'Tricorythodes',
     'Trico Parachute', '#22-24', 'dry fly', 'adult',
     7, 9, '/images/flies/parachute-adams.jpg',
     'Black-bodied micro-mayfly; 6X-7X tippet required.'),

    # ── Hellgrammite (Corydalus cornutus) — smallmouth main-stem star ──
    ('Hellgrammite (smallmouth)', 'Megaloptera', 'Corydalus',
     'Black Wooly Bugger', '#4-8', 'streamer', 'larva',
     5, 9, '/images/flies/stimulator.jpg',
     'Hellgrammites are smallmouth candy on Shenandoah main stem.'),
    ('Hellgrammite (smallmouth)', 'Megaloptera', 'Corydalus',
     'Black Hellgrammite Pattern', '#6', 'nymph', 'larva',
     5, 9, '/images/flies/stimulator.jpg',
     'Weighted; dead-drift along rocky structure.'),

    # ── Little Black Stonefly (Capniidae) — late-winter / early-spring ──
    ('Little Black Stonefly', 'Plecoptera', 'Capnia',
     'Black Stimulator', '#16-18', 'dry fly', 'adult',
     2, 3, '/images/flies/stimulator.jpg',
     'Tiny black stonefly; first hatch of the season on Smith Creek.'),
    ('Little Black Stonefly', 'Plecoptera', 'Capnia',
     'Black Pheasant Tail', '#16-18', 'nymph', 'nymph',
     1, 3, '/images/flies/pheasant-tail-nymph.jpg',
     'Crawls to shore to emerge; nymph still useful in tail-outs.'),

    # ── Caddisflies (generic Hydropsyche / Brachycentrus) ──
    ('Caddisflies', 'Trichoptera', 'Hydropsyche',
     'Elk Hair Caddis', '#14-18', 'dry fly', 'adult',
     4, 9, '/images/flies/elk-hair-caddis.jpg',
     'Tan body; the all-purpose East Coast caddis dry.'),
    ('Caddisflies', 'Trichoptera', 'Hydropsyche',
     'X-Caddis', '#14-18', 'emerger', 'emerger',
     4, 9, '/images/flies/elk-hair-caddis.jpg',
     'Trailing shuck for selective trout during emergence.'),
    ('Caddisflies', 'Trichoptera', 'Brachycentrus',
     'Sparkle Pupa', '#14-18', 'nymph', 'pupa',
     4, 9, '/images/flies/pheasant-tail-nymph.jpg',
     'Swung wet-fly style during peak emergence.'),
]


def upgrade() -> None:
    conn = op.get_bind()
    from sqlalchemy import text
    for r in ROWS:
        (insect_common_name, insect_order, insect_genus,
         fly_pattern_name, fly_size, fly_type, life_stage,
         season_start, season_end, fly_image_url, notes) = r
        conn.execute(
            text("""
                INSERT INTO silver.insect_fly_patterns
                    (insect_order, insect_genus, insect_common_name,
                     fly_pattern_name, fly_size, fly_type, life_stage,
                     season_start, season_end, fly_image_url, notes,
                     fly_image_credit, water_type)
                SELECT CAST(:iorder AS varchar), CAST(:igenus AS varchar), CAST(:icn AS varchar),
                       CAST(:fpn AS varchar), CAST(:fsize AS varchar), CAST(:ftype AS varchar), CAST(:lstage AS varchar),
                       :s_start, :s_end, :furl, :notes,
                       'Standard pattern (placeholder asset)',
                       'East Coast mountain / limestone'
                 WHERE NOT EXISTS (
                       SELECT 1 FROM silver.insect_fly_patterns
                        WHERE insect_common_name = CAST(:icn AS varchar)
                          AND fly_pattern_name   = CAST(:fpn AS varchar)
                          AND COALESCE(life_stage, '') = COALESCE(CAST(:lstage AS varchar), '')
                 )
            """),
            {
                "iorder": insect_order, "igenus": insect_genus, "icn": insect_common_name,
                "fpn": fly_pattern_name, "fsize": fly_size, "ftype": fly_type, "lstage": life_stage,
                "s_start": season_start, "s_end": season_end, "furl": fly_image_url, "notes": notes,
            },
        )

    # Also populate curated_hatch_chart.fly_patterns for shenandoah so the
    # frontend's "Flies to Tie" pill list (which reads c.fly_patterns) has
    # something to render in addition to the joined silver table.
    op.execute("""
        UPDATE curated_hatch_chart SET fly_patterns = ARRAY['Pheasant Tail Nymph', 'Parachute Adams', 'Sparkle Dun']
         WHERE watershed = 'shenandoah' AND common_name = 'Blue-Winged Olive';
        UPDATE curated_hatch_chart SET fly_patterns = ARRAY['Quill Gordon Dry', 'Pheasant Tail Nymph']
         WHERE watershed = 'shenandoah' AND common_name = 'Quill Gordon';
        UPDATE curated_hatch_chart SET fly_patterns = ARRAY['Hendrickson Dry', 'Hendrickson Sparkle Dun', 'Pheasant Tail Nymph']
         WHERE watershed = 'shenandoah' AND common_name = 'Hendrickson';
        UPDATE curated_hatch_chart SET fly_patterns = ARRAY['Sulphur Parachute', 'Sulphur Sparkle Dun', 'Pheasant Tail Nymph']
         WHERE watershed = 'shenandoah' AND common_name = 'Sulphur';
        UPDATE curated_hatch_chart SET fly_patterns = ARRAY['Light Cahill Dry', 'Hare''s Ear Nymph']
         WHERE watershed = 'shenandoah' AND common_name = 'Light Cahill';
        UPDATE curated_hatch_chart SET fly_patterns = ARRAY['Trico Spinner', 'Trico Parachute']
         WHERE watershed = 'shenandoah' AND common_name = 'Trico';
        UPDATE curated_hatch_chart SET fly_patterns = ARRAY['Elk Hair Caddis', 'X-Caddis', 'Sparkle Pupa']
         WHERE watershed = 'shenandoah' AND common_name = 'Caddisflies';
        UPDATE curated_hatch_chart SET fly_patterns = ARRAY['Black Wooly Bugger', 'Black Hellgrammite Pattern']
         WHERE watershed = 'shenandoah' AND common_name = 'Hellgrammite (smallmouth)';
        UPDATE curated_hatch_chart SET fly_patterns = ARRAY['Black Stimulator', 'Black Pheasant Tail']
         WHERE watershed = 'shenandoah' AND common_name = 'Little Black Stonefly';
        UPDATE curated_hatch_chart SET fly_patterns = ARRAY['Griffith''s Gnat', 'Zebra Midge']
         WHERE watershed = 'shenandoah' AND common_name = 'Midges';
    """)

    # Refresh the downstream gold view that joins these patterns.
    op.execute("REFRESH MATERIALIZED VIEW gold.hatch_fly_recommendations")


def downgrade() -> None:
    op.execute("DELETE FROM silver.insect_fly_patterns WHERE water_type = 'East Coast mountain / limestone'")
    op.execute("UPDATE curated_hatch_chart SET fly_patterns = '{}' WHERE watershed = 'shenandoah'")
