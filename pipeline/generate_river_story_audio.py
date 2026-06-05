"""Generate + cache OpenAI TTS audio for every river story (watershed × reading level).

The /api/v1/sites/{ws}/river-story endpoint returns audio_url only when an mp3
exists in app/audio_cache (local .river_story_audio/ in dev; the GCS bucket in
prod). Without it the frontend falls back to browser SpeechSynthesis, which is
silent on iOS. This script generates the mp3s so the in-app Audio button plays.

Voice/model mirror deeptrail_ai.py (OpenAI tts-1, voice 'nova'). OpenAI TTS caps
input at 4096 chars, so long (expert) stories are split at sentence boundaries
and the mp3 chunks are concatenated (mp3 frame concat plays fine).

Usage:
  OPENAI_API_KEY=... python -m pipeline.generate_river_story_audio [--watershed <slug>]
Then upload .river_story_audio/*.mp3 to gs://$GCS_BUCKET_ASSETS/audio/river_stories/ for prod.
"""
import os
import pathlib
import re
import sys

import httpx
from sqlalchemy import text

from pipeline.db import engine

OUT_DIR = pathlib.Path(__file__).resolve().parent.parent / ".river_story_audio"
TTS_URL = "https://api.openai.com/v1/audio/speech"
MODEL = "tts-1"
VOICE = "nova"
MAX_CHARS = 3800  # under the 4096 hard cap, with headroom


def _chunk(textbody: str) -> list[str]:
    if len(textbody) <= MAX_CHARS:
        return [textbody]
    # split on sentence boundaries, accumulate up to MAX_CHARS
    sentences = re.split(r'(?<=[.!?])\s+', textbody)
    chunks, cur = [], ""
    for s in sentences:
        if len(cur) + len(s) + 1 > MAX_CHARS and cur:
            chunks.append(cur.strip())
            cur = ""
        cur += s + " "
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


def _tts(client: httpx.Client, api_key: str, body: str) -> bytes:
    out = b""
    for chunk in _chunk(body):
        resp = client.post(
            TTS_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": MODEL, "voice": VOICE, "input": chunk},
            timeout=120,
        )
        resp.raise_for_status()
        out += resp.content
    return out


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    only = None
    if "--watershed" in sys.argv:
        only = sys.argv[sys.argv.index("--watershed") + 1]

    OUT_DIR.mkdir(exist_ok=True)
    q = "SELECT watershed, reading_level, narrative FROM river_stories"
    params = {}
    if only:
        q += " WHERE watershed = :w"
        params = {"w": only}
    q += " ORDER BY watershed, reading_level"
    with engine.connect() as conn:
        rows = conn.execute(text(q), params).all()

    made = skipped = 0
    with httpx.Client() as client:
        for ws, level, narrative in rows:
            out_file = OUT_DIR / f"{ws}_{level}.mp3"
            if out_file.exists() and out_file.stat().st_size > 0:
                print(f"  skip {out_file.name} (exists)")
                skipped += 1
                continue
            print(f"  generating {ws}_{level} ({len(narrative)} chars)...")
            audio = _tts(client, api_key, narrative)
            out_file.write_bytes(audio)
            print(f"    wrote {out_file.name} ({len(audio)} bytes)")
            made += 1
    print(f"done: {made} generated, {skipped} skipped, {len(rows)} total")


if __name__ == "__main__":
    main()
