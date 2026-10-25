#!/usr/bin/env python3
"""Run last, after all commands that write evidence, to seal the file inventory."""
import hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
rows=[]
for p in sorted(root.rglob('*')):
    if p.is_file() and p.name!='SHA256SUMS.txt' and '__pycache__' not in p.parts:
        rows.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root)}\n')
(root/'SHA256SUMS.txt').write_text(''.join(rows))
print(f'Sealed {len(rows)} files.')
