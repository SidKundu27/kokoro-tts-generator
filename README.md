# Kokoro TTS Audio Generator

A Python utility to generate high-quality speech audio from text using **Kokoro**, a lightweight and efficient open-weight TTS model. This generator breaks large texts into manageable chunks, synthesizes them in parallel or sequence, and stitches the audio together seamlessly.

## Features

- 🎙️ **High-quality voice synthesis** using Kokoro (82M parameters)
- 📚 **Resumable processing** — if interrupted, re-run to resume from the last completed chunk
- 🔗 **Seamless stitching** with optional crossfade between chunks
- 📊 **Sentence-aware chunking** — automatically splits text at sentence boundaries for natural breaks
- 🚀 **GPU-accelerated** when available (CUDA support)
- 📦 **Multiple voices** supported (e.g., `af_heart`, `am_michael`, etc.)

## Prerequisites

### System Requirements

- **Python 3.10+** (tested on 3.12)
- **GPU** (optional, but recommended for speed): NVIDIA GPU with CUDA support
- **4GB+ RAM** (8GB+ recommended for larger chunks)

### On Windows

You'll need:
1. Python 3.10+ installed from [python.org](https://www.python.org/downloads/windows/)
2. Optionally, NVIDIA GPU drivers for acceleration

### On Linux/WSL

Similar requirements. WSL2 is recommended if using Windows with GPU support.

## Setup

### 1. Clone or Download the Project

```bash
cd /path/to/Kokoro_tts_audio
```

### 2. Create a Virtual Environment

Using **venv** (built-in, recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Using **conda** (if available):

```bash
conda create -n kokoro-tts python=3.12 -y
conda activate kokoro-tts
```

### 3. Install Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** If you have a GPU and PyTorch CPU-only was installed, you may need to reinstall PyTorch with GPU support:

```powershell
# For CUDA 12.1 (example; adjust version for your driver)
pip install --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio
```

### 4. Verify Installation

```powershell
python check_env.py
```

This should print:
- ✅ `OK: kokoro`
- ✅ `OK: torch`
- ✅ `OK: soundfile`
- ✅ `CUDA available: True` (if GPU is available)

If PyTorch says CUDA isn't available but you have an NVIDIA GPU, see the GPU Setup section below.

## Usage

### Basic Example

```powershell
python tts.py --input-file example.txt --voice af_heart
```

This generates `out/example_audio.wav` from the text in `example.txt`.

### Command-Line Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--input-file`, `-i` | *(required)* | Path to the text file to synthesize |
| `--voice`, `-v` | `af_heart` | Voice ID (e.g., `af_heart`, `am_michael`) |
| `--out-dir`, `-o` | `out` | Output directory for generated WAV files |
| `--chunk-size` | `2000` | Approximate characters per chunk (larger = fewer model calls, more memory) |
| `--keep-chunks` | *(flag)* | If set, keep intermediate chunk WAV files (useful for debugging) |
| `--crossfade-ms` | `30` | Duration of crossfade (in ms) between stitched chunks (reduce if you hear clicks) |

### Examples

**Generate audio in a custom directory:**

```powershell
python tts.py -i my_text.txt --out-dir my_output --voice af_heart
```

**Use a larger chunk size (faster for short texts, uses more GPU memory):**

```powershell
python tts.py -i long_text.txt --chunk-size 5000
```

**Keep chunk files for inspection:**

```powershell
python tts.py -i example.txt --keep-chunks
```

**Adjust crossfade (use less if you hear audio glitches at joins):**

```powershell
python tts.py -i example.txt --crossfade-ms 20
```

## Available Voices

Kokoro supports multiple voices. Common ones include:

- `af_heart` — Female, expressive (default)
- `am_michael` — Male, neutral
- `af_sarah` — Female, calm
- `am_adam` — Male, energetic

For a full list, refer to [Kokoro documentation](https://github.com/hexgrad/kokoro).

## Output

Running the generator produces:

- `<name>_audio.wav` — Final stitched audio file (24 kHz, mono)
- `<name>_chunk_XXXX.wav` — Individual chunk files (deleted by default unless `--keep-chunks` is used)

## Resumable Processing

If synthesis is interrupted (e.g., crash, timeout):

```powershell
# Re-run the same command
python tts.py -i example.txt --out-dir out
```

The script skips already-generated chunks and resumes from where it left off. This is useful for large files or unreliable systems.

## Performance Tips

### On GPU

1. **Ensure GPU is being used:**
   ```powershell
   python check_env.py
   ```
   Look for `CUDA available: True` and your GPU device name.

2. **Use larger chunks** to reduce per-call overhead:
   ```powershell
   python tts.py -i text.txt --chunk-size 4000  # experiment with sizes
   ```

3. **Monitor GPU usage** while running (useful to see if GPU is actually being used).

### On CPU

1. **Increase chunk size** to reduce the number of model calls.
2. **Use smaller text files** to avoid long runs.
3. **Consider GPU setup** — even a modest GPU can be 5–10× faster than CPU for TTS.

### General

- **First run may be slow** as the model is downloaded and cached (~500MB).
- **Subsequent runs are faster** due to caching.

## GPU Setup

### Check GPU Availability

```powershell
nvidia-smi
```

If this shows your GPU, you have the driver installed. Then check PyTorch:

```powershell
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('CUDA version:', torch.version.cuda)"
```

### Install GPU-Enabled PyTorch

If `torch.cuda.is_available()` returns `False`:

1. **Uninstall CPU PyTorch:**
   ```powershell
   pip uninstall -y torch torchvision torchaudio
   ```

2. **Install GPU version** (example for CUDA 12.1; adjust based on your driver):
   ```powershell
   pip install --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio
   ```

3. **Verify:**
   ```powershell
   python check_env.py
   ```

For detailed instructions, see [PyTorch's Get Started guide](https://pytorch.org/get-started/locally/).

## Troubleshooting

### "CUDA requested but not available"

**Cause:** PyTorch is CPU-only or GPU drivers are missing.  
**Fix:** Follow the GPU Setup section above.

### "CUDA capability sm_120 is not compatible"

**Cause:** PyTorch build doesn't support your GPU's compute capability.  
**Fix:** Install a newer PyTorch build (e.g., cu131 or conda's pytorch-cuda package).

### Audio quality is poor or contains static

**Cause:** Crossfade duration is too aggressive, or chunk boundaries are bad.  
**Fix:** Try reducing `--crossfade-ms` or increasing `--chunk-size`.

### Synthesis is too slow

**Cause:** Running on CPU, or GPU isn't being used.  
**Fix:** 
- Check `nvidia-smi` and `check_env.py` to confirm GPU access.
- Increase `--chunk-size` to reduce overhead.
- Reinstall PyTorch with GPU support (see GPU Setup).

### "ModuleNotFoundError: No module named 'kokoro'"

**Cause:** Dependencies not installed.  
**Fix:** Run `pip install -r requirements.txt` in your active virtual environment.

## Project Structure

```
Kokoro_tts_audio/
├── tts.py                 # Main synthesis runner
├── utils.py               # Chunking, audio stitching, WAV I/O
├── check_env.py           # Environment and GPU diagnostics
├── requirements.txt       # Python package dependencies
├── example.txt            # Example input text
├── README.md              # This file
├── .gitignore             # Git exclusions
└── out/                   # Default output directory (generated)
```

## Contributing & Customization

### Input Text Format

Any plain text file (`.txt`) works. The script automatically splits on sentence boundaries.

### Supported Voices

Edit the `--voice` argument. Kokoro voice IDs are typically formatted as `[gender]_[name]` (e.g., `af_heart`, `am_michael`).

### Advanced Customization

For deeper customization (e.g., different models, custom vocoders, or batch processing), edit `tts.py` and `utils.py` directly. The code is modular and well-commented.

## License

This project uses [Kokoro](https://github.com/hexgrad/kokoro) under its Apache license. See Kokoro's repository for details.

## References

- [Kokoro GitHub](https://github.com/hexgrad/kokoro)
- [PyTorch](https://pytorch.org)
- [SoundFile](https://pysoundfile.readthedocs.io/)

