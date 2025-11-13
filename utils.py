import os
import math
from typing import List, Tuple
import soundfile as sf
import numpy as np

def chunk_text(text: str, chunk_size: int = 1000) -> List[str]:
    """Split text into sentence-aware chunks of approximately chunk_size characters.
    This uses a lightweight regex to split sentences and then groups sentences until
    the chunk_size is approximately reached. No overlap is used to avoid audio duplication.
    """
    import re
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    # Split text into sentences. This is a heuristic and works reasonably for many languages.
    sentence_end_re = re.compile(r'(?<=[.!?])\s+')
    sentences = [s.strip() for s in sentence_end_re.split(text) if s.strip()]
    chunks: List[str] = []
    current = []
    current_len = 0
    for s in sentences:
        slen = len(s)
        if current_len + slen <= chunk_size or not current:
            current.append(s)
            current_len += slen + 1
        else:
            chunks.append(' '.join(current).strip())
            current = [s]
            current_len = slen + 1
    if current:
        chunks.append(' '.join(current).strip())
    return chunks

def write_wav(path: str, audio: np.ndarray, samplerate: int = 24000):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, audio, samplerate)

def stitch_wavs(paths: List[str], out_path: str, samplerate: int = 24000):
    """Read wavs and concatenate them, writing out_path. All files must share samplerate and channels.
    This is a simple concatenation; if overlap trimming is needed, do that externally.
    """
    arrays = []
    for p in paths:
        data, sr = sf.read(p)
        if sr != samplerate:
            raise ValueError(f"Samplerate mismatch: {p} is {sr}, expected {samplerate}")
        arrays.append(data)
    if len(arrays) == 0:
        raise ValueError("No files to stitch")
    concat = np.concatenate(arrays, axis=0)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sf.write(out_path, concat, samplerate)


def stitch_wavs_with_crossfade(paths: List[str], out_path: str, samplerate: int = 24000, crossfade_ms: int = 0):
    """Concatenate wavs with optional linear crossfade (in milliseconds) between adjacent files.
    If crossfade_ms == 0 this is identical to stitch_wavs.
    """
    arrays = []
    for p in paths:
        data, sr = sf.read(p)
        if sr != samplerate:
            raise ValueError(f"Samplerate mismatch: {p} is {sr}, expected {samplerate}")
        arrays.append(data)
    if len(arrays) == 0:
        raise ValueError("No files to stitch")

    if crossfade_ms <= 0:
        concat = np.concatenate(arrays, axis=0)
    else:
        overlap = int(samplerate * (crossfade_ms / 1000.0))
        if overlap <= 0:
            concat = np.concatenate(arrays, axis=0)
        else:
            out = arrays[0].copy()
            for a in arrays[1:]:
                # ensure both segments are long enough for overlap
                if len(out) < overlap or len(a) < overlap:
                    # fallback to simple concat
                    out = np.concatenate([out, a], axis=0)
                    continue
                # create linear ramps
                ramp = np.linspace(0.0, 1.0, overlap)
                inv = 1.0 - ramp
                # apply crossfade
                out_end = out[-overlap:]
                a_start = a[:overlap]
                mixed = (out_end * inv.reshape(-1, 1)) + (a_start * ramp.reshape(-1, 1)) if out_end.ndim == 2 else (out_end * inv) + (a_start * ramp)
                out = np.concatenate([out[:-overlap], mixed, a[overlap:]], axis=0)
            concat = out

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sf.write(out_path, concat, samplerate)
