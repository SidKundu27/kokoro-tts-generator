import argparse
import os
import sys
from typing import List
import numpy as np

from kokoro import KPipeline
from utils import chunk_text, write_wav, stitch_wavs, stitch_wavs_with_crossfade
import warnings

# Quiet some non-actionable deprecation warnings from torch internals
warnings.filterwarnings(
    "ignore",
    message=r".*weight_norm.*",
    category=FutureWarning,
)


def synth_chunk(pipeline: KPipeline, text: str, voice: str):
    # pipeline returns a generator of (gs, ps, audio)
    gen = pipeline(text, voice=voice)
    aud = None
    for i, (gs, ps, audio) in enumerate(gen):
        # we expect a single audio array per chunk; if multiple, concatenate
        if aud is None:
            aud = audio
        else:
            aud = np.concatenate([aud, audio], axis=0)
    return aud


def main():
    parser = argparse.ArgumentParser(description='Kokoro TTS Audio Generator')
    parser.add_argument('--input-file', '-i', required=True, help='Text file to synthesize')
    parser.add_argument('--voice', '-v', default='af_heart', help='Voice id (default: af_heart)')
    parser.add_argument('--out-dir', '-o', default='out', help='Output directory (default: out)')
    parser.add_argument('--chunk-size', type=int, default=2000, help='Approximate characters per chunk (default: 2000)')
    parser.add_argument('--keep-chunks', action='store_true', help='Keep intermediate chunk WAV files')
    parser.add_argument('--crossfade-ms', type=int, default=30, help='Crossfade duration in ms between chunks (default: 30)')
    args = parser.parse_args()

    with open(args.input_file, 'r', encoding='utf-8') as f:
        text = f.read().strip()

    chunks = chunk_text(text, args.chunk_size)

    # Apply sensible defaults for performance
    try:
        import torch
        # Enable cuDNN benchmarking for consistent input sizes
        try:
            torch.backends.cudnn.benchmark = True
        except Exception:
            pass
    except Exception:
        pass

    # Create pipeline with sensible defaults
    pipeline = KPipeline(lang_code='a')

    base = os.path.splitext(os.path.basename(args.input_file))[0]
    os.makedirs(args.out_dir, exist_ok=True)

    chunk_paths: List[str] = []
    for idx, chunk in enumerate(chunks):
        chunk_fn = os.path.join(args.out_dir, f'{base}_chunk_{idx:04d}.wav')
        # Track every expected chunk path; we'll only stitch existing ones
        chunk_paths.append(chunk_fn)
        if os.path.exists(chunk_fn):
            print(f'Skipping existing chunk {idx} -> {chunk_fn}')
            continue
        try:
            print(f'Synthesizing chunk {idx+1}/{len(chunks)} (chars {len(chunk)})')
            audio = synth_chunk(pipeline, chunk, voice=args.voice)
            if audio is None:
                raise RuntimeError('No audio produced by pipeline')
            write_wav(chunk_fn, audio, samplerate=24000)
        except Exception as e:
            print(f'Error synthesizing chunk {idx}: {e}', file=sys.stderr)
            print('Stopping; you can re-run to resume from the last produced chunk')
            sys.exit(2)

    # Stitch existing chunks only
    existing = [p for p in chunk_paths if os.path.exists(p)]
    if not existing:
        print('No chunk files found to stitch.', file=sys.stderr)
        sys.exit(3)

    # Determine final output name
    base = os.path.splitext(os.path.basename(args.input_file))[0]
    combined = os.path.join(args.out_dir, f'{base}_audio.wav')

    print('Stitching', len(existing), 'chunks ->', combined)
    stitch_wavs_with_crossfade(existing, combined, samplerate=24000, crossfade_ms=args.crossfade_ms)
    print('Done. Output:', combined)

    # Remove chunk files unless user asked to keep them
    if not args.keep_chunks:
        for p in existing:
            try:
                os.remove(p)
                print('Removed chunk:', p)
            except Exception as e:
                print(f'Warning: failed to remove {p}: {e}', file=sys.stderr)


if __name__ == '__main__':
    main()
