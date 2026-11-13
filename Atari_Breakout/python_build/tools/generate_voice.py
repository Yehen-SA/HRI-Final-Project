"""Make the robot's voice files from its lines, using Piper (offline text-to-speech).

Run from the game folder after changing lines in src/robot_persona/lines.py:

    uv run tools/generate_voice.py

- Downloads the Piper voice (persona_config.PIPER_VOICE) once into tools/.voice_cache/.
- Writes one .ogg per line into assets/robot/voice/, named after the line's text, so only new
  or changed lines are generated. OGG works both on desktop and in the browser build.
- Lists voice files no line uses any more, so you can remove them (git rm).
"""

import io
import os
import sys
import wave
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
GAME_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GAME_DIR / "src"))

import soundfile  # noqa: E402
from piper import PiperVoice, SynthesisConfig  # noqa: E402
from piper.download_voices import download_voice  # noqa: E402

from robot_persona import persona_config as cfg  # noqa: E402
from robot_persona.lines import all_lines  # noqa: E402
from robot_persona.speech import voice_path  # noqa: E402

CACHE = GAME_DIR / "tools" / ".voice_cache"


def load_voice() -> PiperVoice:
    model = CACHE / f"{cfg.PIPER_VOICE}.onnx"
    if not model.exists():
        print(f"Downloading Piper voice {cfg.PIPER_VOICE}...")
        CACHE.mkdir(parents=True, exist_ok=True)
        download_voice(cfg.PIPER_VOICE, CACHE)
    return PiperVoice.load(model)


def synthesize_ogg(voice: PiperVoice, text: str, out: Path) -> None:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        voice.synthesize_wav(
            text, wav, syn_config=SynthesisConfig(length_scale=cfg.PIPER_LENGTH_SCALE)
        )
    buffer.seek(0)
    audio, rate = soundfile.read(buffer)
    out.parent.mkdir(parents=True, exist_ok=True)
    soundfile.write(out, audio, rate, format="OGG", subtype="VORBIS")


def main() -> None:
    lines = all_lines()
    wanted = {voice_path(trigger, text) for trigger, text in lines}
    missing = [(t, text) for t, text in lines if not voice_path(t, text).exists()]
    if missing:
        voice = load_voice()
        for trigger, text in missing:
            out = voice_path(trigger, text)
            synthesize_ogg(voice, text, out)
            print(f"  made {out.name}: {text}")
    print(
        f"{len(lines)} lines, {len(missing)} generated, {len(lines) - len(missing)} already there."
    )

    voice_dir = voice_path("x", "x").parent
    stale = sorted(p for p in voice_dir.glob("*.ogg") if p not in wanted)
    if stale:
        print("\nNo line uses these any more; remove them with:")
        print("  git rm " + " ".join(str(p.relative_to(GAME_DIR)) for p in stale))


if __name__ == "__main__":
    main()
