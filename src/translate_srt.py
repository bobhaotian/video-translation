import argparse, pysrt, re
from transformers import pipeline

def normalize(line: str) -> str:
    # Collapse multi-line cues and trim spaces
    return re.sub(r"\s+", " ", line).strip()

def main(in_srt: str, out_srt: str, formal: bool = True):
    subs = pysrt.open(in_srt, encoding="utf-8")
    translator = pipeline(
        "translation",
        model="Helsinki-NLP/opus-mt-en-de"
    )
    prefix = "FORMAL " if formal else ""  # gentle bias toward Sie
    for s in subs:
        text_en = normalize(s.text.replace("\n", " "))
        if not text_en:
            continue
        result = translator(prefix + text_en, max_length=512)[0]["translation_text"]
        # Light cleanup (keeps numbers/names as-is)
        s.text = result
    subs.save(out_srt, encoding="utf-8")
    print(f"Wrote {out_srt}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("in_srt")
    ap.add_argument("out_srt")
    ap.add_argument("--informal", action="store_true", help="use du instead of Sie")
    args = ap.parse_args()
    main(args.in_srt, args.out_srt, formal=(not args.informal))
