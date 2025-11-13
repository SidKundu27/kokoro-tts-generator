import sys
import importlib

packages = [
    ('kokoro', 'KPipeline'),
    ('torch', None),
    ('soundfile', None),
    ('numpy', None),
]

def check():
    print('Python executable:', sys.executable)
    print('Python version:', sys.version)
    for pkg, symbol in packages:
        try:
            m = importlib.import_module(pkg)
            ver = getattr(m, '__version__', 'unknown')
            print(f'OK: {pkg} (version: {ver})')
            if symbol:
                if not hasattr(m, symbol):
                    print(f'  WARNING: {pkg} does not expose {symbol}')
        except Exception as e:
            print(f'MISSING: {pkg} -> {e}')

    # GPU diagnostics
    try:
        import torch
        print('Torch version:', getattr(torch, '__version__', 'unknown'))
        print('CUDA available:', torch.cuda.is_available())
        if torch.cuda.is_available():
            try:
                print('CUDA device count:', torch.cuda.device_count())
                for i in range(torch.cuda.device_count()):
                    print(i, torch.cuda.get_device_name(i))
            except Exception as e:
                print('Error querying CUDA devices:', e)
    except Exception:
        pass

    # nvidia-smi (optional)
    try:
        import subprocess
        res = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits'], shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            print('\nNVIDIA SMI output:')
            print(res.stdout.strip())
    except Exception:
        pass

if __name__ == '__main__':
    check()
