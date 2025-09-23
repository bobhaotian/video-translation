import argparse, os, numpy as np, pysrt, soundfile as sf, librosa
from pydub import AudioSegment
from TTS.api import TTS
from tqdm import tqdm
from torch.serialization import add_safe_globals
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsAudioConfig
add_safe_globals([XttsConfig, XttsAudioConfig])

def make_timeline(duration_ms: int, sr: int) -> AudioSegment:
    # pydub timeline in ms, matches sr for exported audio
    return AudioSegment.silent(duration=duration_ms, frame_rate=sr).set_channels(1)

def main(in_srt: str, out_wav: str, ref_wav: str, speed: float = 1.0):
    os.makedirs(os.path.dirname(out_wav), exist_ok=True)
    subs = pysrt.open(in_srt, encoding="utf-8")
    if not subs:
        raise SystemExit("No subtitles found.")

    # Cross-lingual voice cloning model (captures speaker identity + tone)
    model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
    tts = TTS(model_name)

    sr = 24000  # XTTS native sample rate
    end_ms = subs[-1].end.ordinal + 1000
    timeline = make_timeline(end_ms, sr)

    tmp_dir = os.path.join(os.path.dirname(out_wav), "chunks")
    os.makedirs(tmp_dir, exist_ok=True)

    for idx, s in enumerate(tqdm(subs, desc="Cloning+Synth")):
        text = s.text.replace("\n", " ").strip()
        if not text:
            continue

        # Clone the original speaker’s identity from ref_wav
        wav = tts.tts(
            text=text,
            speaker_wav=ref_wav,
            language="de",
            speed=speed
        )
        wav = np.asarray(wav, dtype=np.float32)

        start_ms, end_ms = s.start.ordinal, s.end.ordinal
        target_sec = max(0.25, (end_ms - start_ms) / 1000.0)

        # Stretch/compress to fit subtitle timing
        dur_sec = len(wav) / sr
        rate = max(0.6, min(1.6, dur_sec / target_sec))
        stretched = librosa.effects.time_stretch(wav, rate=rate)

        # Normalize loudness
        if np.max(np.abs(stretched)) > 0:
            stretched = 0.9 * stretched / np.max(np.abs(stretched))

        # Overlay onto master timeline
        chunk_path = os.path.join(tmp_dir, f"{idx:04d}.wav")
        sf.write(chunk_path, stretched, sr, subtype="PCM_16")
        seg = AudioSegment.from_wav(chunk_path)
        timeline = timeline.overlay(seg, position=start_ms)

    timeline.export(out_wav, format="wav")
    print(f"Wrote {out_wav}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("in_srt", help="German SRT file")
    ap.add_argument("out_wav", help="Output WAV file")
    ap.add_argument("--ref_wav", required=True, help="Original voice reference (e.g. outputs/orig.wav)")
    ap.add_argument("--speed", type=float, default=1.0, help="Playback speed adjustment")
    args = ap.parse_args()
    main(args.in_srt, args.out_wav, ref_wav=args.ref_wav, speed=args.speed)
