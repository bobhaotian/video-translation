import argparse, subprocess, os

def run(cmd):
    print(" ".join(cmd))
    subprocess.check_call(cmd)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("in_mp4")
    ap.add_argument("in_wav")
    ap.add_argument("out_mp4")
    args = ap.parse_args()

    run([
        "ffmpeg", "-y",
        "-i", args.in_mp4, "-i", args.in_wav,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        args.out_mp4
    ])
