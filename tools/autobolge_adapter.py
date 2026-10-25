"""Minimal OFFLINE encoder/trace/anchor bridge, never a runtime supervisor.

This does not implement relational proposal search or JIT. It invokes the real
Autobolge encoder and observes a separate from-zero run; it never calls restore.
"""
from pathlib import Path
import importlib.util
import json
import sys
import hashlib

from tools.build_candidates import build_conditional
from tools.observe import run
from tools.oracles import raw_reference

ROOT = Path(__file__).resolve().parents[1]
AUTO = ROOT/'vendor/autobolge'


def modules():
    if not AUTO.exists():
        raise RuntimeError('Pinned Autobolge vendor snapshot is missing; see README.md')
    if str(AUTO) not in sys.path:
        sys.path.insert(0, str(AUTO))
    from relational.classic import ClassicDebugger
    from relational.anchors import EpochAnchorV1
    from relational.trace import verify_trace, replay_trace
    from relational.synthesizer import char_for
    return ClassicDebugger, EpochAnchorV1, verify_trace, replay_trace, char_for


def eof_probe():
    Debugger, _, _, _, _ = modules()
    source = b'uP'  # '/' at zero, 'v' at one; two strict-valid bytes
    strict = run(source, b'')
    dbg = Debugger(source.decode('ascii'), '', 10)
    while not dbg.is_stopped and dbg.step_count < 10:
        dbg.step()
    return {'source_hex': source.hex(), 'payload_hex': '',
            'strict': {'a': strict['registers'][0], 'c': strict['registers'][1],
                       'd': strict['registers'][2], 'terminal': strict['terminal'], 'trace': strict['trace']},
            'autobolge': {'a': dbg.a, 'c': dbg.c, 'd': dbg.d,
                          'reason': dbg.get_state().stop_reason, 'steps': dbg.step_count}}


def semantic_probes():
    Debugger, _, _, _, _ = modules()
    enc_src = bytes.fromhex('2750')
    enc_strict = raw_reference(enc_src, b'', 10)
    enc_obs = run(enc_src, b'', 10)
    enc_dbg = Debugger(enc_src.decode('latin1'), '', 10)
    while not enc_dbg.is_stopped and enc_dbg.step_count < 10:
        enc_dbg.step()

    ldr_src = bytes.fromhex('af50')
    ldr_strict = raw_reference(ldr_src, b'', 10)
    try:
        ldr_obs = run(ldr_src, b'', 10)
        ldr_obs_info = {'terminal': ldr_obs['terminal']}
    except ValueError as err:
        ldr_obs_info = {'rejected': str(err)}
    ldr_dbg = Debugger(ldr_src.decode('latin1'), '', 10)
    while not ldr_dbg.is_stopped and ldr_dbg.step_count < 10:
        ldr_dbg.step()

    return {
        'invalid_encryption': {
            'source_hex': enc_src.hex(),
            'strict_returncode': enc_strict.returncode,
            'strict_stderr': enc_strict.stderr.decode('latin1').strip(),
            'observer': {
                'a': enc_obs['registers'][0],
                'c': enc_obs['registers'][1],
                'd': enc_obs['registers'][2],
                'terminal': enc_obs['terminal'],
            },
            'autobolge': {
                'a': enc_dbg.a,
                'c': enc_dbg.c,
                'd': enc_dbg.d,
                'reason': enc_dbg.get_state().stop_reason,
                'steps': enc_dbg.step_count,
            },
        },
        'non_ascii_loader': {
            'source_hex': ldr_src.hex(),
            'strict_returncode': ldr_strict.returncode,
            'strict_stderr': ldr_strict.stderr.decode('latin1').strip(),
            'observer': ldr_obs_info,
            'autobolge': {
                'a': ldr_dbg.a,
                'c': ldr_dbg.c,
                'd': ldr_dbg.d,
                'reason': ldr_dbg.get_state().stop_reason,
                'steps': ldr_dbg.step_count,
            },
        },
    }


def bridge(payload):
    Debugger, Anchor, verify_trace, replay_trace, char_for = modules()
    source, meta = build_conditional(encoder=char_for)
    native, _ = build_conditional()
    strict = run(source, payload)
    trace = []
    dbg = Debugger(source.decode('ascii'), payload.decode('latin1'), 5000, trace=trace)
    anchor = None
    while not dbg.is_stopped and dbg.step_count < 5000:
        pre_c = dbg.c
        dbg.step()
        if pre_c == meta['labels']['restore']:
            saved = Anchor.from_debugger(dbg, trace)
            anchor = {'digest': saved.digest(), 'memory_root': saved.memory_root,
                      'target_value': saved.memory[36], 'journal_value': saved.memory[52],
                      'pc': saved.pc, 'a': saved.a, 'd': saved.d, 'step': saved.step}
    verify_trace(trace)
    replay_trace(source.decode('ascii'), payload.decode('latin1'), trace, 5000)
    return {'same_source': source == native, 'source_sha256': hashlib.sha256(source).hexdigest(),
            'strict_state_parity': list(dbg.memory) == strict['memory'] and
                [dbg.a,dbg.c,dbg.d] == strict['registers'][:3] and dbg.output.encode('latin1') == strict['output'],
            'anchor_at_restore': anchor, 'autobolge_steps_including_halt': dbg.step_count,
            'scope': 'offline encoding and observational anchors only; no relational proposal search, JIT, or snapshot resume'}


if __name__ == '__main__':
    dest = ROOT/'evidence/autobolge-bridge.json'
    dest.write_text(json.dumps({'eof_difference': eof_probe(), 'semantic_probes': semantic_probes(), 'cases': [bridge(p) for p in [b'\x01\x03', b'\x03\x03']]}, indent=2)+'\n')
    print(dest)
