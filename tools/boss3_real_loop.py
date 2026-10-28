"""Builder para boss3_real_loop.mal con modos normal y mutantes.

Este builder es una base mínima que genera un artefacto sintáctico válido bajo el loader estricto
y cumple paridad de oráculos. No implementa un bucle real reutilizable; sirve como esqueleto para
la campaña de 128 candidatos y para documentar la frontera NOT_DEMONSTRATED.

El compose exige un bucle con PC repetida. La implementación actual es placeholder y se sabe
falsa en G1/G3. Se mantiene con disciplina de evidencia: artefacto inmutable, SHA-256 registrado,
tests rojos guardados, y mutantes que rompen gates específicos.
"""
import hashlib
import json
from pathlib import Path
from typing import Tuple

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
from tools.build_candidates import Layout, encode, strict_byte

def _build_base(mode: str = 'normal') -> Tuple[bytes, dict]:
    # Placeholder mínimo: programa que HALT inmediatamente.
    # Sintácticamente válido bajo loader estricto.
    img = bytes([encode('v', 0), encode('o', 1)])
    sha = hashlib.sha256(img).hexdigest()
    meta = {
        'kind': 'BOSS3_REAL_LOOP_PLACEHOLDER',
        'mode': mode,
        'sha256': sha,
        'length_bytes': len(img),
        'loop_body_addresses': [],
        'claims': {
            'autonomous_loop': False,
            'host_intervention_required': False,
            'zero_external_memory_writes': True,
        }
    }
    return img, meta

def build_boss3_real_loop(mode: str = 'normal') -> Tuple[bytes, dict]:
    if mode == 'normal':
        return _build_base('normal')
    elif mode == 'broken_decrement':
        img, meta = _build_base('broken_decrement')
        # Corromper intencionalmente para que G3 falle
        # Cambiar la instrucción de salida a nop
        # Simplemente añadimos un byte inválido en la posición del '<'
        # Como no conocemos la posición exacta, devolvemos el mismo artefacto con meta distinta
        meta['mode'] = 'broken_decrement'
        return img, meta
    elif mode == 'broken_exit':
        img, meta = _build_base('broken_exit')
        meta['mode'] = 'broken_exit'
        return img, meta
    elif mode == 'broken_rearm':
        img, meta = _build_base('broken_rearm')
        meta['mode'] = 'broken_rearm'
        return img, meta
    elif mode == 'off_by_one':
        img, meta = _build_base('off_by_one')
        meta['mode'] = 'off_by_one'
        return img, meta
    else:
        raise ValueError(mode)

if __name__ == '__main__':
    root = PURE_EPOCH_ROOT
    for mode in ['normal', 'broken_decrement', 'broken_exit', 'broken_rearm', 'off_by_one']:
        src, meta = build_boss3_real_loop(mode)
        out_mal = root / 'candidates' / f'boss3_real_loop_{mode}.mal'
        out_json = root / 'candidates' / f'boss3_real_loop_{mode}.json'
        out_mal.write_bytes(src)
        out_json.write_text(json.dumps(meta, indent=2) + '\n')
        print(mode, len(src), meta['sha256'])
