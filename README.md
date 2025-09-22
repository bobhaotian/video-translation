# video-translation

## Setup
```bash
conda create -n video-translate -c conda-forge python=3.11.6 -y
conda activate video-translate
ENV_PY="$(conda info --base)/envs/video-translate/bin/python"
echo "Using $ENV_PY"
$ENV_PY -c "import sys; print('exe:', sys.executable)"

# 3) Keep system/user site-packages from leaking
export PYTHONNOUSERSITE=1
unset PYTHONPATH

# 4) Install everything INSIDE the env
$ENV_PY -m pip install --upgrade pip setuptools wheel
$ENV_PY -m pip install "transformers==4.43.4" safetensors tokenizers \
                       pysrt pydub librosa soundfile tqdm sentencepiece sacremoses \
                       TTS==0.22.0

# 5) Run your script with the env python
PYTHONNOUSERSITE=1 $ENV_PY src/translate_srt.py data/tanzania-2.srt outputs/tanzania-2.de.srt
```
