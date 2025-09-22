import argparse, os, numpy as np, pysrt, soundfile as sf, librosa
from pydub import AudioSegment
from TTS.api import TTS
from tqdm import tqdm

def make_timeline(duration_ms: int) -> AudioSegment:
    # 16-bit mono WAV at 22.05k; pydub uses milliseconds
    return AudioSegment.silent(duration=duration_ms, frame_rate=22050).set_channels(1)

def main(in_srt: str, out_wav: str, voice: str):
    os.makedirs(os.path.dirname(out_wav), exist_ok=True)
    subs = pysrt.open(in_srt, encoding="utf-8")
    if not subs:
        raise SystemExit("No subtitles found.")

    # Pick a solid German model (offline). Other good options:
    #  - tts_models/de/thorsten/tacotron2-DDC
    #  - tts_models/de/css10/vits-neon
    model_name = "tts_models/de/thorsten/tacotron2-DDC"
    tts = TTS(model_name)

    sr = 22050
    end_ms = subs[-1].end.ordinal + 1000
    timeline = make_timeline(end_ms)

    tmp_dir = os.path.join(os.path.dirname(out_wav), "chunks")
    os.makedirs(tmp_dir, exist_ok=True)

    for idx, s in enumerate(tqdm(subs, desc="Synthesizing")):
        text = s.text.replace("\n", " ").strip()
        if not text:
            continue
        # Raw TTS (numpy float32, sr=22050)
        wav = tts.tts(text=text, speaker=voice) if "multi_speaker" in model_name else tts.tts(text=text)
        wav = np.asarray(wav, dtype=np.float32)

        start_ms, end_ms = s.start.ordinal, s.end.ordinal
        target_sec = max(0.2, (end_ms - start_ms) / 1000.0)

        # Time-stretch the sample to fit subtitle window
        dur_sec = len(wav) / sr
        rate = max(0.5, min(2.0, dur_sec / target_sec))  # clamp extreme stretch
        stretched = librosa.effects.time_stretch(wav, rate=rate)
        # Loudness normalize a bit
        if np.max(np.abs(stretched)) > 0:
            stretched = 0.85 * stretched / np.max(np.abs(stretched))

        chunk_path = os.path.join(tmp_dir, f"{idx:04d}.wav")
        sf.write(chunk_path, stretched, sr, subtype="PCM_16")
        seg = AudioSegment.from_wav(chunk_path)
        timeline = timeline.overlay(seg, position=start_ms)

    timeline.export(out_wav, format="wav")
    print(f"Wrote {out_wav}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("in_srt")
    ap.add_argument("out_wav")
    ap.add_argument("--voice", default=None, help="speaker name if model supports it")
    args = ap.parse_args()
    main(args.in_srt, args.out_wav, voice=args.voice)
